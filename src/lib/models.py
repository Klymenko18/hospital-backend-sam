from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Dict


class PatientRecord(BaseModel):
    """
    Serializable patient record.
    """
    patient_id: str
    name: str
    sex: str = Field(pattern="^(M|F|X)$")
    date_of_birth: str
    bmi: float
    medications: List[str]
    diseases: List[str]


class MetricsOverview(BaseModel):
    """
    Aggregated metrics overview.
    """
    total_patients: int
    avg_bmi: float
    counts_by_sex: Dict[str, int]
    avg_age_years: float
    top_diseases: List[Dict[str, int]]
