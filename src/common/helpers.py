"""Shared helpers: responses, claims, DynamoDB client."""

from __future__ import annotations

import json
import os
from typing import Any, Dict

import boto3


def json_response(status: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Build an API Gateway compatible JSON response."""
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json", "Cache-Control": "no-store"},
        "body": json.dumps(body),
    }


def get_table():
    """Return a DynamoDB Table resource using TABLE_NAME env var."""
    table_name = os.environ["TABLE_NAME"]
    return boto3.resource("dynamodb").Table(table_name)


def get_jwt_claims(event: Dict[str, Any]) -> Dict[str, Any]:
    """Extract JWT claims from API Gateway HTTP API event."""
    return (
        event.get("requestContext", {})
        .get("authorizer", {})
        .get("jwt", {})
        .get("claims", {})
    )


def require_admin(claims: Dict[str, Any]) -> None:
    """Raise PermissionError if user is not in 'admin' group."""
    groups = claims.get("cognito:groups", "")
    if isinstance(groups, str):
        is_admin = "admin" in groups.split(",")
    elif isinstance(groups, list):
        is_admin = "admin" in groups
    else:
        is_admin = False
    if not is_admin:
        raise PermissionError("Admin group required.")
