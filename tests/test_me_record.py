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


def _import_me_handler_module() -> ModuleType:
    """Import the patient 'me' handler module, supporting both possible names."""
    _prepare_src_on_sys_path()
    os.environ.setdefault("PATIENT_TABLE_NAME", "dummy-table")

    try:
        return importlib.import_module("handlers.me_record")
    except ModuleNotFoundError:
        return importlib.import_module("handlers.patient_me")


def test_me_handler_module_imports() -> None:
    """Patient 'me' handler module must be importable."""
    module = _import_me_handler_module()
    assert isinstance(module, ModuleType)


def test_me_handler_has_handler_callable() -> None:
    """Patient 'me' handler module must define a callable handler."""
    module = _import_me_handler_module()
    assert hasattr(module, "handler")
    assert callable(module.handler)
