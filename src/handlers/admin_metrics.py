from __future__ import annotations

import collections
import os
from typing import Any, Dict, Iterable, List

import boto3
from common.utils import claims_from_event, is_admin, json_response, now_utc_iso, logger

_TABLE = os.environ["TABLE_NAME"]
_dynamo = boto3.resource("dynamodb")
_table = _dynamo.Table(_TABLE)
_log = logger()


def _flatten_diagnoses(items: Iterable[Dict[str, Any]]) -> List[str]:
    """Return a flattened list of all diagnoses from items."""
    result: List[str] = []
    for it in items:
        d = it.get("diagnoses") or []
        if isinstance(d, list):
            result.extend([str(x) for x in d])
    return result


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Return aggregated admin metrics across all patient records."""
    claims = claims_from_event(event)
    if not is_admin(claims):
        return json_response(403, {"error": "forbidden", "message": "Admin only"})

    scan = _table.scan()
    items = scan.get("Items", [])
    total = len(items)
    diagnoses = _flatten_diagnoses(items)
    freq = collections.Counter(diagnoses)
    top = [{"diagnosis": k, "count": v} for k, v in freq.most_common(5)]

    payload = {
        "total_patients": total,
        "top_diagnoses": top,
        "timestamp_utc": now_utc_iso(),
    }
    _log.debug("metrics_computed total=%d unique_dx=%d", total, len(freq))
    return json_response(200, payload)
