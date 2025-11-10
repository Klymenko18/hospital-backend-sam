import json
import os
import boto3

TABLE_NAME = os.environ["TABLE_NAME"]
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def _is_admin(event: dict) -> bool:
    claims = (event.get("requestContext", {})
                   .get("authorizer", {})
                   .get("jwt", {})
                   .get("claims", {}))
    groups = claims.get("cognito:groups", "")
    if isinstance(groups, str):
        # Cognito may deliver groups as a comma-separated string
        return "admin" in [g.strip() for g in groups.split(",")] if groups else False
    if isinstance(groups, list):
        return "admin" in groups
    return False


def handler(event, context):
    """Return basic aggregates for admin only."""
    if not _is_admin(event):
        return {"statusCode": 403, "body": json.dumps({"message": "forbidden"})}

    # Simple aggregate: total patients and active count
    scan = table.scan(ProjectionExpression="#pid, #st", ExpressionAttributeNames={
        "#pid": "patient_id", "#st": "status"
    })
    items = scan.get("Items", [])
    total = len(items)
    active = sum(1 for it in items if it.get("status") == "active")

    body = {
        "total_patients": total,
        "active_patients": active
    }
    return {"statusCode": 200, "headers": {"Content-Type": "application/json"}, "body": json.dumps(body)}
