from __future__ import annotations

from typing import Any, Dict

from lib.auth import extract_claims, require_admin
from lib.db import scan_patients
from lib.utils import json_response, compute_age_years, parse_age_bounds


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Returns histogram of diseases for admin with optional age filtering.
    """
    try:
        claims = extract_claims(event)
        require_admin(claims)
    except PermissionError as e:
        return json_response(403, {"message": str(e)})

    params = event.get("queryStringParameters") or {}
    try:
        min_age, max_age = parse_age_bounds(params)
    except ValueError as e:
        return json_response(400, {"message": str(e)})

    items = scan_patients()
    counts: Dict[str, int] = {}

    def age_ok(iso: str) -> bool:
        age = compute_age_years(iso)
        if min_age is not None and age < min_age:
            return False
        if max_age is not None and age > max_age:
            return False
        return True

    for it in items:
        if not age_ok(it["date_of_birth"]):
            continue
        for d in it.get("diseases", []):
            if d:
                counts[d] = counts.get(d, 0) + 1
    return json_response(200, {"diseases": counts})
