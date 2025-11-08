from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import boto3
from botocore.config import Config

_dynamodb = None
_table = None


def _boto3_resource():
    """Returns a cached DynamoDB resource; initializes lazily."""
    global _dynamodb
    if _dynamodb is None:
        region = (
            os.environ.get("AWS_REGION")
            or os.environ.get("AWS_DEFAULT_REGION")
            or "us-east-1"
        )
        _dynamodb = boto3.resource(
            "dynamodb",
            region_name=region,
            config=Config(retries={"max_attempts": 3, "mode": "standard"}),
        )
    return _dynamodb


def _get_table():
    """Returns a cached DynamoDB table handle; initializes lazily."""
    global _table
    if _table is None:
        table_name = os.environ.get("DYNAMODB_TABLE") or "unit-tests"
        _table = _boto3_resource().Table(table_name)
    return _table


def get_patient(patient_id: str) -> Optional[Dict[str, Any]]:
    """Gets a patient by primary key."""
    table = _get_table()
    resp = table.get_item(Key={"patient_id": patient_id})
    return resp.get("Item")


def scan_patients() -> List[Dict[str, Any]]:
    """Scans all patients with pagination."""
    table = _get_table()
    items: List[Dict[str, Any]] = []
    kwargs: Dict[str, Any] = {}
    while True:
        resp = table.scan(**kwargs)
        items.extend(resp.get("Items", []))
        lek = resp.get("LastEvaluatedKey")
        if not lek:
            break
        kwargs["ExclusiveStartKey"] = lek
    return items
