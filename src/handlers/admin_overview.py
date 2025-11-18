from __future__ import annotations

from typing import Any, Dict, List

from lib.auth import extract_claims, require_admin
from lib.db import scan_patients
from lib.models import MetricsOverview, TopItem
from lib.utils import json_response, compute_age_years, average, parse_age_bounds


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Computes aggregated metrics for admin with optional age filtering."""
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
    filtered: List[Dict[str, Any]] = []
    for it in items:
        age = compute_age_years(it["date_of_birth"])
        if min_age is not None and age < min_age:
            continue
        if max_age is not None and age > max_age:
            continue
        filtered.append(it)

    total = len(filtered)
    avg_bmi = average([float(it.get("bmi", 0.0)) for it in filtered])

    counts_by_sex: Dict[str, int] = {}
    for it in filtered:
        sex = it.get("sex") or ""
        counts_by_sex[sex] = counts_by_sex.get(sex, 0) + 1

    avg_age = average([compute_age_years(it["date_of_birth"]) for it in filtered])

    disease_counts: Dict[str, int] = {}
    for it in filtered:
        for d in it.get("diseases", []):
            if d:
                disease_counts[d] = disease_counts.get(d, 0) + 1

    # Build typed TopItem list (prevents pydantic coercion issues)
    top_items: List[TopItem] = [
        TopItem(name=name, count=count) for name, count in disease_counts.items()
    ]
    top_items.sort(key=lambda x: x.count, reverse=True)
    top_items = top_items[:10]

    payload = MetricsOverview(
        total_patients=total,
        avg_bmi=avg_bmi,
        counts_by_sex=counts_by_sex,
        avg_age_years=avg_age,
        top_diseases=top_items,
    )
    return json_response(200, payload.model_dump())
