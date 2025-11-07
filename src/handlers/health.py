from __future__ import annotations

from typing import Any, Dict
from lib.utils import json_response


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Liveness endpoint.
    """
    return json_response(200, {"status": "ok"})
