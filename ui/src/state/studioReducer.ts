import type {
  BreadcrumbFrame,
  GraphEdgeSpec,
  GraphNodeSpec,
  ProposalAction,
  Recommendation,
  StudioAction,
  StudioReport,
  StudioState,
} from "../types/report";

export const initialStudioState: StudioState = {
  status: "empty",
  breadcrumbs: [],
  proposalEdits: {},
  playbackIndex: -1,
  playbackPlaying: false,
};

export function synthesizeGraph(
  recommendations: Recommendation[],
  graphNodes: GraphNodeSpec[] = [],
  graphEdges: GraphEdgeSpec[] = [],
): { nodes: GraphNodeSpec[]; edges: GraphEdgeSpec[] } {
  const byId = new Map<string, GraphNodeSpec>();
  for (const n of graphNodes) byId.set(n.node_id, n);
  for (const rec of recommendations) {
    if (!byId.has(rec.node_id)) {
      byId.set(rec.node_id, {
        node_id: rec.node_id,
        node_kind: rec.node_kind,
        det_class: rec.det_class,
      });
    }
  }
  return { nodes: [...byId.values()], edges: graphEdges.length ? graphEdges : [] };
}

function rootFrame(report: StudioReport): BreadcrumbFrame {
  const { nodes, edges } = synthesizeGraph(
    report.recommendations,
    report.graph?.nodes ?? [],
    report.graph?.edges ?? [],
  );
  return {
    id: "root",
    label: report.graph_identity ?? report.graph?.identity ?? "Architecture",
    nodes,
    edges,
  };
}

export function mergeProposalEdits(
  report: StudioReport,
  edits: Record<string, ProposalAction>,
): Record<string, ProposalAction> {
  const merged: Record<string, ProposalAction> = {};
  for (const rec of report.recommendations) {
    merged[rec.node_id] = edits[rec.node_id] ?? rec.action;
  }
  for (const [id, action] of Object.entries(edits)) {
    if (!(id in merged)) merged[id] = action;
  }
  return merged;
}

export function buildExportProposal(
  report: StudioReport,
  edits: Record<string, ProposalAction>,
) {
  return {
    disclaimer: "Draft proposal only. Export for review; never auto-applied to agent source.",
    report_version: report.report_version ?? "1.0",
    graph_identity: report.graph_identity ?? report.graph?.identity,
    edits: mergeProposalEdits(report, edits),
    source_recommendations: report.recommendations.map((r) => ({
      node_id: r.node_id,
      action: r.action,
    })),
  };
}

export function nodeHasChildren(node: GraphNodeSpec): boolean {
  return Boolean(
    (node.children && node.children.length > 0) ||
      (node.subgraph?.nodes && node.subgraph.nodes.length > 0),
  );
}

export function subgraphFrame(node: GraphNodeSpec): BreadcrumbFrame | null {
  if (node.subgraph?.nodes?.length) {
    return {
      id: node.node_id,
      label: node.node_id,
      nodes: node.subgraph.nodes,
      edges: node.subgraph.edges ?? [],
    };
  }
  if (node.children?.length) {
    return {
      id: node.node_id,
      label: node.node_id,
      nodes: node.children,
      edges: node.children.slice(0, -1).map((n, i) => ({
        src: n.node_id,
        dst: node.children![i + 1]!.node_id,
        kind: "parent",
      })),
    };
  }
  return null;
}

export function studioReducer(state: StudioState, action: StudioAction): StudioState {
  switch (action.type) {
    case "LOAD_START":
      return { ...initialStudioState, status: "loading", fileName: action.fileName };
    case "LOAD_SUCCESS": {
      const edits: Record<string, ProposalAction> = {};
      for (const rec of action.report.recommendations) edits[rec.node_id] = rec.action;
      if (action.report.ui_proposal?.edits) Object.assign(edits, action.report.ui_proposal.edits);
      return {
        ...initialStudioState,
        status: "ready",
        report: action.report,
        fileName: action.fileName,
        breadcrumbs: [rootFrame(action.report)],
        proposalEdits: edits,
        selectedNodeId: action.report.recommendations[0]?.node_id,
        playbackIndex: action.report.simulation_events?.length ? 0 : -1,
      };
    }
    case "LOAD_ERROR":
      return {
        ...initialStudioState,
        status: "error",
        error: action.error,
        fileName: action.fileName,
      };
    case "RESET":
      return initialStudioState;
    case "SELECT_NODE":
      return { ...state, selectedNodeId: action.nodeId };
    case "ENTER_SUBGRAPH":
      return {
        ...state,
        breadcrumbs: [...state.breadcrumbs, action.frame],
        selectedNodeId: undefined,
      };
    case "POP_BREADCRUMB":
      if (state.breadcrumbs.length <= 1) return state;
      return {
        ...state,
        breadcrumbs: state.breadcrumbs.slice(0, -1),
        selectedNodeId: undefined,
      };
    case "POP_TO_BREADCRUMB":
      if (action.index < 0 || action.index >= state.breadcrumbs.length - 1) return state;
      return {
        ...state,
        breadcrumbs: state.breadcrumbs.slice(0, action.index + 1),
        selectedNodeId: undefined,
      };
    case "SET_PROPOSAL":
      return {
        ...state,
        proposalEdits: { ...state.proposalEdits, [action.nodeId]: action.action },
      };
    case "PLAYBACK_PLAY":
      if (!state.report?.simulation_events?.length) return state;
      return { ...state, playbackPlaying: true };
    case "PLAYBACK_PAUSE":
      return { ...state, playbackPlaying: false };
    case "PLAYBACK_STEP": {
      const events = state.report?.simulation_events ?? [];
      if (!events.length) return state;
      const next = Math.max(
        0,
        Math.min(events.length - 1, state.playbackIndex + action.direction),
      );
      return { ...state, playbackIndex: next, playbackPlaying: false };
    }
    case "PLAYBACK_RESET":
      return { ...state, playbackIndex: -1, playbackPlaying: false };
    case "PLAYBACK_TICK": {
      const events = state.report?.simulation_events ?? [];
      if (!state.playbackPlaying || !events.length) return state;
      const next = state.playbackIndex + 1;
      if (next >= events.length) {
        return { ...state, playbackIndex: events.length - 1, playbackPlaying: false };
      }
      return { ...state, playbackIndex: next };
    }
    default:
      return state;
  }
}

export function currentFrame(state: StudioState): BreadcrumbFrame | undefined {
  return state.breadcrumbs[state.breadcrumbs.length - 1];
}

export function recommendationForNode(
  report: StudioReport | undefined,
  nodeId: string | undefined,
): Recommendation | undefined {
  if (!report || !nodeId) return undefined;
  return report.recommendations.find((r) => r.node_id === nodeId);
}
