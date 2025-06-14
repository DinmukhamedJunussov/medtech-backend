"""
Модели базы данных для MedTech приложения
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.sql import func

from app.database import Base


class BloodTestRecord(Base):
    """Модель для хранения результатов анализов крови"""
    
    __tablename__ = "blood_test_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=True)  # ID пользователя (опционально)
    
    # Информация о пациенте
    patient_full_name = Column(String, nullable=True)
    patient_gender = Column(String, nullable=True)
    patient_age = Column(Integer, nullable=True)
    patient_id = Column(String, nullable=True)
    
    # Метаданные тестирования
    sample_taken_date = Column(DateTime, nullable=True)
    sample_received_date = Column(DateTime, nullable=True)
    result_printed_date = Column(DateTime, nullable=True)
    doctor = Column(String, nullable=True)
    laboratory = Column(String, nullable=True)
    
    # Основные показатели крови
    hemoglobin = Column(Float, nullable=True)  # г/л
    white_blood_cells = Column(Float, nullable=True)  # тыс/мкл (Лейкоциты)
    red_blood_cells = Column(Float, nullable=True)  # млн/мкл (Эритроциты)
    platelets = Column(Float, nullable=True)  # тыс/мкл (Тромбоциты)
    hematocrit = Column(Float, nullable=True)  # % (Гематокрит)
    
    # Эритроцитарные индексы
    mcv = Column(Float, nullable=True)  # фл (Средний объем эритроцита)
    mch = Column(Float, nullable=True)  # пг (Среднее содержание гемоглобина в эритроците)
    mchc = Column(Float, nullable=True)  # г/дл (Средняя концентрация гемоглобина в эритроците)
    rdw = Column(Float, nullable=True)  # % (Ширина распределения эритроцитов)
    
    # Нейтрофилы
    neutrophils_percent = Column(Float, nullable=True)
    neutrophils_absolute = Column(Float, nullable=True)
    
    # Лимфоциты
    lymphocytes_percent = Column(Float, nullable=True)
    lymphocytes_absolute = Column(Float, nullable=True)
    
    # Моноциты
    monocytes_percent = Column(Float, nullable=True)
    monocytes_absolute = Column(Float, nullable=True)
    
    # Эозинофилы
    eosinophils_percent = Column(Float, nullable=True)
    eosinophils_absolute = Column(Float, nullable=True)
    
    # Базофилы
    basophils_percent = Column(Float, nullable=True)
    basophils_absolute = Column(Float, nullable=True)
    
    # СОЭ
    esr = Column(Float, nullable=True)  # мм/ч (Скорость оседания эритроцитов)
    
    # SII расчет
    sii_value = Column(Float, nullable=True)
    sii_level = Column(String, nullable=True)
    sii_interpretation = Column(Text, nullable=True)
    
    # Системные поля
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Дополнительные данные в JSON формате (все аналиты с единицами и референсными значениями)
    analytes_data = Column(JSON, nullable=True)
    
    # Метаданные файла
    source_filename = Column(String, nullable=True)
    processing_session_id = Column(String, nullable=True)


class UserProfile(Base):
    """Модель профиля пользователя"""
    
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True)
    
    # Персональная информация
    name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    
    # Медицинская информация
    birth_date = Column(DateTime, nullable=True)
    gender = Column(String, nullable=True)
    medical_history = Column(JSON, nullable=True)
    
    # Системные поля
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AnalysisSession(Base):
    """Модель сессии анализа документа"""
    
    __tablename__ = "analysis_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    user_id = Column(String, nullable=True)
    
    # Информация о файле
    filename = Column(String, nullable=True)
    file_type = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    
    # Результаты обработки
    processing_status = Column(String, default="pending")  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    
    # Извлеченные данные
    extracted_text = Column(Text, nullable=True)
    blood_test_id = Column(Integer, nullable=True)  # Ссылка на BloodTestRecord
    
    # Системные поля
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class SystemLog(Base):
    """Модель для системных логов"""
    
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Информация о событии
    level = Column(String, index=True)  # INFO, WARNING, ERROR, DEBUG
    message = Column(Text)
    module = Column(String, nullable=True)
    function = Column(String, nullable=True)
    
    # Контекст
    user_id = Column(String, nullable=True)
    session_id = Column(String, nullable=True)
    request_id = Column(String, nullable=True)
    
    # Дополнительные данные
    extra_data = Column(JSON, nullable=True)
    
    # Системные поля
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 