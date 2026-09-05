from pathlib import Path

from superdeterminism.ingest import load_traces_path
from superdeterminism.narrative import recommendations_to_narrative
from superdeterminism.pipeline import recommend_traces


def test_narrative_mentions_flip_and_disclaimer() -> None:
    recs = recommend_traces(load_traces_path(Path("examples/advisor_flip_to_det.json")))
    text = recommendations_to_narrative(recs)
    assert "simulation-based estimate" in text
    assert "classify" in text
    assert "deterministic" in text.lower()
