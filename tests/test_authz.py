import importlib
import os
import sys
from pathlib import Path
from types import ModuleType


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _prepare_src_on_sys_path() -> None:
    """Ensure that the src directory is importable as a top-level path."""
    src_dir = PROJECT_ROOT / "src"
    src_str = str(src_dir)
    if src_dir.is_dir() and src_str not in sys.path:
        sys.path.insert(0, src_str)


def _import_handlers():
    """Import patient and admin handler modules."""
    _prepare_src_on_sys_path()
    os.environ.setdefault("TABLE_NAME", "dummy-table")
    os.environ.setdefault("AWS_DEFAULT_REGION", "eu-central-1")
    os.environ.setdefault("AWS_REGION", "eu-central-1")
    patient = importlib.import_module("handlers.patient_me")
    admin = importlib.import_module("handlers.admin_metrics")
    return patient, admin


def test_patient_me_module_imports() -> None:
    """Patient handler module must be importable."""
    patient, _ = _import_handlers()
    assert isinstance(patient, ModuleType)


def test_patient_me_has_lambda_handler() -> None:
    """Patient handler module must expose a callable lambda_handler."""
    patient, _ = _import_handlers()
    assert hasattr(patient, "lambda_handler")
    assert callable(getattr(patient, "lambda_handler"))
