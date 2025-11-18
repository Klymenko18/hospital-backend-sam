import json
import decimal
from typing import Any, Dict, Optional

# JSON-адаптер для DynamoDB Decimal та сетів
def _json_default(o: Any):
    if isinstance(o, decimal.Decimal):
        # повертай ціле як int, інакше float
        return int(o) if o % 1 == 0 else float(o)
    if isinstance(o, set):
        return list(o)
    raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")

def json_response(status_code: int, body: Any, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    base_headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
    }
    if headers:
        base_headers.update(headers)
    return {
        "statusCode": status_code,
        "headers": base_headers,
        "body": json.dumps(body, default=_json_default),
    }
