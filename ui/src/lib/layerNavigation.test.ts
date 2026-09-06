import { describe, expect, it } from "vitest";
import { navigateToLayer } from "./layerNavigation";
import type { StudioReport } from "../types/report";

const sampleReport: StudioReport = {
  recommendations: [],
  graph: {
    nodes: [
      {
        node_id: "task_router",
        subgraph: {
          nodes: [
            { node_id: "research_agent", subgraph: { nodes: [{ node_id: "web_search" }] } },
            { node_id: "code_agent" },
          ],
        },
      },
      { node_id: "supervisor_gate" },
    ],
    edges: [],
  },
};

describe("navigateToLayer", () => {
  it("returns root only for L0", () => {
    const frames = navigateToLayer(sampleReport, "L0");
    expect(frames).toHaveLength(1);
    expect(frames[0].nodes).toHaveLength(2);
  });

  it("enters task_router subgraph for L1", () => {
    const frames = navigateToLayer(sampleReport, "L1");
    expect(frames).toHaveLength(2);
    expect(frames[1].nodes.map((n) => n.node_id)).toContain("research_agent");
  });

  it("drills to L2 tools frame", () => {
    const frames = navigateToLayer(sampleReport, "L2");
    expect(frames.length).toBeGreaterThanOrEqual(3);
    expect(frames[2].nodes[0].node_id).toBe("web_search");
  });
});
