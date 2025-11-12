import json
import os
from typing import Any, Dict, List

import boto3


def _is_admin(event: Dict[str, Any]) -> bool:
    """Return True if the caller is in the Cognito admin group."""
    claims = event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {})
    groups = claims.get("cognito:groups", "") or ""
    if isinstance(groups, list):
        return "GroupAdmin" in groups
    return "GroupAdmin" in str(groups).split(",")


def _dynamo():
    """Return a DynamoDB client."""
    region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "eu-central-1"
    return boto3.client("dynamodb", region_name=region)


def handler(event, context):
    """Serve /admin/stats with basic counts, using an aggregates table when possible."""
    if not _is_admin(event):
        return {"statusCode": 403, "body": json.dumps({"error": "forbidden"})}

    db = _dynamo()
    records = os.getenv("TABLE_NAME")
    aggs = os.getenv("AGG_TABLE") or os.getenv("AGGREGATES_TABLE") or "AdminAggregates-dev"

    try:
        agg = db.get_item(TableName=aggs, Key={"aggKey": {"S": "daily"}}).get("Item") or {}
        snapshot = {
            "patientsTotal": int(agg.get("patientsTotal", {}).get("N", "0")),
            "updatedToday": int(agg.get("updatedToday", {}).get("N", "0")),
        }
        return {"statusCode": 200, "headers": {"content-type": "application/json"}, "body": json.dumps({"snapshot": snapshot})}
    except Exception:
        resp = db.scan(TableName=records, ProjectionExpression="patientId")
        count = resp.get("Count", 0)
        return {"statusCode": 200, "headers": {"content-type": "application/json"}, "body": json.dumps({"snapshot": {"patientsTotal": count}})}
