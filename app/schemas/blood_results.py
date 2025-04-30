from datetime import datetime

from pydantic import BaseModel, Field


class BloodTestResults(BaseModel):
    """Модель для хранения результатов анализа крови"""
    
    # Основные показатели
    hemoglobin: float | None = Field(None, description="Гемоглобин (HGB)")
    white_blood_cells: float | None = Field(None, description="Лейкоциты (WBC)")
    red_blood_cells: float | None = Field(None, description="Эритроциты (RBC)")
    platelets: float | None = Field(None, description="Тромбоциты (PLT)")
    
    # Нейтрофилы
    neutrophils_percent: float | None = Field(None, description="Нейтрофилы (NEUT%)")
    neutrophils_absolute: float | None = Field(None, description="Нейтрофилы (абс. кол-во) (NEUT#)")
    
    # Лимфоциты
    lymphocytes_percent: float | None = Field(None, description="Лимфоциты (LYM%)")
    lymphocytes_absolute: float | None = Field(None, description="Лимфоциты (абс. кол-во) (LYM#)")
    
    # Моноциты
    monocytes_percent: float | None = Field(None, description="Моноциты (MON%)")
    monocytes_absolute: float | None = Field(None, description="Моноциты (абс. кол-во) (MON#)")
    
    # Эозинофилы
    eosinophils_percent: float | None = Field(None, description="Эозинофилы (EOS%)")
    eosinophils_absolute: float | None = Field(None, description="Эозинофилы (абс. кол-во) (EOS#)")
    
    # Базофилы
    basophils_percent: float | None = Field(None, description="Базофилы (BAS%)")
    basophils_absolute: float | None = Field(None, description="Базофилы (абс. кол-во) (BAS#)")
    
    # Метаданные
    test_date: datetime | None = Field(None, description="Дата проведения анализа")
    patient_id: int | None = Field(None, description="ID пациента")
    lab_id: int | None = Field(None, description="ID лаборатории")
    notes: str | None = Field(None, description="Дополнительные заметки")

    model_config = {
        "json_schema_extra": {
            "example": {
                "hemoglobin": 14.5,
                "white_blood_cells": 6.8,
                "red_blood_cells": 4.5,
                "platelets": 250,
                "neutrophils_percent": 60.0,
                "neutrophils_absolute": 4.1,
                "lymphocytes_percent": 30.0,
                "lymphocytes_absolute": 2.0,
                "monocytes_percent": 5.0,
                "monocytes_absolute": 0.3,
                "eosinophils_percent": 3.0,
                "eosinophils_absolute": 0.2,
                "basophils_percent": 2.0,
                "basophils_absolute": 0.1,
                "test_date": "2024-03-20T10:00:00",
                "patient_id": 1,
                "lab_id": 1,
                "notes": "Нормальные показатели"
            }
        }
    }

# blood_test_names = [
#     ("Гемоглобин", "HGB"),
#     ("Лейкоциты", "WBC"),
#     ("Эритроциты", "RBC"),
#     ("Тромбоциты", "PLT"),
#     ("Нейтрофилы", "NEUT%"),
#     ("Нейтрофилы (абс. кол-во)", "NEUT#"),
#     ("Лимфоциты", "LYM%"),
#     ("Лимфоциты (абс. кол-во)", "LYM#"),
#     ("Моноциты", "MON%"),
#     ("Моноциты (абс. кол-во)", "MON#"),
#     ("Эозинофилы", "EOS%"),
#     ("Эозинофилы (абс. кол-во)", "EOS#"),
#     ("Базофилы", "BAS%"),
#     ("Базофилы (абс. кол-во)", "BAS#"),
# ]
