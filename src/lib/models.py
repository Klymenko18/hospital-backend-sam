from __future__ import annotations

from typing import Dict, List
from pydantic import BaseModel, Field


class PatientRecord(BaseModel):
    """Patient document stored in DynamoDB."""
    patient_id: str
    name: str
    sex: str
    date_of_birth: str
    bmi: float
    medications: List[str] = Field(default_factory=list)
    diseases: List[str] = Field(default_factory=list)


class TopItem(BaseModel):
    """Generic ranked item (e.g., top diseases)."""
    name: str
    count: int


class MetricsOverview(BaseModel):
    """Aggregated metrics for admin dashboard."""
    total_patients: int
    avg_bmi: float
    counts_by_sex: Dict[str, int]
    avg_age_years: float
    top_diseases: List[TopItem] = Field(default_factory=list)
