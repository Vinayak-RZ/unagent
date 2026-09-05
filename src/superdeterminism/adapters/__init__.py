"""Lazy adapter registry. Framework modules are imported only on resolve()."""

from __future__ import annotations

import importlib
import importlib.util
from collections.abc import Callable
from typing import Any, Protocol

from superdeterminism.models import Trace

_MODULES = {
    "langgraph": "superdeterminism.adapters.langgraph",
    "custom": "superdeterminism.adapters.custom",
    "atif": "superdeterminism.adapters.atif",
    "crewai": "superdeterminism.adapters.crewai",
}
_EXTRAS = {
    "langgraph": ("langgraph", "langchain"),
    "custom": (),
    "atif": (),
    "crewai": (),  # export mapper; no hard crewai import
}


class Adapter(Protocol):
    def load(self, path_or_bytes: Any) -> list[Trace]: ...


class AdapterError(ValueError):
    """Unknown adapter or missing optional extra."""


def extra_installed(name: str) -> bool:
    pkgs = _EXTRAS.get(name)
    if pkgs is None:
        return False
    if not pkgs:
        return True
    return all(importlib.util.find_spec(pkg) is not None for pkg in pkgs)


def resolve(name: str) -> Callable[..., Any]:
    if name not in _MODULES:
        raise AdapterError(f"unknown adapter: {name}")
    if not extra_installed(name):
        raise AdapterError(
            f"adapter {name} requires: pip install 'superdeterminism[{name}]'"
        )
    mod = importlib.import_module(_MODULES[name])
    load = getattr(mod, "load", None)
    if load is None:
        raise AdapterError(f"adapter {name} has no load()")
    return load
