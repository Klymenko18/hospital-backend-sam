from __future__ import annotations

import json
from typing import Any, Dict
import handlers.patient_me as h


def test_patient_me_happy_path(monkeypatch):
    def fake_get_patient(pid: str):
        return {
            "patient_id": pid,
            "name": "Jane Doe",
            "sex": "F",
            "date_of_birth": "1985-06-15",
            "bmi": 24.1,
            "medications": [],
            "diseases": [],
        }

    monkeypatch.setattr(h, "get_patient", fake_get_patient)
    event: Dict[str, Any] = {
        "requestContext": {"authorizer": {"jwt": {"claims": {"sub": "abc-123"}}}}
    }
    resp = h.lambda_handler(event, None)
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["patient_id"] == "abc-123"


def test_patient_me_not_found(monkeypatch):
    monkeypatch.setattr(h, "get_patient", lambda _: None)
    event = {"requestContext": {"authorizer": {"jwt": {"claims": {"sub": "missing"}}}}}
    resp = h.lambda_handler(event, None)
    assert resp["statusCode"] == 404


def test_patient_me_unauthorized_without_sub():
    event = {"requestContext": {"authorizer": {"jwt": {"claims": {}}}}}
    resp = h.lambda_handler(event, None)
    assert resp["statusCode"] == 401
