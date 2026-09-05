from __future__ import annotations

from pathlib import Path

import pytest

from superdeterminism.ingest import IngestError
from superdeterminism.pipeline import recommend_traces
from superdeterminism.sinks import load_langfuse_file, load_langsmith_file, load_mlflow_file, load_sink

FIX = Path(__file__).resolve().parents[1] / "fixtures" / "sinks"


def test_langfuse_file_recommend() -> None:
    traces = load_langfuse_file(FIX / "langfuse_export.json")
    assert traces
    recs = recommend_traces(traces, n_min=30)
    assert any(r.action.value == "FlipToDet" for r in recs)


def test_langsmith_and_mlflow_files() -> None:
    assert load_langsmith_file(FIX / "langsmith_export.json")
    assert load_mlflow_file(FIX / "mlflow_export.json")


def test_load_sink_dispatch() -> None:
    traces = load_sink("langfuse", path=FIX / "langfuse_export.json")
    assert sum(len(t.spans) for t in traces) == 40


def test_live_requires_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    with pytest.raises(IngestError):
        load_sink("langfuse", live=True)
