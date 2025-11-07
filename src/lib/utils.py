from __future__ import annotations

import json
import os
from datetime import date, datetime
from statistics import mean
from typing import Any, Dict, Iterable, Tuple


def json_response(status: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Builds a consistent JSON HTTP response with CORS headers.
    """
    origin = os.environ.get("ALLOWED_ORIGIN", "*")
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "GET,OPTIONS",
        },
        "body": json.dumps(body),
    }


def parse_iso_date(value: str) -> date:
    """
    Parses an ISO date string (YYYY-MM-DD) into date.
    """
    return datetime.strptime(value, "%Y-%m-%d").date()


def compute_age_years(born_iso: str) -> float:
    """
    Computes age in years given ISO birth date.
    """
    b = parse_iso_date(born_iso)
    today = date.today()
    delta = today.toordinal() - b.toordinal()
    return round(delta / 365.2425, 2)


def average(values: Iterable[float]) -> float:
    """
    Returns the average of values or 0.0 if empty.
    """
    vals = list(values)
    return round(mean(vals), 2) if vals else 0.0


def histogram(values: Iterable[str]) -> Dict[str, int]:
    """
    Returns a frequency dictionary for values.
    """
    counts: Dict[str, int] = {}
    for v in values:
        if not v:
            continue
        counts[v] = counts.get(v, 0) + 1
    return counts


def parse_age_bounds(params: Dict[str, Any]) -> Tuple[float | None, float | None]:
    """
    Parses min_age/max_age query parameters and validates numeric order.
    """
    min_age = params.get("min_age")
    max_age = params.get("max_age")

    def _num(x):
        if x is None or x == "":
            return None
        return float(x)

    mn = _num(min_age)
    mx = _num(max_age)
    if mn is not None and mn < 0:
        raise ValueError("min_age must be >= 0")
    if mx is not None and mx < 0:
        raise ValueError("max_age must be >= 0")
    if mn is not None and mx is not None and mn > mx:
        raise ValueError("min_age must be <= max_age")
    return mn, mx
