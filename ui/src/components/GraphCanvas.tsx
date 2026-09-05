import { useEffect, useState } from "react";
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  type Edge,
  type Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { layoutGraph, type FlowNodeData } from "../lib/graphLayout";
import type { GraphEdgeSpec, GraphNodeSpec, ProposalAction } from "../types/report";
import StudioNode from "./StudioNode";

const nodeTypes = { studio: StudioNode };

type Props = {
  nodes: GraphNodeSpec[];
  edges: GraphEdgeSpec[];
  proposalEdits: Record<string, ProposalAction>;
  recommendations: Map<string, ProposalAction>;
  activeNodeId?: string;
  selectedNodeId?: string;
  onNodeClick: (nodeId: string) => void;
};

export default function GraphCanvas({
  nodes,
  edges,
  proposalEdits,
  recommendations,
  activeNodeId,
  selectedNodeId,
  onNodeClick,
}: Props) {
  const [rfNodes, setRfNodes] = useState<Node<FlowNodeData>[]>([]);
  const [rfEdges, setRfEdges] = useState<Edge[]>([]);

  useEffect(() => {
    let cancelled = false;
    void layoutGraph(nodes, edges, {
      activeNodeId,
      selectedNodeId,
      proposalEdits,
      recommendations,
    }).then((laid) => {
      if (cancelled) return;
      setRfNodes(laid.nodes);
      setRfEdges(laid.edges);
    });
    return () => {
      cancelled = true;
    };
  }, [nodes, edges, proposalEdits, recommendations, activeNodeId, selectedNodeId]);

  return (
    <ReactFlow
      nodes={rfNodes}
      edges={rfEdges}
      nodeTypes={nodeTypes}
      fitView
      nodesDraggable={false}
      onNodeClick={(_, n) => onNodeClick(n.id)}
      proOptions={{ hideAttribution: true }}
    >
      <Background gap={20} color="#dee3e9" />
      <Controls />
      <MiniMap pannable zoomable />
    </ReactFlow>
  );
}
