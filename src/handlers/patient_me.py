# src/handlers/patient_me.py
import json
import os
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError


def _response(status: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Build API Gateway HTTP API compliant response."""
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
        },
        "body": json.dumps(body),
    }


def _extract_claims(event: Dict[str, Any]) -> Dict[str, Any]:
    """Extract JWT claims from API Gateway HTTP API v2 event."""
    return (
        event.get("requestContext", {})
        .get("authorizer", {})
        .get("jwt", {})
        .get("claims", {})
    )


def _resolve_identity(claims: Dict[str, Any]) -> Optional[str]:
    """
    Determine patient's identity key.

    Preference order:
    1) email
    2) cognito:username (as a fallback; only if your PK stores usernames)
    """
    email = claims.get("email")
    if isinstance(email, str) and email:
        return email

    username = claims.get("cognito:username")
    if isinstance(username, str) and username:
        return username

    return None


def lambda_handler(event: Dict[str, Any], _ctx) -> Dict[str, Any]:
    """
    Return current patient's record from DynamoDB by identity from JWT.

    Env:
        TABLE_NAME: DynamoDB table name
        PK_NAME: partition key attribute name (default: 'patientId')
    """
    table_name = os.getenv("TABLE_NAME")
    pk_name = os.getenv("PK_NAME", "patientId")

    if not table_name:
        return _response(500, {"message": "Server misconfigured: TABLE_NAME missing"})

    claims = _extract_claims(event)
    identity = _resolve_identity(claims)

    if not identity:
        return _response(401, {"message": "Unauthorized"})

    ddb = boto3.client("dynamodb")

    try:
        item = ddb.get_item(
            TableName=table_name,
            Key={pk_name: {"S": identity}},
            ConsistentRead=True,
        ).get("Item")
    except ClientError as e:
        # Minimal surface; detailed diagnostics remain in CloudWatch Logs.
        return _response(500, {"message": "DynamoDB error", "code": e.response["Error"]["Code"]})

    if not item:
        return _response(404, {"message": "Record not found"})

    # Convert DynamoDB JSON to plain JSON succinctly
    def _unwrap(attr: Dict[str, Any]) -> Any:
        # Only handle scalar types we actually store here
        if "S" in attr:
            return attr["S"]
        if "N" in attr:
            return attr["N"]
        if "BOOL" in attr:
            return attr["BOOL"]
        return attr  # fallback (lists/maps etc.)

    result = {k: _unwrap(v) for k, v in item.items()}
    return _response(200, result)
