import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import type { FlowNodeData } from "../lib/graphLayout";

function actionBadge(action?: string) {
  if (!action) return null;
  const cls =
    action === "FlipToDet"
      ? "badge badge-flip"
      : action === "STRENGTHEN_SDB"
        ? "badge badge-strengthen"
        : "badge badge-abstain";
  return <span className={cls}>{action}</span>;
}

function StudioNodeComponent({ data }: NodeProps) {
  const d = data as FlowNodeData;
  const classes = [
    "studio-node",
    d.selected ? "is-selected" : "",
    d.active ? "is-active" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <>
      <Handle type="target" position={Position.Left} />
      <div className={classes}>
        <div className="studio-node-title">{d.label}</div>
        <div className="studio-node-meta">
          {[d.nodeKind, d.detClass, d.surface].filter(Boolean).join(" · ") || "node"}
        </div>
        {d.action ? <div style={{ marginTop: 6 }}>{actionBadge(d.action)}</div> : null}
        {d.hasChildren ? <div className="studio-node-drill">Enter subgraph →</div> : null}
      </div>
      <Handle type="source" position={Position.Right} />
    </>
  );
}

export default memo(StudioNodeComponent);
