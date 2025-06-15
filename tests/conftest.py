import os
import sys
import pytest
from fastapi.testclient import TestClient

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Импортируем app из main.py (который использует новую архитектуру)
from app.main import app

@pytest.fixture
def client():
    """Fixture для тестового клиента FastAPI"""
    return TestClient(app)

@pytest.fixture
def sample_blood_test_data():
    """Fixture с примером данных анализа крови"""
    return {
        "hemoglobin": 14.5,
        "white_blood_cells": 6.8,
        "red_blood_cells": 4.5,
        "platelets": 250.0,
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
        "cancer_type": "C34"
    }

@pytest.fixture
def minimal_blood_test_data():
    """Fixture с минимальными данными для расчета SII"""
    return {
        "neutrophils_absolute": 4.0,
        "platelets": 250.0,
        "lymphocytes_absolute": 2.0,
        "cancer_type": "C34"
    } 