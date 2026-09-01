"""Facade: ingest → classify → graph → evidence → L0 replay → fail-closed recommend."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable
from typing import Any

from superdeterminism.classify import classify_span
from superdeterminism.evidence import attach_replay, collect_node_stats, wilson_lower
from superdeterminism.graph import reconstruct
from superdeterminism.ingest import IngestError, load_traces, load_traces_dir, load_traces_path
from superdeterminism.models import (
    Action,
    DetClass,
    EvidenceTier,
    NodeKind,
    Recommendation,
    ReplayStatus,
    SCHEMA_VERSION,
    TAPE_VERSION,
    Trace,
    TrustLevel,
)

N_MIN_DEFAULT = 30
SCHEMA_OK_MIN = 0.80
P_MODE_MIN = 0.70
HARD_OVERRIDE = re.compile(
    r"(refund|commit|payment|payout|auth|oauth|pii|password|secret|spend|charge)",
    re.I,
)
DISCLAIMER = "simulation != production; canary is confirmatory"


def _is_llm(kind: NodeKind, det: DetClass) -> bool:
    return det in {DetClass.LLM, DetClass.LLM_SEEDED} or kind in {
        NodeKind.LLM_REASONER,
        NodeKind.SUBAGENT,
    }


def _is_det(kind: NodeKind, det: DetClass) -> bool:
    return det == DetClass.DETERMINISTIC or kind == NodeKind.DETERMINISTIC_TOOL


def _metric_improves(kind: NodeKind, det: DetClass, cost_tokens: float, latency_ms: float) -> tuple[bool, list[str]]:
    deltas: list[str] = []
    if _is_llm(kind, det):
        deltas.append("auditability: llm logs -> deterministic function")
        if cost_tokens > 0:
            deltas.append(f"cost_tokens estimated -{cost_tokens:.1f} per call")
        if latency_ms > 0:
            deltas.append(f"latency_ms estimated -{latency_ms:.1f} model wait")
        return True, deltas
    return False, deltas


def _decide(
    *,
    kind: NodeKind,
    det: DetClass,
    n: int,
    n_min: int,
    p_mode: float,
    p_lower: float,
    schema_ok: float,
    failure_rate: float,
    sensitive: bool,
    mixed: bool,
    unknown: bool,
    tier: EvidenceTier,
    replay: ReplayStatus,
    cost_tokens: float,
    latency_ms: float,
    completeness: float,
    trust: TrustLevel,
    mixed_workload: bool,
) -> tuple[Action, list[str], tuple[str, ...]]:
    if unknown or mixed or kind is NodeKind.UNKNOWN:
        return Action.ABSTAIN, ["unknown or mixed node kinds; refuse to guess"], ()
    if sensitive and _is_llm(kind, det):
        return Action.STRENGTHEN_SDB, [
            "hard override: commit/spend/PII/auth must stay a deterministic gate",
            "keep proposer; do not FlipToNondet a commit path",
        ], ()
    if sensitive and _is_det(kind, det) and failure_rate > 0:
        return Action.STRENGTHEN_SDB, [
            "hard override: failures on a sensitive DET node harden the gate, not the model",
        ], ()
    if n < n_min:
        return Action.ABSTAIN, [f"n={n} < n_min={n_min}"], ()
    if _is_llm(kind, det) and failure_rate > 0:
        return Action.ABSTAIN, [
            f"failure_rate={failure_rate:.2f} > 0; FlipToDet requires failure not worsen",
        ], ()
    if _is_llm(kind, det) and schema_ok >= SCHEMA_OK_MIN and p_mode >= P_MODE_MIN and p_lower >= P_MODE_MIN:
        if tier is not EvidenceTier.CASSETTE or replay is not ReplayStatus.TAIL_STABLE:
            return Action.ABSTAIN, [
                f"observational/cassette incomplete (tier={tier.value}, replay={replay.value}); "
                "FlipToDet requires L0 tail-stable splice",
            ], ()
        ok, deltas = _metric_improves(kind, det, cost_tokens, latency_ms)
        if not ok:
            return Action.ABSTAIN, ["no cost/latency/variance/auditability improvement"], ()
        if completeness < 0.5:
            return Action.ABSTAIN, ["graph completeness < 0.5"], ()
        if trust in {TrustLevel.LOW, TrustLevel.UNTRUSTED}:
            return Action.ABSTAIN, [f"graph trust={trust.value}; FlipToDet needs medium+"], ()
        if mixed_workload:
            return Action.ABSTAIN, [
                "mixed model/prompt workload cells; abstain until stratified (RouteGuard)",
            ], ()
        reasons = [
            f"schema_ok={schema_ok:.2f} >= {SCHEMA_OK_MIN}",
            f"p_mode={p_mode:.2f} (wilson_lower={p_lower:.2f}) >= {P_MODE_MIN}",
            f"L0 splice {replay.value}",
        ]
        return Action.FLIP_TO_DET, reasons, tuple(deltas)
    if _is_det(kind, det) and failure_rate >= 0.30 and not sensitive:
        return Action.ABSTAIN, [
            f"DET node failure_rate={failure_rate:.2f} >= 0.30; "
            "FlipToNondet needs L1 evidence a policy swap recovers the tail",
        ], ()
    if _is_llm(kind, det) and schema_ok >= SCHEMA_OK_MIN and p_mode >= P_MODE_MIN and p_lower < P_MODE_MIN:
        return Action.ABSTAIN, [
            f"p_mode point {p_mode:.2f} meets threshold but wilson_lower {p_lower:.2f} does not",
        ], ()
    return Action.ABSTAIN, ["no rule fired with a CI that excludes the threshold"], ()


def recommend_traces(
    traces: list[Trace],
    *,
    n_min: int = N_MIN_DEFAULT,
) -> list[Recommendation]:
    graph = reconstruct(traces)
    stats = attach_replay(traces, collect_node_stats(traces))
    recs: list[Recommendation] = []
    payload_hash = _input_hash(traces)
    for node_id, row in sorted(stats.items()):
        action, reasons, deltas = _decide(
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
        estimator = (
            "l0_tape_splice"
            if row["tier"] is EvidenceTier.CASSETTE
            else "observational_l0_proxy"
        )
        recs.append(
            Recommendation(
                node_id=node_id,
                node_kind=row["kind"],
                det_class=row["det"],
                action=action,
                n=row["n"],
                p_mode=round(row["p_mode"], 4),
                p_mode_lower=round(row["p_mode_lower"], 4),
                schema_ok=round(row["schema_ok"], 4),
                failure_rate=round(row["failure_rate"], 4),
                estimator=estimator,
                reasons=tuple(reasons),
                evidence_tier=row["tier"].value,
                replay_status=row["replay"].value,
                mixed=row["mixed"],
                cost_tokens=round(row["cost_tokens"], 4),
                latency_ms=round(row["latency_ms"], 4),
                auditability=0.0 if _is_llm(row["kind"], row["det"]) else 1.0,
                task_success=row["task_success"],
                policy_ok=row.get("policy_ok"),
                graph_identity=graph.identity,
                graph_completeness=graph.completeness,
                graph_trust=graph.trust.value,
                input_hash=payload_hash,
                deltas=deltas,
            )
        )
    recs = _attach_interactions(recs, graph)
    return recs


def _attach_interactions(recs: list[Recommendation], graph) -> list[Recommendation]:
    """Bounded pair hypotheses: adjacent failing nodes may be AND-repairs (GCJR-shaped)."""
    fail_ids = {r.node_id for r in recs if r.failure_rate >= 0.30}
    if len(fail_ids) < 2:
        return recs
    pairs: list[str] = []
    for edge in graph.edges:
        if edge.src in fail_ids and edge.dst in fail_ids:
            pairs.append(f"AND? {edge.src}+{edge.dst}")
            if len(pairs) >= 8:
                break
    if not pairs:
        return recs
    out = []
    hypo = tuple(pairs)
    for r in recs:
        if r.node_id in fail_ids:
            out.append(
                Recommendation(
                    **{**r.__dict__, "interaction_hypotheses": hypo}
                )
            )
        else:
            out.append(r)
    return out


def _input_hash(traces: list[Trace]) -> str:
    blob = json.dumps(
        [{"id": t.trace_id, "n": len(t.spans)} for t in traces],
        sort_keys=True,
    )
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def inspect_traces(traces: list[Trace]) -> dict[str, Any]:
    graph = reconstruct(traces)
    rows = []
    for trace in traces:
        for span in trace.spans:
            node_id, kind, det = classify_span(span)
            rows.append(
                {
                    "trace_id": span.trace_id or trace.trace_id,
                    "span_id": span.span_id,
                    "node_id": node_id,
                    "node_kind": kind.value,
                    "det_class": det.value,
                    "error": span.error,
                    "producer": span.producer,
                }
            )
    return {
        "advisor.schema_version": SCHEMA_VERSION,
        "graph_identity": graph.identity,
        "completeness": graph.completeness,
        "trust": graph.trust.value,
        "warnings": list(graph.warnings),
        "nodes": [
            {
                "node_id": n.node_id,
                "node_kind": n.node_kind.value,
                "mixed": n.mixed,
                "side_effects": n.side_effects,
                "is_decision": n.is_decision,
            }
            for n in graph.nodes
        ],
        "edges": [{"src": e.src, "dst": e.dst, "kind": e.kind.value} for e in graph.edges],
        "spans": rows,
    }


def recommendations_to_dict(recs: Iterable[Recommendation]) -> dict[str, Any]:
    rec_list = list(recs)
    estimators = {r.estimator for r in rec_list}
    estimator = "l0_tape_splice" if "l0_tape_splice" in estimators else "observational_l0_proxy"
    ceiling = "cassette" if estimator == "l0_tape_splice" else "observational"
    identity = rec_list[0].graph_identity if rec_list else ""
    input_hash = rec_list[0].input_hash if rec_list else ""
    return {
        "disclaimer": DISCLAIMER,
        "report_version": "1.0",
        "advisor.schema_version": SCHEMA_VERSION,
        "estimator": estimator,
        "evidence_ceiling": ceiling,
        "graph_identity": identity,
        "graph_completeness": rec_list[0].graph_completeness if rec_list else 0.0,
        "graph_trust": rec_list[0].graph_trust if rec_list else "",
        "tape_version": TAPE_VERSION,
        "input_hash": input_hash,
        "recommendations": [
            {
                "node_id": r.node_id,
                "node_kind": r.node_kind.value,
                "det_class": r.det_class.value,
                "action": r.action.value,
                "n": r.n,
                "p_mode": r.p_mode,
                "p_mode_lower": r.p_mode_lower,
                "schema_ok": r.schema_ok,
                "failure_rate": r.failure_rate,
                "estimator": r.estimator,
                "reasons": list(r.reasons),
                "disclaimer": r.disclaimer,
                "evidence_tier": r.evidence_tier,
                "replay_status": r.replay_status,
                "mixed": r.mixed,
                "cost_tokens": r.cost_tokens,
                "latency_ms": r.latency_ms,
                "auditability": r.auditability,
                "task_success": r.task_success,
                "policy_ok": r.policy_ok,
                "deltas": list(r.deltas),
                "interaction_hypotheses": list(r.interaction_hypotheses),
            }
            for r in rec_list
        ],
        "canary": [
            "shadow the candidate function on the same traffic",
            "compare outcome vector: failure, cost, latency, variance, policy",
            "promote only if intervals and safety gates pass; else ABSTAIN/demote",
            "simulation != production",
        ],
    }


def recommendations_to_markdown(recs: list[Recommendation]) -> str:
    lines = [
        "# Determinism Advisor report",
        "",
        f"> {DISCLAIMER}",
        "",
        "| node | kind | class | action | n | p_mode | p_mode_lo | schema_ok | fail | tier | replay |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for r in recs:
        nid = r.node_id.replace("|", "\\|")
        lines.append(
            f"| {nid} | {r.node_kind.value} | {r.det_class.value} | "
            f"{r.action.value} | {r.n} | {r.p_mode:.2f} | {r.p_mode_lower:.2f} | "
            f"{r.schema_ok:.2f} | {r.failure_rate:.2f} | {r.evidence_tier} | {r.replay_status} |"
        )
    lines.extend(["", "## Reasons", ""])
    for r in recs:
        lines.append(f"### {r.node_id} — {r.action.value}")
        for reason in r.reasons:
            lines.append(f"- {reason}")
        for delta in r.deltas:
            lines.append(f"- delta: {delta}")
        lines.append("")
    lines.extend(["## Canary", "", "- simulation != production; canary is confirmatory", ""])
    return "\n".join(lines)
