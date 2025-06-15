from typing import Optional, Dict, Tuple
from pydantic import BaseModel, Field
from datetime import date, datetime

class PatientInfo(BaseModel):
    full_name: str
    gender: str
    age: int
    patient_id: Optional[str] = None

class TestMetadata(BaseModel):
    sample_taken_date: datetime
    sample_received_date: Optional[datetime] = None
    result_printed_date: datetime
    doctor: Optional[str] = None
    laboratory: Optional[str] = None

class AnalyteResult(BaseModel):
    value: float
    unit: str
    reference_range: Optional[str] = None
    comment: Optional[str] = None

class BloodTestResults(BaseModel):
    patient: PatientInfo
    metadata: TestMetadata
    analytes: Dict[str, AnalyteResult]

