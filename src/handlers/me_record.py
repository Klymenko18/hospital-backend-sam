from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import Any, Dict

# Ensure 'src/' is on sys.path for local tests
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

me_record = importlib.import_module("handlers.me_record")


class _FakeTable:
    def __init__(self, item: Dict[str, Any] | None):
        self._item = item

    def get_item(self, Key: Dict[str, Any]) -> Dict[str, Any]:
        return {"Item": self._item} if self._item else {}


def _event_with_claims(sub: str | None) -> Dict[str, Any]:
    claims = {}
    if sub:
        claims["sub"] = sub
    return {"requestContext": {"authorizer": {"jwt": {"claims": claims}}}}


def _body(res: Dict[str, Any]) -> Dict[str, Any]:
    return json.loads(res["body"])


def test_me_record_ok(monkeypatch):
    monkeypatch.setattr(me_record, "_table", _FakeTable({"patient_id": "abc", "full_name": "Jane Doe"}))
    event = _event_with_claims("abc")
    res = me_record.handler(event, context=None)
    assert res["statusCode"] == 200
    assert "record" in _body(res)


def test_me_record_not_found(monkeypatch):
    monkeypatch.setattr(me_record, "_table", _FakeTable(None))
    event = _event_with_claims("abc")
    res = me_record.handler(event, context=None)
    assert res["statusCode"] == 404


def test_me_record_unauthorized(monkeypatch):
    monkeypatch.setattr(me_record, "_table", _FakeTable(None))
    event = _event_with_claims(None)
    res = me_record.handler(event, context=None)
    assert res["statusCode"] == 401
