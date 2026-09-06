interface EmptyStateProps {
  onLoadClick: () => void;
}

export function EmptyState({ onLoadClick }: EmptyStateProps) {
  return (
    <div className="empty-state">
      <h2>Load an advisor report</h2>
      <p>
        Unagent Studio visualizes ingested production graphs, L0 simulation playback, and draft flip
        proposals. Start with a JSON report from{" "}
        <code>python -m superdeterminism studio-report TRACES.json</code>.
      </p>
      <button type="button" className="btn btn-accent" onClick={onLoadClick}>
        Choose report JSON
      </button>
      <p style={{ marginTop: 24, fontSize: 13 }}>
        Sample: <code>examples/studio_report.json</code> or orchestrator demo{" "}
        <code>?report=/e2e_orchestrator_studio_report.json</code>
      </p>
    </div>
  );
}

export function LoadingState({ fileName }: { fileName?: string }) {
  return (
    <div className="loading-state">
      <div className="loading-spinner" aria-hidden />
      <h2>Loading report</h2>
      <p>{fileName ? `Parsing ${fileName}…` : "Reading JSON…"}</p>
    </div>
  );
}

export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <div className="error-state">
      <h2>Could not load report</h2>
      <p>{message}</p>
      <p>
        Reports must include a <code>recommendations</code> array. Generate one with{" "}
        <code>python -m superdeterminism studio-report examples/advisor_flip_to_det.json</code>.
      </p>
      <button type="button" className="btn btn-secondary" onClick={onRetry}>
        Try another file
      </button>
    </div>
  );
}
