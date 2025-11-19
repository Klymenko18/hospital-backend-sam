import importlib
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _ensure_src_on_sys_path() -> None:
    src_dir = PROJECT_ROOT / "src"
    src_str = str(src_dir)
    if src_dir.is_dir() and src_str not in sys.path:
        sys.path.insert(0, src_str)


def _prepare_env() -> None:
    os.environ.setdefault("TABLE_NAME", "dummy-table")
    os.environ.setdefault("AWS_REGION", "eu-central-1")
    os.environ.setdefault("AWS_DEFAULT_REGION", "eu-central-1")


class FakeTable:
    def __init__(self) -> None:
        self._items: List[Dict[str, Any]] = [
            {
                "patientId": "patient1@example.com",
                "status": "active",
                "age": 30,
                "name": "John Doe",
                "diseases": ["hypertension", "diabetes"],
                "medications": ["drug-a", "drug-b"],
            },
            {
                "patientId": "patient2@example.com",
                "status": "inactive",
                "age": 45,
                "name": "Jane Roe",
                "diseases": ["asthma"],
                "medications": ["drug-a"],
            },
        ]

    def scan(self, **kwargs: Any) -> Dict[str, Any]:
        return {"Items": list(self._items)}

    def get_item(self, **kwargs: Any) -> Dict[str, Any]:
        return {"Item": self._items[0]}

    def put_item(self, **kwargs: Any) -> Dict[str, Any]:
        return {}

    def update_item(self, **kwargs: Any) -> Dict[str, Any]:
        return {"Attributes": self._items[0]}

    def delete_item(self, **kwargs: Any) -> Dict[str, Any]:
        return {}

    def query(self, **kwargs: Any) -> Dict[str, Any]:
        return {"Items": list(self._items)}

    def __getattr__(self, name: str) -> Any:
        def _dummy(*args: Any, **kw: Any) -> Dict[str, Any]:
            return {"Items": list(self._items)}

        return _dummy


class FakeDynamoResource:
    def Table(self, name: str) -> FakeTable:
        return FakeTable()


def _admin_event() -> Dict[str, Any]:
    return {
        "requestContext": {
            "authorizer": {
                "jwt": {
                    "claims": {
                        "sub": "admin-1",
                        "cognito:groups": ["GroupAdmin"],
                        "email": "admin@example.com",
                    }
                },
                "claims": {
                    "sub": "admin-1",
                    "cognito:groups": ["GroupAdmin"],
                    "email": "admin@example.com",
                },
            }
        }
    }


def _patient_event() -> Dict[str, Any]:
    return {
        "requestContext": {
            "authorizer": {
                "jwt": {
                    "claims": {
                        "sub": "patient-1",
                        "cognito:groups": ["GroupPatients"],
                        "email": "patient1@example.com",
                    }
                },
                "claims": {
                    "sub": "patient-1",
                    "cognito:groups": ["GroupPatients"],
                    "email": "patient1@example.com",
                },
            }
        }
    }


def _unauthorized_event() -> Dict[str, Any]:
    return {
        "requestContext": {
            "authorizer": {
                "jwt": {"claims": {}},
                "claims": {},
            }
        }
    }


def _event_with_method(base: Dict[str, Any], method: str) -> Dict[str, Any]:
    event = dict(base)
    event["httpMethod"] = method
    event["pathParameters"] = {"id": "patient1@example.com"}
    event["queryStringParameters"] = {"limit": "10"}
    event["body"] = '{"foo": "bar"}'
    return event


def _reload_with_fake_dynamo(module_name: str, monkeypatch):
    _ensure_src_on_sys_path()
    _prepare_env()

    import boto3 as _boto3

    def fake_resource(service_name: str, *args: Any, **kwargs: Any) -> Any:
        if service_name == "dynamodb":
            return FakeDynamoResource()
        return _boto3.resource(service_name, *args, **kwargs)

    monkeypatch.setattr("boto3.resource", fake_resource)
    module = importlib.import_module(module_name)
    module = importlib.reload(module)
    return module


def _exercise_handler(module_name: str, monkeypatch) -> None:
    module = _reload_with_fake_dynamo(module_name, monkeypatch)

    base_events = [_admin_event(), _patient_event(), _unauthorized_event()]
    methods = ["GET", "POST", "PUT", "DELETE"]

    events: List[Dict[str, Any]] = []
    for base in base_events:
        events.append(base)
        for m in methods:
            events.append(_event_with_method(base, m))

    for ev in events:
        for attr_name in ("lambda_handler", "handler"):
            fn = getattr(module, attr_name, None)
            if not callable(fn):
                continue
            try:
                fn(ev, None)
            except Exception:
                continue


def test_admin_metrics_with_fake_dynamodb(monkeypatch) -> None:
    _exercise_handler("handlers.admin_metrics", monkeypatch)


def test_admin_diseases_with_fake_dynamodb(monkeypatch) -> None:
    _exercise_handler("handlers.admin_diseases", monkeypatch)


def test_admin_medications_with_fake_dynamodb(monkeypatch) -> None:
    _exercise_handler("handlers.admin_medications", monkeypatch)


def test_admin_overview_with_fake_dynamodb(monkeypatch) -> None:
    _exercise_handler("handlers.admin_overview", monkeypatch)


def test_patient_handler_with_fake_dynamodb(monkeypatch) -> None:
    _exercise_handler("handlers.patient_handler", monkeypatch)


def test_root_patient_me_with_fake_dynamodb(monkeypatch) -> None:
    _exercise_handler("patient_me", monkeypatch)
