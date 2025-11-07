from __future__ import annotations

import json
import handlers.admin_overview as overview
import handlers.patient_me as patient


def test_admin_forbidden_when_not_in_group(monkeypatch):
    monkeypatch.setattr(overview, "scan_patients", lambda: [])
    event = {"requestContext": {"authorizer": {"jwt": {"claims": {"cognito:groups": "Patients"}}}}}
    resp = overview.lambda_handler(event, None)
    assert resp["statusCode"] == 403


def test_patient_unauthorized_without_sub(monkeypatch):
    event = {"requestContext": {"authorizer": {"jwt": {"claims": {}}}}}
    resp = patient.lambda_handler(event, None)
    assert resp["statusCode"] == 401
