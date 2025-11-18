"""Health check Lambda handler."""

import json
from typing import Any, Dict


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Return basic health information for the API."""
    body = {
      "status": "ok",
      "service": "hospital-backend",
      "version": "1.0.0"
    }

    return {
      "statusCode": 200,
      "headers": {
        "Content-Type": "application/json"
      },
      "body": json.dumps(body)
    }
