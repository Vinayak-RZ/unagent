import { useEffect, useMemo, useReducer, useRef } from "react";
import Breadcrumbs from "./components/Breadcrumbs";
import GraphCanvas from "./components/GraphCanvas";
import Inspector, { ProposalRail } from "./components/Inspector";
import PlaybackStrip from "./components/PlaybackStrip";
import { EmptyState, ErrorState, LoadingState } from "./components/States";
import {
  PLAYBACK_INTERVAL_MS,
  activeEventNodeId,
  sortedEvents,
} from "./state/playback";
import {
  buildExportProposal,
  currentFrame,
  initialStudioState,
  nodeHasChildren,
  recommendationForNode,
  studioReducer,
  subgraphFrame,
} from "./state/studioReducer";
import type { ProposalAction, StudioReport } from "./types/report";
import "./index.css";

function parseReport(raw: unknown): StudioReport {
  if (!raw || typeof raw !== "object") {
    throw new Error("Report must be a JSON object");
  }
  const data = raw as StudioReport;
  if (!Array.isArray(data.recommendations)) {
    throw new Error("Report must include a recommendations array");
  }
  return data;
}

export default function App() {
  const [state, dispatch] = useReducer(studioReducer, initialStudioState);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const frame = currentFrame(state);
  const events = useMemo(
    () => sortedEvents(state.report?.simulation_events ?? []),
    [state.report?.simulation_events],
  );
  const activeNodeId = activeEventNodeId(events, state.playbackIndex);
  const selectedRec = recommendationForNode(state.report, state.selectedNodeId);

  useEffect(() => {
    if (!state.playbackPlaying) return;
    const id = window.setInterval(
      () => dispatch({ type: "PLAYBACK_TICK" }),
      PLAYBACK_INTERVAL_MS,
    );
    return () => window.clearInterval(id);
  }, [state.playbackPlaying]);

  useEffect(() => {
    const reportUrl = new URLSearchParams(window.location.search).get("report");
    if (!reportUrl) return;
    dispatch({ type: "LOAD_START", fileName: reportUrl });
    void fetch(reportUrl)
      .then(async (res) => {
        if (!res.ok) throw new Error(`Failed to fetch report (${res.status})`);
        return parseReport(await res.json());
      })
      .then((report) => dispatch({ type: "LOAD_SUCCESS", report, fileName: reportUrl }))
      .catch((e: unknown) =>
        dispatch({
          type: "LOAD_ERROR",
          error: e instanceof Error ? e.message : String(e),
          fileName: reportUrl,
        }),
      );
  }, []);

  function openFilePicker() {
    fileInputRef.current?.click();
  }

  function onFile(file: File | null) {
    if (!file) return;
    dispatch({ type: "LOAD_START", fileName: file.name });
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const report = parseReport(JSON.parse(String(reader.result)));
        dispatch({ type: "LOAD_SUCCESS", report, fileName: file.name });
      } catch (e) {
        dispatch({
          type: "LOAD_ERROR",
          error: e instanceof Error ? e.message : "Invalid JSON",
          fileName: file.name,
        });
      }
    };
    reader.readAsText(file);
  }

  function onNodeClick(nodeId: string) {
    dispatch({ type: "SELECT_NODE", nodeId });
    const node = frame?.nodes.find((n) => n.node_id === nodeId);
    if (!node || !nodeHasChildren(node)) return;
    const next = subgraphFrame(node);
    if (next) dispatch({ type: "ENTER_SUBGRAPH", frame: next });
  }

  function exportProposal() {
    if (!state.report) return;
    const payload = buildExportProposal(state.report, state.proposalEdits);
    const blob = new Blob([JSON.stringify(payload, null, 2)], {
      type: "application/json",
    });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "unagent-proposal.json";
    a.click();
    URL.revokeObjectURL(a.href);
  }

  const recActions = useMemo(() => {
    const map = new Map<string, ProposalAction>();
    for (const r of state.report?.recommendations ?? []) {
      map.set(r.node_id, r.action);
    }
    return map;
  }, [state.report?.recommendations]);

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <h1 className="app-title">Unagent Studio</h1>
          <p className="app-tagline">
            Visualize determinism advice · L0 simulation · draft proposals only
          </p>
        </div>
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <input
            ref={fileInputRef}
            type="file"
            accept="application/json,.json"
            style={{ display: "none" }}
            onChange={(e) => onFile(e.target.files?.[0] ?? null)}
          />
          <button type="button" className="btn btn-secondary" onClick={openFilePicker}>
            Load report
          </button>
          <button
            type="button"
            className="btn btn-accent"
            disabled={state.status !== "ready"}
            onClick={exportProposal}
          >
            Export proposal
          </button>
        </div>
      </header>

      <div className="disclaimer-banner" role="note">
        Simulation ≠ production. In-graph edits are proposal drafts — never auto-applied to agent
        source.
      </div>

      <div className="app-main">
        <section className="canvas-panel">
          {state.status === "ready" && frame ? (
            <>
              <Breadcrumbs
                labels={state.breadcrumbs.map((b) => b.label)}
                onNavigate={(index) => dispatch({ type: "POP_TO_BREADCRUMB", index })}
              />
              <div className="graph-wrap">
                <GraphCanvas
                  nodes={frame.nodes}
                  edges={frame.edges}
                  proposalEdits={state.proposalEdits}
                  recommendations={recActions}
                  activeNodeId={activeNodeId}
                  selectedNodeId={state.selectedNodeId}
                  onNodeClick={onNodeClick}
                />
              </div>
            </>
          ) : state.status === "loading" ? (
            <LoadingState fileName={state.fileName} />
          ) : state.status === "error" ? (
            <ErrorState message={state.error ?? "Unknown error"} onRetry={openFilePicker} />
          ) : (
            <EmptyState onLoadClick={openFilePicker} />
          )}
        </section>

        <aside className="rail-panel">
          <Inspector recommendation={selectedRec} selectedNodeId={state.selectedNodeId} />
          <ProposalRail
            selectedNodeId={state.selectedNodeId}
            currentAction={
              state.selectedNodeId
                ? (state.proposalEdits[state.selectedNodeId] ?? selectedRec?.action)
                : undefined
            }
            onSetProposal={(action) => {
              if (!state.selectedNodeId) return;
              dispatch({ type: "SET_PROPOSAL", nodeId: state.selectedNodeId, action });
            }}
            onExport={exportProposal}
            hasEdits={state.status === "ready"}
          />
        </aside>
      </div>

      <PlaybackStrip
        events={events}
        index={state.playbackIndex}
        playing={state.playbackPlaying}
        onPlay={() => dispatch({ type: "PLAYBACK_PLAY" })}
        onPause={() => dispatch({ type: "PLAYBACK_PAUSE" })}
        onStep={(direction) => dispatch({ type: "PLAYBACK_STEP", direction })}
        onReset={() => dispatch({ type: "PLAYBACK_RESET" })}
      />
    </div>
  );
}
