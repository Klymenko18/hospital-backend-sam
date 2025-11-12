import json
import os
from typing import Any, Dict

import boto3


def _email_from_jwt(event: Dict[str, Any]) -> str:
    """Extract the email claim from a Cognito-authorized request."""
    claims = event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {})
    email = claims.get("email")
    if not email:
        raise ValueError("Missing email claim")
    return email


def _dynamo():
    """Return a DynamoDB low-level client."""
    region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "eu-central-1"
    return boto3.client("dynamodb", region_name=region)


def handler(event, context):
    """Handle GET/PUT /me/record using patientId as HASH key."""
    method = event.get("requestContext", {}).get("http", {}).get("method", "GET").upper()
    table = os.getenv("TABLE_NAME")
    pk_name = os.getenv("PK_NAME", "patientId")
    email = _email_from_jwt(event)
    db = _dynamo()

    if method == "GET":
        res = db.get_item(TableName=table, Key={pk_name: {"S": email}})
        item = res.get("Item")
        body = {
            "patientId": email,
            "diagnosis": item.get("diagnosis", {}).get("S") if item else None,
            "updatedAt": item.get("updatedAt", {}).get("S") if item else None,
        }
        return {"statusCode": 200, "headers": {"content-type": "application/json"}, "body": json.dumps(body)}

    if method == "PUT":
        payload = json.loads(event.get("body") or "{}")
        diagnosis = payload.get("diagnosis")
        if not diagnosis:
            return {"statusCode": 400, "body": json.dumps({"error": "diagnosis is required"})}
        db.update_item(
            TableName=table,
            Key={pk_name: {"S": email}},
            UpdateExpression="SET diagnosis = :d, updatedAt = :t",
            ExpressionAttributeValues={
                ":d": {"S": str(diagnosis)},
                ":t": {"S": payload.get("updatedAt") or "1970-01-01T00:00:00Z"},
            },
        )
        return {"statusCode": 204, "body": ""}

    return {"statusCode": 405, "body": json.dumps({"error": "method not allowed"})}
