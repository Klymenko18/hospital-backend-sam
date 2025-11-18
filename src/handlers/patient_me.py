"""Patient profile Lambda handler."""

import json
import os
from typing import Any, Dict, Optional
from decimal import Decimal

import boto3
from botocore.exceptions import BotoCoreError, ClientError

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.getenv("PATIENT_TABLE_NAME", "")


def _get_claims(event: Dict[str, Any]) -> Dict[str, Any]:
    """Extract JWT claims from API Gateway event for HTTP API v2 or v1."""
    context = event.get("requestContext") or {}
    authorizer = context.get("authorizer") or {}

    jwt = authorizer.get("jwt")
    if isinstance(jwt, dict):
        claims = jwt.get("claims")
        if isinstance(claims, dict):
            return claims

    claims = authorizer.get("claims")
    if isinstance(claims, dict):
        return claims

    return {}


def _load_patient(email: Optional[str]) -> Optional[Dict[str, Any]]:
    """Load patient record from DynamoDB by email, if possible."""
    if not email or not TABLE_NAME:
        return None

    try:
        table = dynamodb.Table(TABLE_NAME)
        resp = table.get_item(Key={"patientId": email})
    except (BotoCoreError, ClientError):
        return None

    return resp.get("Item")


def _to_plain(obj: Any) -> Any:
    """Recursively convert Decimals to int/float for JSON serialization."""
    if isinstance(obj, Decimal):
        # якщо ціле число – віддаємо int, інакше float
        return int(obj) if obj % 1 == 0 else float(obj)
    if isinstance(obj, dict):
        return {k: _to_plain(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_plain(v) for v in obj]
    return obj


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Return profile information for the authenticated patient."""
    claims = _get_claims(event)

    email = claims.get("email")
    sub = claims.get("sub") or claims.get("cognito:username")

    patient = _load_patient(email)
    patient_plain = _to_plain(patient) if patient is not None else None

    body = {
        "user": {
            "email": email,
            "sub": sub,
        },
        "patient": patient_plain,
    }

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": json.dumps(body),
    }
