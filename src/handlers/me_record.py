import json
import os
import boto3
from botocore.exceptions import ClientError

TABLE_NAME = os.environ["TABLE_NAME"]
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def _user_sub(event: dict) -> str | None:
    claims = (event.get("requestContext", {})
                   .get("authorizer", {})
                   .get("jwt", {})
                   .get("claims", {}))
    return claims.get("sub")


def handler(event, context):
    """Return current user's record by cognito sub."""
    sub = _user_sub(event)
    if not sub:
        return {"statusCode": 401, "body": json.dumps({"message": "unauthorized"})}

    try:
        resp = table.get_item(Key={"patient_id": sub})
        item = resp.get("Item")
        if not item:
            return {"statusCode": 404, "body": json.dumps({"message": "not_found"})}
        return {"statusCode": 200, "headers": {"Content-Type": "application/json"}, "body": json.dumps(item)}
    except ClientError as e:
        return {"statusCode": 500, "body": json.dumps({"message": "dynamodb_error", "error": str(e)})}
