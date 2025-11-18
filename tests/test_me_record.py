from __future__ import annotations

from typing import Any, Dict

import importlib

me_record = importlib.import_module("src.handlers.me_record")


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


def test_me_record_ok(monkeypatch):
    monkeypatch.setattr(me_record, "_table", _FakeTable({"patient_id": "abc", "full_name": "Jane Doe"}))
    event = _event_with_claims("abc")
    res = me_record.handler(event, context=None)
    assert res["statusCode"] == 200
    assert "record" in res_body(res)


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


def res_body(res: Dict[str, Any]) -> Dict[str, Any]:
    import json

    return json.loads(res["body"])
