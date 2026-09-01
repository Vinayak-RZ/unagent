"""Public domain types. Stdlib only. No framework imports."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

SCHEMA_VERSION = "1.0"
REPORT_VERSION = "1.0"
TAPE_VERSION = "1.0"


class NodeKind(str, Enum):
    DETERMINISTIC_TOOL = "deterministic_tool"
    LLM_REASONER = "llm_reasoner"
    SUBAGENT = "subagent"
    ROUTER = "router"
    RETRIEVER = "retriever"
    WORKFLOW = "workflow"
    UNKNOWN = "unknown"


class DetClass(str, Enum):
    DETERMINISTIC = "deterministic"
    LLM = "llm"
    LLM_SEEDED = "llm_seeded"
    STOCHASTIC_INDEX = "stochastic_index"
    COMPOSITE = "composite"
    EXTERNAL = "external"


class Action(str, Enum):
    FLIP_TO_DET = "FlipToDet"
    FLIP_TO_NONDET = "FlipToNondet"
    STRENGTHEN_SDB = "STRENGTHEN_SDB"
    ABSTAIN = "ABSTAIN"


class CaptureStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    REDACTED = "redacted"


class EdgeKind(str, Enum):
    PARENT = "parent"
    CONTROL = "control"
    HANDOFF = "handoff"
    PARALLEL = "parallel"


class TrustLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNTRUSTED = "untrusted"


class EvidenceTier(str, Enum):
    OBSERVATIONAL = "observational"
    CASSETTE = "cassette"
    INTERVENTIONAL = "interventional"
    PRODUCTION_CONFIRMED = "production_confirmed"


class ReplayStatus(str, Enum):
    NOT_RUN = "not_run"
    PREFIX_VERIFIED = "prefix_verified"
    TAIL_STABLE = "tail_stable"
    DIVERGED = "diverged"
    REFUSED_MUTATING = "refused_mutating"
    RESAMPLE_ONLY = "resample_only"


@dataclass(frozen=True)
class Span:
    name: str
    attributes: dict[str, Any]
    input: Any = None
    output: Any = None
    tokens: int = 0
    latency_ms: float = 0.0
    error: bool = False
    trace_id: str = ""
    span_id: str = ""
    parent_span_id: str = ""
    start_ns: int = 0
    end_ns: int = 0
    producer: str = ""
    input_capture: str = CaptureStatus.ABSENT.value
    output_capture: str = CaptureStatus.ABSENT.value


@dataclass
class Trace:
    spans: list[Span] = field(default_factory=list)
    trace_id: str = ""
    outcome_success: float | None = None
    policy_ok: float | None = None


@dataclass(frozen=True)
class GraphNode:
    node_id: str
    node_kind: NodeKind
    det_class: DetClass
    mixed: bool = False
    side_effects: bool = False
    is_decision: bool = True


@dataclass(frozen=True)
class GraphEdge:
    src: str
    dst: str
    kind: EdgeKind = EdgeKind.PARENT


@dataclass
class ArchitectureGraph:
    version: str = SCHEMA_VERSION
    identity: str = ""
    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)
    completeness: float = 0.0
    trust: TrustLevel = TrustLevel.LOW
    warnings: tuple[str, ...] = ()
    commitment_node_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class Recommendation:
    node_id: str
    node_kind: NodeKind
    det_class: DetClass
    action: Action
    n: int
    p_mode: float
    p_mode_lower: float
    schema_ok: float
    failure_rate: float
    estimator: str
    reasons: tuple[str, ...]
    disclaimer: str = "simulation != production; canary is confirmatory"
    evidence_tier: str = EvidenceTier.OBSERVATIONAL.value
    replay_status: str = ReplayStatus.NOT_RUN.value
    mixed: bool = False
    cost_tokens: float = 0.0
    latency_ms: float = 0.0
    auditability: float = 0.0
    task_success: float | None = None
    policy_ok: float | None = None
    graph_identity: str = ""
    graph_completeness: float = 0.0
    graph_trust: str = TrustLevel.LOW.value
    input_hash: str = ""
    deltas: tuple[str, ...] = ()
    interaction_hypotheses: tuple[str, ...] = ()
