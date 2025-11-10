"""Return current patient's record from DynamoDB by Cognito subject."""

from __future__ import annotations

from typing import Any, Dict

from common.helpers import get_jwt_claims, get_table, json_response


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Protected GET /patient/me. Looks up item by patientId == sub."""
    claims = get_jwt_claims(event)
    sub = claims.get("sub")
    if not sub:
        return json_response(401, {"message": "Unauthorized"})

    table = get_table()
    resp = table.get_item(Key={"patientId": sub})
    item = resp.get("Item")
    if not item:
        return json_response(404, {"message": "Record not found"})

    return json_response(200, item)
