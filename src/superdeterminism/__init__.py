"""Agnostic determinism advisor (P0). No framework imports."""

from superdeterminism.models import (
    DetClass,
    NodeKind,
    Recommendation,
    Span,
    Trace,
)
from superdeterminism.pipeline import recommend_traces
from superdeterminism.simulate import simulate_design, simulate_report, simulate_what_if

__all__ = [
    "DetClass",
    "NodeKind",
    "Recommendation",
    "Span",
    "Trace",
    "recommend_traces",
    "simulate_design",
    "simulate_report",
    "simulate_what_if",
]
__version__ = "0.2.0"
