from __future__ import annotations

import json
from typing import Any, Dict
import handlers.admin_overview as overview
import handlers.admin_diseases as diseases
import handlers.admin_medications as meds


def admin_event(qs: Dict[str, str] | None = None):
    return {
        "requestContext": {"authorizer": {"jwt": {"claims": {"cognito:groups": "Admin"}}}},
        "queryStringParameters": qs,
    }


def patients_fixture():
    return [
        {
            "patient_id": "1",
            "name": "A",
            "sex": "M",
            "date_of_birth": "1980-01-01",
            "bmi": 25.0,
            "medications": ["atorvastatin 20 mg"],
            "diseases": ["hypertension"],
        },
        {
            "patient_id": "2",
            "name": "B",
            "sex": "F",
            "date_of_birth": "1990-01-01",
            "bmi": 27.0,
            "medications": ["metformin 500 mg"],
            "diseases": ["type 2 diabetes", "hypertension"],
        },
    ]


def test_overview(monkeypatch):
    monkeypatch.setattr(overview, "scan_patients", lambda: patients_fixture())
    resp = overview.lambda_handler(admin_event(), None)
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["total_patients"] == 2
    assert "avg_bmi" in body
    assert "counts_by_sex" in body
    assert "top_diseases" in body


def test_diseases_hist(monkeypatch):
    monkeypatch.setattr(diseases, "scan_patients", lambda: patients_fixture())
    resp = diseases.lambda_handler(admin_event(), None)
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["diseases"]["hypertension"] == 2


def test_meds_hist(monkeypatch):
    monkeypatch.setattr(meds, "scan_patients", lambda: patients_fixture())
    resp = meds.lambda_handler(admin_event(), None)
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert sum(body["medications"].values()) == 2


def test_admin_forbidden_when_not_in_group(monkeypatch):
    monkeypatch.setattr(overview, "scan_patients", lambda: [])
    event = {"requestContext": {"authorizer": {"jwt": {"claims": {"cognito:groups": "Patients"}}}}}
    resp = overview.lambda_handler(event, None)
    assert resp["statusCode"] == 403
