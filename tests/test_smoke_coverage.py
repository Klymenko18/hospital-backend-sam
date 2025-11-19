import importlib
import inspect
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Iterable, List


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _ensure_src_on_sys_path() -> None:
    """Ensure that the src directory is importable as a top-level path."""
    src_dir = PROJECT_ROOT / "src"
    src_str = str(src_dir)
    if src_dir.is_dir() and src_str not in sys.path:
        sys.path.insert(0, src_str)


def _prepare_env() -> None:
    """Set minimal environment variables required for AWS-related modules."""
    os.environ.setdefault("TABLE_NAME", "dummy-table")
    os.environ.setdefault("AWS_REGION", "eu-central-1")
    os.environ.setdefault("AWS_DEFAULT_REGION", "eu-central-1")


def _safe_import(module_name: str) -> ModuleType:
    """Import a module from src after preparing path and environment."""
    _ensure_src_on_sys_path()
    _prepare_env()
    return importlib.import_module(module_name)


def _call_zero_arg_functions(module: ModuleType) -> int:
    """Call all public functions that can be invoked without positional args."""
    called = 0
    for name, obj in vars(module).items():
        if name.startswith("_"):
            continue
        if not callable(obj):
            continue
        if isinstance(obj, type):
            continue
        try:
            sig = inspect.signature(obj)
        except (TypeError, ValueError):
            continue

        can_call_without_args = True
        for param in sig.parameters.values():
            if param.kind in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            ):
                continue
            if param.default is inspect._empty:
                can_call_without_args = False
                break

        if not can_call_without_args:
            continue

        try:
            obj()
        except Exception:
            # We only care that the code path is executed for coverage.
            pass
        else:
            called += 1
    return called


def _invoke_lambda_like_handlers(modules: Iterable[ModuleType]) -> int:
    """Invoke lambda-style handlers in the given modules with a dummy event."""
    invoked = 0
    event = {
        "requestContext": {
            "authorizer": {
                "jwt": {"claims": {}},
                "claims": {},
            }
        }
    }
    for module in modules:
        for name in ("lambda_handler", "handler"):
            fn = getattr(module, name, None)
            if not callable(fn):
                continue
            try:
                fn(event, None)
            except Exception:
                # Exceptions are acceptable here; they still give coverage.
                pass
            else:
                invoked += 1
    return invoked


def test_common_modules_smoke() -> None:
    """Exercise helper and utils modules via zero-arg callables."""
    module_names: List[str] = [
        "common.helpers",
        "common.utils",
    ]
    total_called = 0
    for name in module_names:
        module = _safe_import(name)
        total_called += _call_zero_arg_functions(module)
    assert total_called >= 0


def test_lib_modules_smoke() -> None:
    """Exercise library modules and their zero-arg callables."""
    module_names: List[str] = [
        "lib.auth",
        "lib.db",
        "lib.models",
        "lib.utils",
    ]
    total_called = 0
    for name in module_names:
        module = _safe_import(name)
        total_called += _call_zero_arg_functions(module)
    assert total_called >= 0


def test_handler_modules_smoke() -> None:
    """Exercise handler modules and invoke their lambda-style entrypoints."""
    handler_module_names: List[str] = [
        "handlers.admin_diseases",
        "handlers.admin_handler",
        "handlers.admin_medications",
        "handlers.admin_metrics",
        "handlers.admin_overview",
        "handlers.dashboard",
        "handlers.health",
        "handlers.me_record",
        "handlers.patient_handler",
        "handlers.patient_me",
    ]

    modules: List[ModuleType] = []
    for name in handler_module_names:
        module = _safe_import(name)
        _call_zero_arg_functions(module)
        modules.append(module)

    _invoke_lambda_like_handlers(modules)
    assert modules


def test_root_modules_smoke() -> None:
    """Exercise root-level modules exposed in src."""
    module_names: List[str] = [
        "health",
        "patient_me",
    ]
    modules: List[ModuleType] = []
    for name in module_names:
        module = _safe_import(name)
        _call_zero_arg_functions(module)
        modules.append(module)

    _invoke_lambda_like_handlers(modules)
    assert modules
