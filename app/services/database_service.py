"""
Сервис для работы с базой данных
"""
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger
import uuid

from app.models.database import BloodTestRecord, AnalysisSession
from app.schemas.user_uploads import BloodTestResults


class DatabaseService:
    """Сервис для работы с базой данных"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def save_blood_test_results(
        self,
        blood_test_data: BloodTestResults,
        session_id: Optional[str] = None,
        source_filename: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> BloodTestRecord:
        """
        Сохраняет результаты анализа крови в базу данных
        
        Args:
            blood_test_data: Данные анализа крови
            session_id: ID сессии обработки
            source_filename: Имя исходного файла
            user_id: ID пользователя
            
        Returns:
            BloodTestRecord: Сохраненная запись
        """
        try:
            # Создаем запись в базе данных
            blood_test_record = BloodTestRecord(
                user_id=user_id,
                processing_session_id=session_id,
                source_filename=source_filename,
                
                # Информация о пациенте
                patient_full_name=blood_test_data.patient.full_name,
                patient_gender=blood_test_data.patient.gender,
                patient_age=blood_test_data.patient.age,
                patient_id=blood_test_data.patient.patient_id,
                
                # Метаданные тестирования
                sample_taken_date=blood_test_data.metadata.sample_taken_date,
                sample_received_date=blood_test_data.metadata.sample_received_date,
                result_printed_date=blood_test_data.metadata.result_printed_date,
                doctor=blood_test_data.metadata.doctor,
                laboratory=blood_test_data.metadata.laboratory,
                
                # Извлекаем основные показатели
                hemoglobin=self._extract_analyte_value(blood_test_data.analytes, "Гемоглобин"),
                white_blood_cells=self._extract_analyte_value(blood_test_data.analytes, "Лейкоциты"),
                red_blood_cells=self._extract_analyte_value(blood_test_data.analytes, "Эритроциты"),
                platelets=self._extract_analyte_value(blood_test_data.analytes, "Тромбоциты"),
                hematocrit=self._extract_analyte_value(blood_test_data.analytes, "Гематокрит"),
                
                # Эритроцитарные индексы
                mcv=self._extract_analyte_value(blood_test_data.analytes, "MCV"),
                mch=self._extract_analyte_value(blood_test_data.analytes, "MCH"),
                mchc=self._extract_analyte_value(blood_test_data.analytes, "MCHC"),
                rdw=self._extract_analyte_value(blood_test_data.analytes, "RDW"),
                
                # Нейтрофилы
                neutrophils_percent=self._extract_analyte_value(blood_test_data.analytes, "Нейтрофилы (%)"),
                neutrophils_absolute=self._extract_analyte_value(blood_test_data.analytes, "Нейтрофилы (абс.)"),
                
                # Лимфоциты
                lymphocytes_percent=self._extract_analyte_value(blood_test_data.analytes, "Лимфоциты (%)"),
                lymphocytes_absolute=self._extract_analyte_value(blood_test_data.analytes, "Лимфоциты (абс.)"),
                
                # Моноциты
                monocytes_percent=self._extract_analyte_value(blood_test_data.analytes, "Моноциты (%)"),
                monocytes_absolute=self._extract_analyte_value(blood_test_data.analytes, "Моноциты (абс.)"),
                
                # Эозинофилы
                eosinophils_percent=self._extract_analyte_value(blood_test_data.analytes, "Эозинофилы (%)"),
                eosinophils_absolute=self._extract_analyte_value(blood_test_data.analytes, "Эозинофилы (абс.)"),
                
                # Базофилы
                basophils_percent=self._extract_analyte_value(blood_test_data.analytes, "Базофилы (%)"),
                basophils_absolute=self._extract_analyte_value(blood_test_data.analytes, "Базофилы (абс.)"),
                
                # СОЭ
                esr=self._extract_analyte_value(blood_test_data.analytes, "СОЭ"),
                
                # Сохраняем все аналиты в JSON формате
                analytes_data=self._convert_analytes_to_json(blood_test_data.analytes)
            )
            
            # Рассчитываем SII если есть необходимые данные
            self._calculate_sii(blood_test_record)
            
            # Сохраняем в базу данных
            self.db.add(blood_test_record)
            await self.db.commit()
            await self.db.refresh(blood_test_record)
            
            logger.info(f"Сохранены результаты анализа крови для пациента: {blood_test_data.patient.full_name} (ID: {blood_test_record.id})")
            return blood_test_record
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении результатов анализа крови: {e}")
            await self.db.rollback()
            raise
    
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
            
            logger.info(f"Создана сессия анализа: {session.session_id}")
            return session
            
        except Exception as e:
            logger.error(f"Ошибка при создании сессии анализа: {e}")
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
                
                logger.info(f"Обновлена сессия анализа: {session_id} -> {status}")
                return session
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении сессии анализа: {e}")
            await self.db.rollback()
            raise
    
    def _extract_analyte_value(self, analytes: Dict[str, Any], name: str) -> Optional[float]:
        """
        Извлекает числовое значение аналита
        
        Args:
            analytes: Словарь аналитов
            name: Название аналита
            
        Returns:
            Optional[float]: Значение аналита или None
        """
        if name in analytes:
            try:
                return float(analytes[name].value)
            except (ValueError, AttributeError):
                pass
        return None
    
    def _convert_analytes_to_json(self, analytes: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Конвертирует аналиты в JSON формат для сохранения в базе данных
        
        Args:
            analytes: Словарь аналитов
            
        Returns:
            Dict: Аналиты в JSON формате
        """
        json_analytes = {}
        for name, analyte in analytes.items():
            json_analytes[name] = {
                "value": analyte.value,
                "unit": analyte.unit,
                "reference_range": analyte.reference_range,
                "comment": analyte.comment
            }
        return json_analytes
    
    def _calculate_sii(self, record: BloodTestRecord) -> None:
        """
        Рассчитывает Systemic Immune-Inflammation Index (SII)
        
        Args:
            record: Запись анализа крови
        """
        try:
            if (record.neutrophils_absolute is not None and 
                record.platelets is not None and 
                record.lymphocytes_absolute is not None and
                record.lymphocytes_absolute > 0):
                
                # SII = (Neutrophils × Platelets) / Lymphocytes
                sii_value = (record.neutrophils_absolute * record.platelets * 1000) / record.lymphocytes_absolute
                
                record.sii_value = round(sii_value, 2)
                
                # Интерпретация SII
                if sii_value < 500:
                    record.sii_level = "Низкий"
                    record.sii_interpretation = "Низкий уровень системного воспаления"
                elif sii_value < 1000:
                    record.sii_level = "Умеренный"
                    record.sii_interpretation = "Умеренный уровень системного воспаления"
                else:
                    record.sii_level = "Высокий"
                    record.sii_interpretation = "Высокий уровень системного воспаления"
                
        except Exception as e:
            logger.warning(f"Не удалось рассчитать SII: {e}")


async def get_database_service(db_session: AsyncSession) -> DatabaseService:
    """
    Создает экземпляр сервиса базы данных
    
    Args:
        db_session: Сессия базы данных
        
    Returns:
        DatabaseService: Экземпляр сервиса
    """
    return DatabaseService(db_session) 