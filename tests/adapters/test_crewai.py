from __future__ import annotations

from pathlib import Path

import pytest

from superdeterminism.adapters import AdapterError, resolve
from superdeterminism.ingest import IngestError

FIX = Path(__file__).resolve().parents[1] / "fixtures" / "adapters"


def test_crewai_maps_tasks() -> None:
    load = resolve("crewai")
    traces = load(FIX / "crewai_kickoff.json")
    assert traces
    names = [s.name for s in traces[0].spans]
    assert any("researcher" in n for n in names)
    assert any("search" in n for n in names)


def test_crewai_refuses_langgraph_payload() -> None:
    load = resolve("crewai")
    with pytest.raises(IngestError, match="refuse"):
        load(FIX / "langgraph_shaped.json")


def test_unknown_adapter() -> None:
    with pytest.raises(AdapterError):
        resolve("not-a-real-adapter")
