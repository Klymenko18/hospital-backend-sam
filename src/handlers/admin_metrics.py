"""Return admin-only aggregate metrics from DynamoDB."""
import json
import os
import boto3

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.getenv("PATIENT_TABLE_NAME", "")
table = dynamodb.Table(TABLE_NAME)


def _is_admin(claims) -> bool:
    groups = claims.get("cognito:groups")
    if isinstance(groups, list):
        return "admin" in groups
    if isinstance(groups, str):
        return "admin" in [g.strip() for g in groups.split(",")]
    return False


def _count_patients() -> int:
    total = 0
    last_key = None
    while True:
        kwargs = {"Select": "COUNT"}
        if last_key:
            kwargs["ExclusiveStartKey"] = last_key
        resp = table.scan(**kwargs)
        total += resp.get("Count", 0)
        last_key = resp.get("LastEvaluatedKey")
        if not last_key:
            break
    return total


def handler(event, _ctx):
    """GET /admin/metrics. Requires 'admin' group."""
    claims = (event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {}))
    if not _is_admin(claims):
        return {"statusCode": 403, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"detail": "forbidden"})}

    body = {"status": "ok", "metrics": {"patients_total": _count_patients()}}
    return {"statusCode": 200, "headers": {"Content-Type": "application/json"}, "body": json.dumps(body)}
