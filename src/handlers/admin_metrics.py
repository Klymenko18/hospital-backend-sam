"""Admin metrics Lambda handler."""

import json
import os
from collections import Counter
from typing import Any, Dict, Iterable, List

import boto3
from botocore.exceptions import BotoCoreError, ClientError

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.getenv("PATIENT_TABLE_NAME", "")
ADMIN_GROUPS_ENV = os.getenv("ADMIN_GROUPS", "GroupAdmin")


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


def _normalize_groups_string(raw: str) -> List[str]:
    """Normalize a groups string like 'GroupAdmin' or '[GroupAdmin]'."""
    cleaned = raw.strip()

    if cleaned.startswith("[") and cleaned.endswith("]"):
        cleaned = cleaned[1:-1]

    parts = [
        part.strip().strip("'\"")
        for part in cleaned.split(",")
        if part.strip()
    ]
    return parts


def _extract_groups(claims: Dict[str, Any]) -> List[str]:
    """Extract Cognito groups from claims in a normalized list form."""
    raw = claims.get("cognito:groups") or claims.get("groups")

    if isinstance(raw, str):
        return _normalize_groups_string(raw)

    if isinstance(raw, Iterable) and not isinstance(raw, (str, bytes)):
        result: List[str] = []
        for value in raw:
            if isinstance(value, str):
                result.extend(_normalize_groups_string(value))
            else:
                result.append(str(value))
        return result

    return []


def _is_admin(groups: Iterable[str]) -> bool:
    """Check if user groups intersect with allowed admin groups."""
    allowed = {g.strip() for g in ADMIN_GROUPS_ENV.split(",") if g.strip()}
    current = {g for g in groups if g}
    return bool(allowed.intersection(current))


def _scan_patients() -> List[Dict[str, Any]]:
    """Scan DynamoDB table and return all patient items."""
    if not TABLE_NAME:
        return []

    try:
        table = dynamodb.Table(TABLE_NAME)
        items: List[Dict[str, Any]] = []
        scan_kwargs: Dict[str, Any] = {}

        while True:
            response = table.scan(**scan_kwargs)
            items.extend(response.get("Items", []))

            token = response.get("LastEvaluatedKey")
            if not token:
                break
            scan_kwargs["ExclusiveStartKey"] = token

        return items
    except (BotoCoreError, ClientError):
        return []


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Return aggregated patient metrics for admin users."""
    claims = _get_claims(event)
    groups = _extract_groups(claims)

    if not _is_admin(groups):
        body = {
            "message": "Forbidden",
            "reason": "User is not in an allowed admin group",
        }
        return {
            "statusCode": 403,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(body),
        }

    patients = _scan_patients()
    total = len(patients)

    by_status_counter = Counter(item.get("status", "unknown") for item in patients)
    by_status = dict(by_status_counter)

    body = {
        "totalPatients": total,
        "byStatus": by_status,
    }

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }
