from __future__ import annotations

import os
import boto3
from typing import Any, Dict, List, Optional


_TABLE_NAME = os.environ.get("DYNAMODB_TABLE")
_dynamodb = boto3.resource("dynamodb")
_table = _dynamodb.Table(_TABLE_NAME) if _TABLE_NAME else None


def get_table():
    """
    Returns a DynamoDB Table instance using the DYNAMODB_TABLE environment variable.
    """
    if not _table:
        raise RuntimeError("DYNAMODB_TABLE is not configured.")
    return _table


def get_patient(patient_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves a patient record by patient_id.
    """
    table = get_table()
    resp = table.get_item(Key={"patient_id": patient_id})
    return resp.get("Item")


def scan_patients() -> List[Dict[str, Any]]:
    """
    Scans the entire patient table and returns a list of items.
    """
    table = get_table()
    items: List[Dict[str, Any]] = []
    resp = table.scan()
    items.extend(resp.get("Items", []))
    while "LastEvaluatedKey" in resp:
        resp = table.scan(ExclusiveStartKey=resp["LastEvaluatedKey"])
        items.extend(resp.get("Items", []))
    return items
