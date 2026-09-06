import type { Recommendation } from "../types/report";
import { PROPOSAL_OPTIONS, UI_PROPOSAL_DISCLAIMER, type ProposalAction } from "../types/report";

function renderNarrative(md: string) {
  return md.split("\n").map((line, i) => {
    if (line.startsWith("## ")) {
      return <h3 key={i} style={{ marginTop: i === 0 ? 0 : 16 }}>{line.slice(3)}</h3>;
    }
    if (line.startsWith("> ")) {
      return (
        <p key={i} style={{ fontSize: 12, color: "#5d6c7b", fontStyle: "italic" }}>
          {line.slice(2)}
        </p>
      );
    }
    if (/^\d+\.\s\*\*/.test(line)) {
      const text = line.replace(/\*\*([^*]+)\*\*/g, "$1");
      return <p key={i} style={{ margin: "8px 0" }}>{text}</p>;
    }
    if (line.trim()) {
      return <p key={i}>{line}</p>;
    }
    return null;
  });
}

interface InspectorProps {
  recommendation?: Recommendation;
  selectedNodeId?: string;
  narrative?: string;
}

export default function Inspector({ recommendation, selectedNodeId, narrative }: InspectorProps) {
  if (!selectedNodeId) {
    return (
      <section className="panel-section">
        <h2>Inspector</h2>
        {narrative ? (
          <div className="narrative-panel">{renderNarrative(narrative)}</div>
        ) : (
          <p>Select a node on the graph to review evidence, Wilson bounds, and advisor reasons.</p>
        )}
      </section>
    );
  }

  if (!recommendation) {
    return (
      <section className="panel-section">
        <h2>Inspector</h2>
        <p>
          <strong>{selectedNodeId}</strong> is visible in this subgraph but has no recommendation
          row in the loaded report.
        </p>
      </section>
    );
  }

  return (
    <section className="panel-section">
      <h2>{recommendation.node_id}</h2>
      <dl>
        <div className="meta-row">
          <dt>Action</dt>
          <dd>{recommendation.action}</dd>
        </div>
        <div className="meta-row">
          <dt>n</dt>
          <dd>{recommendation.n ?? "—"}</dd>
        </div>
        <div className="meta-row">
          <dt>p_mode (Wilson lo)</dt>
          <dd>
            {recommendation.p_mode?.toFixed(2) ?? "—"} (
            {recommendation.p_mode_lower?.toFixed(2) ?? "—"})
          </dd>
        </div>
        <div className="meta-row">
          <dt>schema_ok</dt>
          <dd>{recommendation.schema_ok?.toFixed(2) ?? "—"}</dd>
        </div>
        <div className="meta-row">
          <dt>Evidence</dt>
          <dd>{recommendation.evidence_tier ?? "—"}</dd>
        </div>
        <div className="meta-row">
          <dt>Replay</dt>
          <dd>{recommendation.replay_status ?? "—"}</dd>
        </div>
      </dl>
      {recommendation.reasons?.length ? (
        <>
          <h2 style={{ marginTop: 16 }}>Reasons</h2>
          <ul style={{ paddingLeft: 18, margin: 0 }}>
            {recommendation.reasons.map((r) => (
              <li key={r}>{r}</li>
            ))}
          </ul>
        </>
      ) : null}
    </section>
  );
}

interface ProposalRailProps {
  selectedNodeId?: string;
  currentAction?: ProposalAction;
  onSetProposal: (action: ProposalAction) => void;
  onExport: () => void;
  hasEdits: boolean;
}

export function ProposalRail({
  selectedNodeId,
  currentAction,
  onSetProposal,
  onExport,
  hasEdits,
}: ProposalRailProps) {
  return (
    <section className="panel-section">
      <h2>Proposal</h2>
      <p style={{ fontSize: 12, color: "#5d6c7b" }}>{UI_PROPOSAL_DISCLAIMER}</p>
      {!selectedNodeId ? (
        <p>Select a node to draft a proposal action.</p>
      ) : (
        <div className="proposal-toggle-group" role="radiogroup" aria-label="Proposal action">
          {PROPOSAL_OPTIONS.map((action) => (
            <label
              key={action}
              className={`proposal-option ${currentAction === action ? "is-selected" : ""}`}
            >
              <input
                type="radio"
                name={`proposal-${selectedNodeId}`}
                checked={currentAction === action}
                onChange={() => onSetProposal(action)}
              />
              <span>{action}</span>
            </label>
          ))}
        </div>
      )}
      <div style={{ marginTop: 16 }}>
        <button type="button" className="btn btn-accent" onClick={onExport} disabled={!hasEdits}>
          Export proposal JSON
        </button>
      </div>
    </section>
  );
}
