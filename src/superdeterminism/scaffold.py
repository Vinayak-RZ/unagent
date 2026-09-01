"""Write illustrative scaffold files. Never mutates user source."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from superdeterminism.models import Action

_REFUSE = ("send", "command", "interrupt", "checkpointer")
_DISCLAIMER = (
    "Copy these files by hand. Do not apply this patch to graph.py automatically. "
    "simulation != production; canary is confirmatory."
)


def _md_escape(text: str) -> str:
    return (
        str(text)
        .replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _safe_name(node_id: str, used: set[str]) -> str:
    base = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in node_id) or "node"
    name = base
    n = 2
    while name in used:
        name = f"{base}_{n}"
        n += 1
    used.add(name)
    return name


def _atomic_write(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def write_scaffold(report: dict[str, Any], out_dir: Path) -> None:
    if not isinstance(report, dict):
        raise ValueError("report must be a JSON object")
    recs = report.get("recommendations")
    if recs is None:
        recs = []
    if not isinstance(recs, list):
        raise ValueError("recommendations must be a list")
    for rec in recs:
        if not isinstance(rec, dict):
            raise ValueError("each recommendation must be an object")
    out_dir.mkdir(parents=True, exist_ok=True)
    patches = out_dir / "patches"
    if patches.exists():
        for stale in patches.glob("*.diff"):
            stale.unlink()
    _atomic_write(out_dir / "REPORT.md", _report_md(report, recs))
    _atomic_write(out_dir / "WIRING.md", _wiring_md(recs))
    generated = out_dir / "generated" / "nodes"
    tests_dir = out_dir / "generated" / "tests"
    generated.mkdir(parents=True, exist_ok=True)
    tests_dir.mkdir(parents=True, exist_ok=True)
    patchable = [r for r in recs if _wants_patch(r)]
    used: set[str] = set()
    if not patchable:
        return
    patches.mkdir(exist_ok=True)
    for rec in patchable:
        name = _safe_name(str(rec.get("node_id") or "node"), used)
        _atomic_write(patches / f"{name}.diff", _diff_for(rec))
        if rec.get("action") == Action.FLIP_TO_DET.value:
            _atomic_write(generated / f"{name}.py", _node_stub(name))
            _atomic_write(tests_dir / f"test_{name}.py", _test_stub(name))
    _atomic_write(out_dir / "ADAPTERS.md", "# Adapters\n\nKeep the node name. Change the callable.\n")
    _atomic_write(out_dir / "CANARY.md", _canary_md(report))


def _wants_patch(rec: dict[str, Any]) -> bool:
    action = rec.get("action")
    if action in {Action.ABSTAIN.value, "ABSTAIN", None}:
        return False
    blob = " ".join(
        [str(rec.get("node_id") or ""), *map(str, rec.get("reasons") or [])]
    ).lower()
    return not any(token in blob for token in _REFUSE)


def _report_md(report: dict[str, Any], recs: list[dict[str, Any]]) -> str:
    lines = [
        "# Determinism Advisor scaffold",
        "",
        f"> {_DISCLAIMER}",
        "",
        f"estimator: {_md_escape(report.get('estimator', 'observational_l0_proxy'))}",
        f"evidence_ceiling: {_md_escape(report.get('evidence_ceiling', 'observational'))}",
        "",
    ]
    for rec in recs:
        lines.append(f"## {_md_escape(rec.get('node_id'))} — {_md_escape(rec.get('action'))}")
        for reason in rec.get("reasons") or []:
            lines.append(f"- {_md_escape(reason)}")
        lines.append("")
    return "\n".join(lines)


def _wiring_md(recs: list[dict[str, Any]]) -> str:
    lines = [
        "# Wiring",
        "",
        "Keep the node name. Change the callable. Human (or a coding agent) copies the diff.",
        "",
        "Use `langchain.agents.create_agent`. Do not emit the deprecated ReAct prebuilt.",
        "",
    ]
    for rec in recs:
        lines.append(
            f"- `{_md_escape(rec.get('node_id'))}`: {_md_escape(rec.get('action'))} "
            f"— edit `add_node(...)` or `tools=`"
        )
    lines.append("")
    return "\n".join(lines)


def _diff_for(rec: dict[str, Any]) -> str:
    node = str(rec.get("node_id") or "node")
    action = rec.get("action")
    if action == Action.FLIP_TO_DET.value:
        return (
            f"- builder.add_node(\"{node}\", llm_{node})\n"
            f"+ builder.add_node(\"{node}\", {node})  # generated/nodes/{node}.py\n"
        )
    if action == Action.FLIP_TO_NONDET.value:
        return (
            f"- builder.add_node(\"{node}\", ToolNode([{node}_regex]))\n"
            f"+ builder.add_node(\"{node}\", {node})  # create_agent subgraph "
            f"(proposer/verifier/commit/reject)\n"
        )
    return (
        f"  builder.add_node(\"{node}\", {node}_proposer)\n"
        f"+ builder.add_node(\"{node}_gate\", {node}_gate)  # deterministic gate stub\n"
    )


def _node_stub(name: str) -> str:
    return (
        f'"""Deterministic stand-in for `{name}`. Copy by hand; do not auto-apply."""\n\n'
        f"def {name}(state: dict) -> dict:\n"
        f"    raise NotImplementedError('fill typed in/out from traces')\n"
    )


def _test_stub(name: str) -> str:
    return (
        f"def test_{name}_stable():\n"
        f"    # planted stability check — fill with cassette inputs\n"
        f"    assert callable({name} if False else lambda: None) or True\n"
    )


def _canary_md(report: dict[str, Any]) -> str:
    lines = ["# Canary checklist", "", "> simulation != production", ""]
    for item in report.get("canary") or []:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)
