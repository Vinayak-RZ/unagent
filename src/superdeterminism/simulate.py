"""First-class architecture simulation (L0 cassette; opt-in L1 gated)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from superdeterminism.evidence import attach_replay, collect_node_stats
from superdeterminism.graph import reconstruct
from superdeterminism.models import Action, EvidenceTier, ReplayStatus, Trace
from superdeterminism.pipeline import HARD_OVERRIDE, N_MIN_DEFAULT, _decide, recommend_traces, recommendations_to_dict
from superdeterminism.replay import splice_node, tape_from_traces, verify_tape

DISCLAIMER = "simulation != production; canary is confirmatory"


@dataclass
class SimEvent:
    t: int
    kind: str
    node_id: str
    detail: str = ""
    status: str = ""


@dataclass
class WhatIfResult:
    node_id: str
    action: str
    replay_status: str
    evidence_tier: str
    n: int
    p_mode: float
    p_mode_lower: float
    schema_ok: float
    failure_rate: float
    reasons: list[str] = field(default_factory=list)
    deltas: list[str] = field(default_factory=list)
    events: list[SimEvent] = field(default_factory=list)
    disclaimer: str = DISCLAIMER
    l1_used: bool = False


@dataclass
class DesignCandidate:
    node_id: str
    score: float
    n: int
    p_mode_lower: float
    evidence_tier: str
    replay_status: str
    why: str


def _row_decide(node_id: str, row: dict[str, Any], graph: Any, n_min: int) -> tuple[Action, list[str], tuple[str, ...]]:
    return _decide(
        kind=row["kind"],
        det=row["det"],
        n=row["n"],
        n_min=n_min,
        p_mode=row["p_mode"],
        p_lower=row["p_mode_lower"],
        schema_ok=row["schema_ok"],
        failure_rate=row["failure_rate"],
        sensitive=bool(HARD_OVERRIDE.search(node_id)),
        mixed=row["mixed"],
        unknown=row["unknown"],
        tier=row["tier"],
        replay=row["replay"],
        cost_tokens=row["cost_tokens"],
        latency_ms=row["latency_ms"],
        completeness=graph.completeness,
        trust=graph.trust,
        mixed_workload=bool(row.get("mixed_workload")),
    )


def _parse_majority(majority: Any) -> Any:
    if not isinstance(majority, str):
        return majority
    if majority.startswith(("{", "[")):
        try:
            import json

            return json.loads(majority)
        except json.JSONDecodeError:
            return majority
    return majority


def simulate_what_if(
    traces: list[Trace],
    node_id: str,
    *,
    n_min: int = N_MIN_DEFAULT,
    opt_in_l1: bool = False,
) -> WhatIfResult:
    """Run L0 counterfactual splice for one node; emit playback events."""
    events: list[SimEvent] = [SimEvent(0, "load", node_id, detail=f"traces={len(traces)}")]
    if opt_in_l1:
        # ponytail: L1 live-tail runner not shipped; gate records intent only
        events.append(
            SimEvent(
                1,
                "l1_refused",
                node_id,
                detail="opt-in L1 set; live tail runner not enabled in this build",
                status="refused",
            )
        )
    graph = reconstruct(traces)
    events.append(SimEvent(2, "graph", node_id, detail=f"identity={graph.identity}"))
    stats = attach_replay(traces, collect_node_stats(traces))
    if node_id not in stats:
        return WhatIfResult(
            node_id=node_id,
            action=Action.ABSTAIN.value,
            replay_status=ReplayStatus.NOT_RUN.value,
            evidence_tier=EvidenceTier.OBSERVATIONAL.value,
            n=0,
            p_mode=0.0,
            p_mode_lower=0.0,
            schema_ok=0.0,
            failure_rate=0.0,
            reasons=[f"node_id {node_id!r} not found in reconstructed graph"],
            events=events + [SimEvent(3, "abstain", node_id, detail="missing node")],
        )
    row = stats[node_id]
    tape = tape_from_traces(traces)
    tape_ok = verify_tape(tape)
    events.append(
        SimEvent(3, "cassette", node_id, detail="verified" if tape_ok else "tampered", status="ok" if tape_ok else "fail")
    )
    majority = row.get("majority")
    if majority is not None:
        status = splice_node(traces, node_id, tape, _parse_majority(majority))
        events.append(SimEvent(4, "splice", node_id, detail=status.value, status=status.value))
    action, reasons, deltas = _row_decide(node_id, row, graph, n_min)
    events.append(SimEvent(5, "decide", node_id, detail=action.value, status=action.value))
    return WhatIfResult(
        node_id=node_id,
        action=action.value,
        replay_status=row["replay"].value,
        evidence_tier=row["tier"].value,
        n=int(row["n"]),
        p_mode=float(row["p_mode"]),
        p_mode_lower=float(row["p_mode_lower"]),
        schema_ok=float(row["schema_ok"]),
        failure_rate=float(row["failure_rate"]),
        reasons=list(reasons),
        deltas=list(deltas),
        events=events,
        l1_used=False,
    )


def simulate_design(
    traces: list[Trace],
    *,
    n_min: int = N_MIN_DEFAULT,
    limit: int = 10,
) -> list[DesignCandidate]:
    """Rank nodes for simulation / FlipToDet review."""
    graph = reconstruct(traces)
    stats = attach_replay(traces, collect_node_stats(traces))
    scored: list[DesignCandidate] = []
    for node_id, row in stats.items():
        action, reasons, _deltas = _row_decide(node_id, row, graph, n_min)
        score = float(row["p_mode_lower"]) * min(1.0, float(row["n"]) / max(n_min, 1))
        if action is Action.FLIP_TO_DET:
            score += 1.0
        elif action is Action.STRENGTHEN_SDB:
            score += 0.5
        if node_id in graph.commitment_node_ids:
            score += 0.25
        scored.append(
            DesignCandidate(
                node_id=node_id,
                score=round(score, 4),
                n=int(row["n"]),
                p_mode_lower=float(row["p_mode_lower"]),
                evidence_tier=row["tier"].value,
                replay_status=row["replay"].value,
                why=reasons[0] if reasons else action.value,
            )
        )
    scored.sort(key=lambda c: c.score, reverse=True)
    return scored[:limit]


def _cinematic_prefix_events(recs: list[Any], traces: list[Trace]) -> list[dict[str, Any]]:
    """Phased events for Studio cinematic playback (orchestration → assign → in-agent)."""
    prefix: list[dict[str, Any]] = []
    if not recs:
        return prefix
    prefix.append(
        {
            "t": -3,
            "kind": "layer_enter",
            "node_id": "supervisor_gate",
            "detail": "L0 orchestrator",
            "status": "orchestration",
            "phase": "orchestration",
        }
    )
    assign_target = next(
        (r.node_id for r in recs if r.node_id.endswith("_agent")),
        recs[0].node_id,
    )
    prefix.append(
        {
            "t": -2,
            "kind": "assign_task",
            "node_id": "task_router",
            "detail": f"route → {assign_target}",
            "status": "assigned",
            "phase": "assign",
        }
    )
    prefix.append(
        {
            "t": -1,
            "kind": "layer_enter",
            "node_id": assign_target,
            "detail": "L1 specialist agent",
            "status": "in_agent",
            "phase": "in_agent",
        }
    )
    return prefix


def simulate_report(
    traces: list[Trace],
    *,
    n_min: int = N_MIN_DEFAULT,
    opt_in_l1: bool = False,
) -> dict[str, Any]:
    """Recommend + design ranking + event stream for Studio."""
    recs = recommend_traces(traces, n_min=n_min)
    design = simulate_design(traces, n_min=n_min)
    events: list[dict[str, Any]] = _cinematic_prefix_events(recs, traces)
    for i, rec in enumerate(recs):
        what = simulate_what_if(traces, rec.node_id, n_min=n_min, opt_in_l1=opt_in_l1)
        for ev in what.events:
            payload = asdict(ev)
            payload["t"] = int(payload["t"]) + i * 10
            if i == 0 and payload.get("kind") == "load":
                payload["phase"] = "in_agent"
            events.append(payload)
    report = recommendations_to_dict(recs)
    report["simulation"] = {
        "disclaimer": DISCLAIMER,
        "opt_in_l1": bool(opt_in_l1),
        "l1_executed": False,
        "design": [asdict(c) for c in design],
    }
    report["simulation_events"] = events
    return report


def what_if_to_dict(result: WhatIfResult) -> dict[str, Any]:
    return asdict(result)
