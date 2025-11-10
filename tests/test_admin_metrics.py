from __future__ import annotations

from typing import Any, Dict, List

import importlib

admin_metrics = importlib.import_module("src.handlers.admin_metrics")


class _FakeTable:
    def __init__(self, items: List[Dict[str, Any]]):
        self._items = items

    def scan(self) -> Dict[str, Any]:
        return {"Items": self._items}


def _event_groups(groups) -> Dict[str, Any]:
    return {"requestContext": {"authorizer": {"jwt": {"claims": {"cognito:groups": groups}}}}}


def res_body(res: Dict[str, Any]) -> Dict[str, Any]:
    import json

    return json.loads(res["body"])


def test_admin_metrics_ok(monkeypatch):
    items = [
        {"patient_id": "a", "diagnoses": ["A", "B", "A"]},
        {"patient_id": "b", "diagnoses": ["A"]},
    ]
    monkeypatch.setattr(admin_metrics, "_table", _FakeTable(items))
    event = _event_groups(["admin"])
    res = admin_metrics.handler(event, context=None)
    assert res["statusCode"] == 200
    body = res_body(res)
    assert body["total_patients"] == 2
    assert body["top_diagnoses"][0]["diagnosis"] == "A"
    assert body["top_diagnoses"][0]["count"] == 3


def test_admin_metrics_forbidden(monkeypatch):
    monkeypatch.setattr(admin_metrics, "_table", _FakeTable([]))
    event = _event_groups(["patients"])
    res = admin_metrics.handler(event, context=None)
    assert res["statusCode"] == 403
