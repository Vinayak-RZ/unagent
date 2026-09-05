"""Plain-language report renderer for non-technical readers."""

from __future__ import annotations

from typing import Any

from superdeterminism.models import Action, Recommendation

_DISCLAIMER = (
    "This is a simulation-based estimate, not a production guarantee. "
    "Confirm with a canary before changing a live agent."
)


def _action_plain(action: str) -> str:
    return {
        Action.FLIP_TO_DET.value: "make this step a reliable function (not a model call)",
        Action.FLIP_TO_NONDET.value: "consider allowing a model here (needs more live evidence)",
        Action.STRENGTHEN_SDB.value: "keep the model, but harden the safety gate around it",
        Action.ABSTAIN.value: "do not change this yet — evidence is incomplete",
    }.get(action, action)


def recommendations_to_narrative(recs: list[Recommendation]) -> str:
    lines = [
        "# Unagent advice (plain language)",
        "",
        _DISCLAIMER,
        "",
    ]
    if not recs:
        lines.extend(["No nodes were found to review.", ""])
        return "\n".join(lines)

    flips = [r for r in recs if r.action is Action.FLIP_TO_DET]
    harden = [r for r in recs if r.action is Action.STRENGTHEN_SDB]
    abstain = [r for r in recs if r.action is Action.ABSTAIN]
    other = [r for r in recs if r not in flips and r not in harden and r not in abstain]

    lines.append("## Bottom line")
    if flips:
        names = ", ".join(r.node_id for r in flips)
        lines.append(
            f"We found {len(flips)} step(s) that look ready to become deterministic tools: {names}."
        )
    elif harden:
        lines.append(
            "We did not certify a tool flip, but we recommend strengthening safety gates on sensitive steps."
        )
    else:
        lines.append(
            "We are not recommending architecture changes yet. More traces or clearer outcomes are needed."
        )
    lines.append("")

    def _section(title: str, items: list[Recommendation]) -> None:
        if not items:
            return
        lines.append(f"## {title}")
        for r in items:
            lines.append(f"### {r.node_id}")
            lines.append(f"- Advice: {_action_plain(r.action.value)}")
            lines.append(f"- Evidence size: {r.n} observations")
            if r.reasons:
                lines.append(f"- Why: {r.reasons[0]}")
            if r.deltas:
                lines.append(f"- Expected benefit: {r.deltas[0]}")
            lines.append("")

    _section("Recommended flips", flips)
    _section("Strengthen gates", harden)
    _section("Holding for more evidence", abstain)
    _section("Other", other)

    lines.extend(
        [
            "## Next step",
            "Export a scaffold, review the proposal in Studio or your editor, then canary — do not auto-apply.",
            "",
        ]
    )
    return "\n".join(lines)


def report_dict_to_narrative(report: dict[str, Any]) -> str:
    """Render a recommendations_to_dict payload without re-running decide."""
    lines = [
        "# Unagent advice (plain language)",
        "",
        str(report.get("disclaimer") or _DISCLAIMER),
        "",
        "## Bottom line",
    ]
    recs = report.get("recommendations") or []
    flips = [r for r in recs if r.get("action") == Action.FLIP_TO_DET.value]
    if flips:
        lines.append(
            "Recommended deterministic flips: "
            + ", ".join(str(r.get("node_id")) for r in flips)
            + "."
        )
    else:
        lines.append("No certified flips in this report.")
    lines.append("")
    for r in recs:
        lines.append(f"### {r.get('node_id')}")
        lines.append(f"- Advice: {_action_plain(str(r.get('action')))}")
        reasons = r.get("reasons") or []
        if reasons:
            lines.append(f"- Why: {reasons[0]}")
        lines.append("")
    if report.get("simulation"):
        lines.extend(
            [
                "## Simulation",
                "A counterfactual simulation accompanied this report. Treat it as design evidence, not production proof.",
                "",
            ]
        )
    return "\n".join(lines)
