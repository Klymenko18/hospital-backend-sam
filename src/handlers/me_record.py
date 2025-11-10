"""Return the authenticated patient's own record by Cognito 'sub'."""
import json
import os
import boto3

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.getenv("PATIENT_TABLE_NAME", "")
table = dynamodb.Table(TABLE_NAME)


def handler(event, _ctx):
    """GET /me/record."""
    claims = (event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {}))
    sub = claims.get("sub")
    email = claims.get("email")

    if not sub:
        return {"statusCode": 401, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"detail": "unauthorized"})}

    resp = table.get_item(Key={"patient_id": sub})
    item = resp.get("Item")
    if not item:
        item = {"patient_id": sub, "email": email, "status": "unknown"}

    return {"statusCode": 200, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"status": "ok", "record": item})}
