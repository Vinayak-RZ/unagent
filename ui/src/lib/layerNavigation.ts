import type { BreadcrumbFrame, StudioReport } from "../types/report";
import type { LayerId } from "../components/LayerLens";
import { subgraphFrame } from "../state/studioReducer";

export function navigateToLayer(
  report: StudioReport,
  layer: LayerId,
): BreadcrumbFrame[] {
  const rootNodes = report.graph?.nodes ?? [];
  const rootEdges = report.graph?.edges ?? [];
  const root: BreadcrumbFrame = {
    id: "root",
    label: report.graph_identity ?? "Architecture",
    nodes: rootNodes,
    edges: rootEdges,
  };

  if (layer === "L0" || !rootNodes.length) {
    return [root];
  }

  const router = rootNodes.find((n) => n.node_id === "task_router") ?? rootNodes[0];
  const l1Frame = router ? subgraphFrame(router) : null;
  if (!l1Frame || layer === "L1") {
    return l1Frame ? [root, l1Frame] : [root];
  }

  const agentWithTools = l1Frame.nodes.find((n) => subgraphFrame(n));
  const l2Frame = agentWithTools ? subgraphFrame(agentWithTools) : null;
  if (!l2Frame) {
    return [root, l1Frame];
  }
  return [
    root,
    { ...l1Frame, label: router?.node_id ?? l1Frame.label },
    { ...l2Frame, label: agentWithTools!.node_id },
  ];
}
