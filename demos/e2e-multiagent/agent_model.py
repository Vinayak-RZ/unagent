"""Load agent-as-model scenario cassettes (lead agent authored the I/O)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SCENARIO_DIR = Path(__file__).resolve().parent / "scenarios"


@dataclass(frozen=True)
class Scenario:
    id: str
    task: str
    route: tuple[str, ...]
    policy: dict[str, Any]
    agents: dict[str, Any] = field(default_factory=dict)
    mix_weight: int = 1

    @property
    def allow(self) -> bool:
        return bool(self.policy.get("allow", True))


def load_scenario(path: Path) -> Scenario:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not raw.get("id") or not raw.get("task"):
        raise ValueError(f"{path} missing id/task")
    if not isinstance(raw.get("route"), list):
        raise ValueError(f"{path} route must be a list")
    if not isinstance(raw.get("policy"), dict):
        raise ValueError(f"{path} policy must be an object")
    return Scenario(
        id=str(raw["id"]),
        task=str(raw["task"]),
        route=tuple(str(x) for x in raw["route"]),
        policy=raw["policy"],
        agents=dict(raw.get("agents") or {}),
        mix_weight=max(1, int(raw.get("mix_weight", 1))),
    )


def load_scenarios(directory: Path | None = None) -> list[Scenario]:
    d = directory or SCENARIO_DIR
    paths = sorted(d.glob("*.json"))
    if not paths:
        raise FileNotFoundError(f"no scenarios in {d}")
    return [load_scenario(p) for p in paths]


def expand_mix(scenarios: list[Scenario], n: int) -> list[Scenario]:
    """Repeat scenarios by mix_weight until n traces. Deterministic order."""
    bag: list[Scenario] = []
    for s in scenarios:
        bag.extend([s] * s.mix_weight)
    if not bag:
        raise ValueError("empty mix")
    out: list[Scenario] = []
    i = 0
    while len(out) < n:
        out.append(bag[i % len(bag)])
        i += 1
    return out


if __name__ == "__main__":
    loaded = load_scenarios()
    assert {s.id for s in loaded} >= {
        "research_query",
        "implement_constant",
        "full_delivery",
        "policy_block",
    }
    mix = expand_mix(loaded, 30)
    assert len(mix) == 30
    print(f"ok {len(loaded)} scenarios, mix30={[s.id for s in mix[:8]]}…")
