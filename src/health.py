"""Lambda health handler."""

from __future__ import annotations

from typing import Any, Dict

from common.helpers import json_response


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Public /health endpoint."""
    return json_response(200, {"service": "hospital-backend-sam", "status": "OK"})
