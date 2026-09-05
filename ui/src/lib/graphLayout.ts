import ELK from "elkjs/lib/elk.bundled.js";
import type { Edge, Node } from "@xyflow/react";
import type { GraphEdgeSpec, GraphNodeSpec, ProposalAction } from "../types/report";

const elk = new ELK();

export interface FlowNodeData extends Record<string, unknown> {
  label: string;
  nodeKind?: string;
  detClass?: string;
  action?: ProposalAction;
  hasChildren: boolean;
  active: boolean;
  selected: boolean;
}

const NODE_W = 180;
const NODE_H = 56;

export async function layoutGraph(
  nodes: GraphNodeSpec[],
  edges: GraphEdgeSpec[],
  opts: {
    activeNodeId?: string;
    selectedNodeId?: string;
    proposalEdits: Record<string, ProposalAction>;
    recommendations: Map<string, ProposalAction>;
  },
): Promise<{ nodes: Node<FlowNodeData>[]; edges: Edge[] }> {
  if (!nodes.length) return { nodes: [], edges: [] };

  const elkGraph = {
    id: "root",
    layoutOptions: {
      "elk.algorithm": "layered",
      "elk.direction": "RIGHT",
      "elk.spacing.nodeNode": "48",
      "elk.layered.spacing.nodeNodeBetweenLayers": "64",
    },
    children: nodes.map((n) => ({ id: n.node_id, width: NODE_W, height: NODE_H })),
    edges: edges.map((e, i) => ({
      id: `e-${i}`,
      sources: [e.src],
      targets: [e.dst],
    })),
  };

  let layoutChildren: Array<{ id: string; x?: number; y?: number }> =
    elkGraph.children;
  try {
    const laidOut = await elk.layout(elkGraph);
    layoutChildren = (laidOut.children ?? []).map((c) => ({
      id: c.id,
      x: c.x,
      y: c.y,
    }));
  } catch {
    // ponytail: grid fallback if ELK fails
  }

  const flowNodes: Node<FlowNodeData>[] = nodes.map((n, i) => {
    const laid = layoutChildren.find((c) => c.id === n.node_id);
    const hasChildren = Boolean(
      (n.children && n.children.length > 0) ||
        (n.subgraph?.nodes && n.subgraph.nodes.length > 0),
    );
    return {
      id: n.node_id,
      type: "studio",
      position: {
        x: laid?.x ?? (i % 4) * (NODE_W + 48),
        y: laid?.y ?? Math.floor(i / 4) * (NODE_H + 48),
      },
      data: {
        label: n.node_id,
        nodeKind: n.node_kind,
        detClass: n.det_class,
        action: opts.proposalEdits[n.node_id] ?? opts.recommendations.get(n.node_id),
        hasChildren,
        active: n.node_id === opts.activeNodeId,
        selected: n.node_id === opts.selectedNodeId,
      },
    };
  });

  const flowEdges: Edge[] = edges.map((e, i) => ({
    id: `edge-${i}`,
    source: e.src,
    target: e.dst,
    type: "smoothstep",
    animated: e.kind === "control" || e.kind === "handoff",
  }));

  return { nodes: flowNodes, edges: flowEdges };
}
