from __future__ import annotations

from typing import Any, Dict

from lib.auth import extract_claims, get_caller_sub
from lib.db import get_patient
from lib.models import PatientRecord
from lib.utils import json_response


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Returns the caller's patient record by matching token sub to patient_id.
    """
    try:
        claims = extract_claims(event)
        sub = get_caller_sub(claims)
    except PermissionError as e:
        return json_response(401, {"message": str(e)})

    item = get_patient(sub)
    if not item:
        return json_response(404, {"message": "Patient not found"})
    record = PatientRecord(**item)
    return json_response(200, record.model_dump())
