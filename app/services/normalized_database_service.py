"""
Сервис для работы с нормализованными таблицами базы данных
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from loguru import logger
import uuid

from app.models.normalized_models import Patient, TestMetadata, AnalyteResult, BloodTestResult
from app.models.database import AnalysisSession
from app.schemas.user_uploads import BloodTestResults


class NormalizedDatabaseService:
    """Сервис для работы с нормализованными таблицами базы данных"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def save_blood_test_results(
        self,
        blood_test_data: BloodTestResults,
        session_id: Optional[str] = None,
        source_filename: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> BloodTestResult:
        """
        Сохраняет результаты анализа крови в нормализованные таблицы
        
        Args:
            blood_test_data: Данные анализа крови
            session_id: ID сессии обработки
            source_filename: Имя исходного файла
            user_id: ID пользователя
            
        Returns:
            BloodTestResult: Сохраненная запись
        """
        try:
            # 1. Создаем или находим пациента
            patient = await self._create_or_get_patient(blood_test_data.patient)
            
            # 2. Создаем метаданные теста
            test_metadata = await self._create_test_metadata(blood_test_data.metadata)
            
            # 3. Создаем основную запись анализа крови
            blood_test_result = BloodTestResult(
                patient_id=patient.id,
                metadata_id=test_metadata.id,
                user_id=user_id,
                session_id=session_id,
                source_filename=source_filename,
                processing_status="completed"
            )
            
            self.db.add(blood_test_result)
            await self.db.flush()  # Получаем ID для создания аналитов
            
            # 4. Создаем записи аналитов
            analyte_records = []
            for analyte_name, analyte_data in blood_test_data.analytes.items():
                analyte_result = AnalyteResult(
                    blood_test_result_id=blood_test_result.id,
                    analyte_name=analyte_name,
                    value=analyte_data.value,
                    unit=analyte_data.unit,
                    reference_range=analyte_data.reference_range,
                    comment=analyte_data.comment
                )
                analyte_records.append(analyte_result)
                self.db.add(analyte_result)
            
            # 5. Рассчитываем SII если возможно
            await self._calculate_sii(blood_test_result, analyte_records)
            
            # Сохраняем все изменения
            await self.db.commit()
            await self.db.refresh(blood_test_result)
            
            logger.info(f"✅ Сохранены результаты анализа крови: Patient ID {patient.id}, Test ID {blood_test_result.id}")
            logger.info(f"📊 Сохранено аналитов: {len(analyte_records)}")
            
            return blood_test_result
            
        except Exception as e:
            logger.error(f"❌ Ошибка при сохранении результатов анализа крови: {e}")
            await self.db.rollback()
            raise
    
    async def _create_or_get_patient(self, patient_info) -> Patient:
        """
        Создает нового пациента или находит существующего
        
        Args:
            patient_info: Информация о пациенте
            
        Returns:
            Patient: Объект пациента
        """
        # Ищем существующего пациента по имени и возрасту
        result = await self.db.execute(
            select(Patient).where(
                Patient.full_name == patient_info.full_name,
                Patient.age == patient_info.age
            )
        )
        existing_patient = result.scalar_one_or_none()
        
        if existing_patient:
            logger.info(f"🔍 Найден существующий пациент: {existing_patient.full_name}")
            return existing_patient
        
        # Создаем нового пациента
        patient = Patient(
            full_name=patient_info.full_name,
            gender=patient_info.gender,
            age=patient_info.age,
            patient_id=patient_info.patient_id
        )
        
        self.db.add(patient)
        await self.db.flush()
        
        logger.info(f"👤 Создан новый пациент: {patient.full_name} (ID: {patient.id})")
        return patient
    
    async def _create_test_metadata(self, metadata_info) -> TestMetadata:
        """
        Создает метаданные теста
        
        Args:
            metadata_info: Метаданные теста
            
        Returns:
            TestMetadata: Объект метаданных
        """
        test_metadata = TestMetadata(
            sample_taken_date=metadata_info.sample_taken_date,
            sample_received_date=metadata_info.sample_received_date,
            result_printed_date=metadata_info.result_printed_date,
            doctor=metadata_info.doctor,
            laboratory=metadata_info.laboratory
        )
        
        self.db.add(test_metadata)
        await self.db.flush()
        
        logger.info(f"🧪 Созданы метаданные теста: {test_metadata.laboratory} (ID: {test_metadata.id})")
        return test_metadata
    
    async def _calculate_sii(self, blood_test_result: BloodTestResult, analyte_records: List[AnalyteResult]) -> None:
        """
        Рассчитывает Systemic Immune-Inflammation Index (SII)
        
        Args:
            blood_test_result: Запись анализа крови
            analyte_records: Список аналитов
        """
        try:
            # Ищем необходимые аналиты
            neutrophils_abs = None
            lymphocytes_abs = None
            platelets = None
            
            for analyte in analyte_records:
                if analyte.analyte_name.lower() in ["нейтрофилы (абс.)", "neutrophils_absolute"]:
                    neutrophils_abs = analyte.value
                elif analyte.analyte_name.lower() in ["лимфоциты (абс.)", "lymphocytes_absolute"]:
                    lymphocytes_abs = analyte.value
                elif analyte.analyte_name.lower() in ["тромбоциты", "platelets"]:
                    platelets = analyte.value
            
            if neutrophils_abs and lymphocytes_abs and platelets and lymphocytes_abs > 0:
                # SII = (Neutrophils × Platelets) / Lymphocytes
                sii_value = (neutrophils_abs * platelets * 1000) / lymphocytes_abs
                
                blood_test_result.sii_value = round(sii_value, 2)
                
                # Интерпретация SII
                if sii_value < 500:
                    blood_test_result.sii_level = "Низкий"
                    blood_test_result.sii_interpretation = "Низкий уровень системного воспаления"
                elif sii_value < 1000:
                    blood_test_result.sii_level = "Умеренный"
                    blood_test_result.sii_interpretation = "Умеренный уровень системного воспаления"
                else:
                    blood_test_result.sii_level = "Высокий"
                    blood_test_result.sii_interpretation = "Высокий уровень системного воспаления"
                
                logger.info(f"🧮 Рассчитан SII: {sii_value:.2f} ({blood_test_result.sii_level})")
                
        except Exception as e:
            logger.warning(f"⚠️ Не удалось рассчитать SII: {e}")
    
    async def get_blood_test_result_with_details(self, blood_test_id: int) -> Optional[BloodTestResult]:
        """
        Получает полную информацию об анализе крови с пациентом, метаданными и аналитами
        
        Args:
            blood_test_id: ID анализа крови
            
        Returns:
            BloodTestResult: Полная информация об анализе
        """
        try:
            result = await self.db.execute(
                select(BloodTestResult)
                .options(
                    selectinload(BloodTestResult.patient),
                    selectinload(BloodTestResult.test_metadata),
                    selectinload(BloodTestResult.analyte_results)
                )
                .where(BloodTestResult.id == blood_test_id)
            )
            
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"❌ Ошибка при получении анализа крови {blood_test_id}: {e}")
            return None
    
    async def get_patient_blood_tests(self, patient_id: int, limit: int = 10) -> List[BloodTestResult]:
        """
        Получает список анализов крови для пациента
        
        Args:
            patient_id: ID пациента
            limit: Максимальное количество записей
            
        Returns:
            List[BloodTestResult]: Список анализов крови
        """
        try:
            result = await self.db.execute(
                select(BloodTestResult)
                .options(
                    selectinload(BloodTestResult.test_metadata),
                    selectinload(BloodTestResult.analyte_results)
                )
                .where(BloodTestResult.patient_id == patient_id)
                .order_by(BloodTestResult.created_at.desc())
                .limit(limit)
            )
            
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"❌ Ошибка при получении анализов пациента {patient_id}: {e}")
            return []
    
    async def create_analysis_session(
        self,
        filename: Optional[str] = None,
        file_type: Optional[str] = None,
        file_size: Optional[int] = None,
        user_id: Optional[str] = None
    ) -> AnalysisSession:
        """
        Создает новую сессию анализа документа
        
        Args:
            filename: Имя файла
            file_type: Тип файла
            file_size: Размер файла
            user_id: ID пользователя
            
        Returns:
            AnalysisSession: Созданная сессия
        """
        try:
            session = AnalysisSession(
                session_id=str(uuid.uuid4()),
                user_id=user_id,
                filename=filename,
                file_type=file_type,
                file_size=file_size,
                processing_status="processing"
            )
            
            self.db.add(session)
            await self.db.commit()
            await self.db.refresh(session)
            
            logger.info(f"📋 Создана сессия анализа: {session.session_id}")
            return session
            
        except Exception as e:
            logger.error(f"❌ Ошибка при создании сессии анализа: {e}")
            await self.db.rollback()
            raise
    
    async def update_analysis_session(
        self,
        session_id: str,
        status: str,
        blood_test_id: Optional[int] = None,
        extracted_text: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Optional[AnalysisSession]:
        """
        Обновляет сессию анализа
        
        Args:
            session_id: ID сессии
            status: Новый статус
            blood_test_id: ID записи анализа крови
            extracted_text: Извлеченный текст
            error_message: Сообщение об ошибке
            
        Returns:
            AnalysisSession: Обновленная сессия
        """
        try:
            result = await self.db.execute(
                select(AnalysisSession).where(AnalysisSession.session_id == session_id)
            )
            session = result.scalar_one_or_none()
            
            if session:
                session.processing_status = status
                if blood_test_id:
                    session.blood_test_id = blood_test_id
                if extracted_text:
                    session.extracted_text = extracted_text
                if error_message:
                    session.error_message = error_message
                
                await self.db.commit()
                await self.db.refresh(session)
                
                logger.info(f"📋 Обновлена сессия анализа: {session_id} -> {status}")
                return session
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка при обновлении сессии анализа: {e}")
            await self.db.rollback()
            raise


async def get_normalized_database_service(db_session: AsyncSession) -> NormalizedDatabaseService:
    """
    Создает экземпляр нормализованного сервиса базы данных
    
    Args:
        db_session: Сессия базы данных
        
    Returns:
        NormalizedDatabaseService: Экземпляр сервиса
    """
    return NormalizedDatabaseService(db_session) 