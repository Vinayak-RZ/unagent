import { describe, expect, it } from "vitest";
import {
  buildExportProposal,
  initialStudioState,
  nodeHasChildren,
  studioReducer,
  subgraphFrame,
  synthesizeGraph,
} from "./studioReducer";
import type { StudioReport } from "../types/report";

const sampleReport: StudioReport = {
  report_version: "1.0",
  graph_identity: "abc123",
  recommendations: [
    { node_id: "classify", action: "FlipToDet", n: 40, p_mode_lower: 0.91 },
    { node_id: "route", action: "ABSTAIN", n: 10 },
  ],
  simulation_events: [
    { t: 0, kind: "load", node_id: "classify" },
    { t: 1, kind: "decide", node_id: "classify", status: "FlipToDet" },
  ],
  graph: {
    nodes: [{ node_id: "classify", node_kind: "llm_reasoner" }],
    edges: [],
  },
};

describe("studioReducer", () => {
  it("loads report into ready state with breadcrumbs", () => {
    const next = studioReducer(initialStudioState, {
      type: "LOAD_SUCCESS",
      report: sampleReport,
      fileName: "test.json",
    });
    expect(next.status).toBe("ready");
    expect(next.breadcrumbs).toHaveLength(1);
    expect(next.proposalEdits.classify).toBe("FlipToDet");
    expect(next.playbackIndex).toBe(0);
  });

  it("synthesizes isolated nodes when edges missing", () => {
    const { nodes, edges } = synthesizeGraph(sampleReport.recommendations, [], []);
    expect(nodes.map((n) => n.node_id).sort()).toEqual(["classify", "route"]);
    expect(edges).toHaveLength(0);
  });

  it("updates proposal edits without mutating prior state", () => {
    const loaded = studioReducer(initialStudioState, {
      type: "LOAD_SUCCESS",
      report: sampleReport,
      fileName: "t.json",
    });
    const edited = studioReducer(loaded, {
      type: "SET_PROPOSAL",
      nodeId: "classify",
      action: "ABSTAIN",
    });
    expect(edited.proposalEdits.classify).toBe("ABSTAIN");
    expect(loaded.proposalEdits.classify).toBe("FlipToDet");
  });

  it("enters subgraph when node has children", () => {
    const node = {
      node_id: "parent",
      children: [{ node_id: "child-a" }, { node_id: "child-b" }],
    };
    expect(nodeHasChildren(node)).toBe(true);
    const frame = subgraphFrame(node);
    expect(frame?.nodes).toHaveLength(2);
    const loaded = studioReducer(initialStudioState, {
      type: "LOAD_SUCCESS",
      report: sampleReport,
      fileName: "t.json",
    });
    const entered = studioReducer(loaded, { type: "ENTER_SUBGRAPH", frame: frame! });
    expect(entered.breadcrumbs).toHaveLength(2);
  });

  it("export payload includes disclaimer and never implies auto-apply", () => {
    const payload = buildExportProposal(sampleReport, { classify: "STRENGTHEN_SDB" });
    expect(payload.disclaimer.toLowerCase()).toContain("never auto-applied");
    expect(payload.edits.classify).toBe("STRENGTHEN_SDB");
    expect(payload.edits.route).toBe("ABSTAIN");
  });
});
