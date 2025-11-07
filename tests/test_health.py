from __future__ import annotations

from handlers.health import lambda_handler


def test_health_ok():
    resp = lambda_handler({}, None)
    assert resp["statusCode"] == 200
