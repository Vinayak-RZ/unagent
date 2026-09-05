import type { SimulationEvent } from "../types/report";

export const PLAYBACK_INTERVAL_MS = 600;

export function sortedEvents(events: SimulationEvent[]): SimulationEvent[] {
  return [...events].sort((a, b) => a.t - b.t);
}

export function activeEventNodeId(
  events: SimulationEvent[],
  index: number,
): string | undefined {
  if (index < 0 || index >= events.length) return undefined;
  return events[index]?.node_id;
}

export function playbackLabel(events: SimulationEvent[], index: number): string {
  if (!events.length) return "No simulation events";
  if (index < 0) return "Ready — press play to walk the L0 splice";
  const ev = events[index];
  if (!ev) return "";
  return `${ev.kind}${ev.detail ? `: ${ev.detail}` : ""} @ ${ev.node_id}`;
}

export function canStepForward(events: SimulationEvent[], index: number): boolean {
  return events.length > 0 && index < events.length - 1;
}

export function canStepBack(events: SimulationEvent[], index: number): boolean {
  return events.length > 0 && index > 0;
}

export function canPlay(events: SimulationEvent[], index: number): boolean {
  return events.length > 0 && index < events.length - 1;
}
