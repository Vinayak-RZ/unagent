import { describe, expect, it } from "vitest";
import {
  activeEventNodeId,
  canPlay,
  canStepBack,
  canStepForward,
  playbackLabel,
  sortedEvents,
} from "./playback";
import type { SimulationEvent } from "../types/report";

const events: SimulationEvent[] = [
  { t: 2, kind: "graph", node_id: "a" },
  { t: 0, kind: "load", node_id: "a" },
  { t: 5, kind: "decide", node_id: "b", detail: "FlipToDet" },
];

describe("playback", () => {
  it("sorts events by t", () => {
    expect(sortedEvents(events).map((e) => e.t)).toEqual([0, 2, 5]);
  });

  it("returns active node for index", () => {
    const sorted = sortedEvents(events);
    expect(activeEventNodeId(sorted, 1)).toBe("a");
    expect(activeEventNodeId(sorted, 2)).toBe("b");
    expect(activeEventNodeId(sorted, -1)).toBeUndefined();
  });

  it("labels steps for the strip", () => {
    const sorted = sortedEvents(events);
    expect(playbackLabel(sorted, -1)).toContain("Ready");
    expect(playbackLabel(sorted, 2)).toContain("decide");
    expect(playbackLabel(sorted, 2)).toContain("b");
  });

  it("gates step and play controls", () => {
    const sorted = sortedEvents(events);
    expect(canStepBack(sorted, 0)).toBe(false);
    expect(canStepForward(sorted, 0)).toBe(true);
    expect(canPlay(sorted, 1)).toBe(true);
    expect(canPlay(sorted, 2)).toBe(false);
  });
});
