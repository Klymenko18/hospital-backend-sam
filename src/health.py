"""Lambda health handler.

Exposes a simple health/status endpoint and demonstrates importing from the
local `common` package to verify SAM packaging is correct.
"""

from __future__ import annotations

import json
from typing import Any, Dict

from common.helpers import build_ok_status


def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Build an API Gateway compatible JSON response."""
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """AWS Lambda entrypoint for the /health endpoint."""
    payload = build_ok_status(service="hospital-backend-sam")
    return _response(200, payload)
