"""
Нормализованные модели базы данных для MedTech приложения
Соответствуют схемам Pydantic из user_uploads.py
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Patient(Base):
    """Модель для информации о пациенте (PatientInfo)"""
    
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    gender = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    patient_id = Column(String, nullable=True, index=True)
    
    # Системные поля
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    blood_test_results = relationship("BloodTestResult", back_populates="patient")


class TestMetadata(Base):
    """Модель для метаданных тестирования (TestMetadata)"""
    
    __tablename__ = "test_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    sample_taken_date = Column(DateTime, nullable=False)
    sample_received_date = Column(DateTime, nullable=True)
    result_printed_date = Column(DateTime, nullable=False)
    doctor = Column(String, nullable=True)
    laboratory = Column(String, nullable=True)
    
    # Системные поля
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    blood_test_results = relationship("BloodTestResult", back_populates="test_metadata")


class AnalyteResult(Base):
    """Модель для результатов аналитов (AnalyteResult)"""
    
    __tablename__ = "analyte_results"
    
    id = Column(Integer, primary_key=True, index=True)
    blood_test_result_id = Column(Integer, ForeignKey("blood_test_results.id"), nullable=False)
    
    # Данные аналита
    analyte_name = Column(String, nullable=False, index=True)
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    reference_range = Column(String, nullable=True)
    comment = Column(Text, nullable=True)
    
    # Системные поля
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    blood_test_result = relationship("BloodTestResult", back_populates="analyte_results")


class BloodTestResult(Base):
    """Модель для результатов анализа крови (BloodTestResults)"""
    
    __tablename__ = "blood_test_results"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Внешние ключи
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    metadata_id = Column(Integer, ForeignKey("test_metadata.id"), nullable=False)
    
    # Дополнительные поля для интеграции
    user_id = Column(String, index=True, nullable=True)  # ID пользователя системы
    session_id = Column(String, index=True, nullable=True)  # ID сессии обработки
    source_filename = Column(String, nullable=True)  # Исходный файл
    
    # Расчетные поля
    sii_value = Column(Float, nullable=True)
    sii_level = Column(String, nullable=True)
    sii_interpretation = Column(Text, nullable=True)
    
    # Статус обработки
    processing_status = Column(String, default="completed")
    
    # Системные поля
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    patient = relationship("Patient", back_populates="blood_test_results")
    test_metadata = relationship("TestMetadata", back_populates="blood_test_results")
    analyte_results = relationship("AnalyteResult", back_populates="blood_test_result", cascade="all, delete-orphan")


# Импортируем существующие модели для совместимости
from app.models.database import AnalysisSession, SystemLog 