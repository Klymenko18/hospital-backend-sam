from __future__ import annotations

import json
import os
import sys
from urllib.request import Request, urlopen


def _get(url: str, token: str | None = None):
    req = Request(url)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urlopen(req) as r:
        return r.getcode(), r.read().decode()


def main() -> None:
    """
    Calls /health, /patient/me (user token), /admin/metrics/overview (admin token).
    """
    base = os.getenv("HTTP_API_URL")
    user_jwt = os.getenv("USER_JWT")
    admin_jwt = os.getenv("ADMIN_JWT")
    if not base:
        print("HTTP_API_URL is required", file=sys.stderr)
        sys.exit(1)

    print("GET /health")
    code, body = _get(f"{base}/health")
    print(code, body)

    if user_jwt:
        print("GET /patient/me")
        code, body = _get(f"{base}/patient/me", user_jwt)
        print(code, body)

    if admin_jwt:
        print("GET /admin/metrics/overview")
        code, body = _get(f"{base}/admin/metrics/overview", admin_jwt)
        print(code, body)


if __name__ == "__main__":
    main()
