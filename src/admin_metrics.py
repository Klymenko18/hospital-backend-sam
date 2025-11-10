"""Return aggregate admin metrics over PatientRecords."""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, Iterable

from common.helpers import get_jwt_claims, get_table, json_response, require_admin


def _safe_list(value: Any) -> Iterable[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Protected GET /admin/metrics. Requires 'admin' group."""
    claims = get_jwt_claims(event)
    try:
        require_admin(claims)
    except PermissionError:
        return json_response(403, {"message": "Forbidden"})

    table = get_table()
    items = []
    scan_kwargs: Dict[str, Any] = {}
    while True:
        page = table.scan(**scan_kwargs)
        items.extend(page.get("Items", []))
        last_key = page.get("LastEvaluatedKey")
        if not last_key:
            break
        scan_kwargs["ExclusiveStartKey"] = last_key

    total_patients = len(items)
    conditions = Counter()
    allergies = Counter()
    for it in items:
        for c in _safe_list(it.get("conditions")):
            conditions[c] += 1
        for a in _safe_list(it.get("allergies")):
            allergies[a] += 1

    payload = {
        "totalPatients": total_patients,
        "topConditions": conditions.most_common(5),
        "topAllergies": allergies.most_common(5),
    }
    return json_response(200, payload)
