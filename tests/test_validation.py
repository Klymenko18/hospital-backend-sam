from __future__ import annotations

import handlers.admin_overview as overview


def test_overview_400_on_invalid_bounds(monkeypatch):
    monkeypatch.setattr(overview, "scan_patients", lambda: [])
    event = {
        "requestContext": {"authorizer": {"jwt": {"claims": {"cognito:groups": "Admin"}}}},
        "queryStringParameters": {"min_age": "60", "max_age": "20"},
    }
    resp = overview.lambda_handler(event, None)
    assert resp["statusCode"] == 400
