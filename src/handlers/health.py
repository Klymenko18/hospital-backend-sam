from __future__ import annotations

import os
from typing import Any, Dict

from common.utils import json_response, now_utc_iso


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Return a public health check payload."""
    payload = {
        "status": "ok",
        "service": "hospital-mini-backend",
        "region": os.environ.get("AWS_REGION", "unknown"),
        "time_utc": now_utc_iso(),
    }
    return json_response(200, payload)
