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


def _import_admin_metrics() -> ModuleType:
    """Import the admin metrics module from the handlers package."""
    _prepare_src_on_sys_path()
    os.environ.setdefault("TABLE_NAME", "dummy-table")
    os.environ.setdefault("AWS_DEFAULT_REGION", "eu-central-1")
    os.environ.setdefault("AWS_REGION", "eu-central-1")
    return importlib.import_module("handlers.admin_metrics")


def test_admin_metrics_module_imports() -> None:
    """Admin metrics module must be importable."""
    module = _import_admin_metrics()
    assert isinstance(module, ModuleType)


def test_admin_metrics_has_callable_entrypoint() -> None:
    """Admin metrics module must have at least one callable symbol."""
    module = _import_admin_metrics()
    names = [name for name in dir(module) if callable(getattr(module, name))]
    assert names
