"""Helper utilities shared by Lambda functions."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict


def build_ok_status(service: str) -> Dict[str, str]:
    """Return a canonical OK-status payload."""
    return {
        "service": service,
        "status": "OK",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
