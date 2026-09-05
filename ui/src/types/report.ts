export type ProposalAction = "FlipToDet" | "STRENGTHEN_SDB" | "ABSTAIN" | "FlipToNondet";

export interface GraphNodeSpec {
  node_id: string;
  node_kind?: string;
  det_class?: string;
  mixed?: boolean;
  side_effects?: boolean;
  is_decision?: boolean;
  children?: GraphNodeSpec[];
  subgraph?: StudioSubgraph;
}

export interface GraphEdgeSpec {
  src: string;
  dst: string;
  kind?: string;
}

export interface StudioSubgraph {
  nodes: GraphNodeSpec[];
  edges?: GraphEdgeSpec[];
}

export interface Recommendation {
  node_id: string;
  node_kind?: string;
  det_class?: string;
  action: ProposalAction;
  n?: number;
  p_mode?: number;
  p_mode_lower?: number;
  schema_ok?: number;
  failure_rate?: number;
  evidence_tier?: string;
  replay_status?: string;
  reasons?: string[];
  deltas?: string[];
  mixed?: boolean;
}

export interface SimulationEvent {
  t: number;
  kind: string;
  node_id: string;
  detail?: string;
  status?: string;
}

export interface StudioReport {
  disclaimer?: string;
  report_version?: string;
  graph_identity?: string;
  graph_completeness?: number;
  graph_trust?: string;
  recommendations: Recommendation[];
  simulation_events?: SimulationEvent[];
  graph?: {
    nodes?: GraphNodeSpec[];
    edges?: GraphEdgeSpec[];
    identity?: string;
    completeness?: number;
    trust?: string;
  };
  ui_proposal?: UiProposal;
  narrative?: string;
}

export interface UiProposal {
  disclaimer: string;
  edits: Record<string, ProposalAction>;
}

export interface BreadcrumbFrame {
  id: string;
  label: string;
  nodes: GraphNodeSpec[];
  edges: GraphEdgeSpec[];
}

export interface StudioState {
  status: "empty" | "loading" | "ready" | "error";
  error?: string;
  report?: StudioReport;
  fileName?: string;
  breadcrumbs: BreadcrumbFrame[];
  selectedNodeId?: string;
  proposalEdits: Record<string, ProposalAction>;
  playbackIndex: number;
  playbackPlaying: boolean;
}

export type StudioAction =
  | { type: "LOAD_START"; fileName: string }
  | { type: "LOAD_SUCCESS"; report: StudioReport; fileName: string }
  | { type: "LOAD_ERROR"; error: string; fileName?: string }
  | { type: "RESET" }
  | { type: "SELECT_NODE"; nodeId: string | undefined }
  | { type: "ENTER_SUBGRAPH"; frame: BreadcrumbFrame }
  | { type: "POP_BREADCRUMB" }
  | { type: "POP_TO_BREADCRUMB"; index: number }
  | { type: "SET_PROPOSAL"; nodeId: string; action: ProposalAction }
  | { type: "PLAYBACK_PLAY" }
  | { type: "PLAYBACK_PAUSE" }
  | { type: "PLAYBACK_STEP"; direction: 1 | -1 }
  | { type: "PLAYBACK_RESET" }
  | { type: "PLAYBACK_TICK" };

export const PROPOSAL_OPTIONS: ProposalAction[] = [
  "FlipToDet",
  "STRENGTHEN_SDB",
  "ABSTAIN",
];

export const UI_PROPOSAL_DISCLAIMER =
  "Draft proposal only. Export for review; never auto-applied to agent source.";
