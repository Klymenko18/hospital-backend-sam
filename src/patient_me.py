import os, json, base64
from decimal import Decimal
from typing import Any, Dict
import boto3
from common.helpers import json_response

dynamodb = boto3.resource("dynamodb")

def _clean_decimal(obj: Any):
    if isinstance(obj, dict):
        return {k: _clean_decimal(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_clean_decimal(v) for v in obj]
    if isinstance(obj, set):
        return [_clean_decimal(v) for v in obj]
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    return obj

def _get_claims(event: Dict[str, Any]) -> Dict[str, Any]:
    rc = event.get("requestContext") or {}
    az = rc.get("authorizer") or {}
    jwt = az.get("jwt")
    if isinstance(jwt, dict) and isinstance(jwt.get("claims"), dict):
        return jwt["claims"]
    claims = az.get("claims")
    return claims if isinstance(claims, dict) else {}

def lambda_handler(event, context):
    table_name = os.environ.get("TABLE_NAME")
    pk_name = os.environ.get("PK_NAME", "patientId")
    if not table_name:
        return json_response(500, {"error": "TABLE_NAME env not set"})

    claims = _get_claims(event)
    sub = claims.get("sub")
    if not sub:
        return json_response(401, {"error": "No sub in token"})

    table = dynamodb.Table(table_name)
    resp = table.get_item(Key={pk_name: sub})
    item = resp.get("Item")
    if not item:
        return json_response(404, {"error": "Patient not found", "patientId": sub})

    return json_response(200, _clean_decimal(item))
