from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Union


_LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
_logger = logging.getLogger("app")
if not _logger.handlers:
    _handler = logging.StreamHandler()
    _formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    _handler.setFormatter(_formatter)
    _logger.addHandler(_handler)
_logger.setLevel(_LOG_LEVEL)


def logger() -> logging.Logger:
    """Return module-level logger configured by LOG_LEVEL."""
    return _logger


def json_response(status: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Return a JSON HTTP response compatible with API Gateway."""
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def claims_from_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Extract JWT claims from the HTTP API event."""
    return (
        event.get("requestContext", {})
        .get("authorizer", {})
        .get("jwt", {})
        .get("claims", {})
        or {}
    )


def groups_from_claims(claims: Dict[str, Any]) -> List[str]:
    """Extract Cognito groups as a list from claims."""
    groups: Union[str, List[str], None] = claims.get("cognito:groups")
    if groups is None:
        return []
    if isinstance(groups, str):
        try:
            import json as _json

            decoded = _json.loads(groups)
            return decoded if isinstance(decoded, list) else [str(groups)]
        except Exception:
            return [groups]
    return list(groups)


def is_admin(claims: Dict[str, Any]) -> bool:
    """Return True if the user belongs to 'admin' group."""
    return "admin" in set(groups_from_claims(claims))


def now_utc_iso() -> str:
    """Return current UTC time in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()
