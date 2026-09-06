import type { SimulationEvent } from "../types/report";

export type PlaybackPhase = "orchestration" | "assign" | "in_agent" | "simulation";

export function eventPhase(ev: SimulationEvent | undefined): PlaybackPhase {
  if (!ev?.phase) {
    if (ev?.kind === "layer_enter" && ev.detail?.includes("L0")) return "orchestration";
    if (ev?.kind === "assign_task") return "assign";
    if (ev?.kind === "layer_enter" && ev.detail?.includes("L1")) return "in_agent";
    return "simulation";
  }
  return ev.phase as PlaybackPhase;
}

export const PHASE_LABELS: Record<PlaybackPhase, string> = {
  orchestration: "Orchestration",
  assign: "Task assignment",
  in_agent: "In-agent simulation",
  simulation: "L0 splice",
};

export function cinematicStatus(events: SimulationEvent[], index: number): string {
  if (index < 0 || !events.length) return "Ready — cinematic walkthrough";
  const ev = events[index];
  if (!ev) return "";
  const phase = PHASE_LABELS[eventPhase(ev)];
  const detail = ev.detail ? ` · ${ev.detail}` : "";
  return `${phase}: ${ev.kind} @ ${ev.node_id}${detail}`;
}
