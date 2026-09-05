interface BreadcrumbsProps {
  labels: string[];
  onNavigate: (index: number) => void;
}

export default function Breadcrumbs({ labels, onNavigate }: BreadcrumbsProps) {
  if (labels.length <= 1) return null;
  return (
    <nav className="breadcrumbs" aria-label="Graph hierarchy">
      {labels.map((label, i) => (
        <span key={`${label}-${i}`} style={{ display: "inline-flex", alignItems: "center" }}>
          {i > 0 ? (
            <span className="breadcrumb-sep" aria-hidden>
              {" "}
              ›{" "}
            </span>
          ) : null}
          <button
            type="button"
            className={`breadcrumb-item ${i === labels.length - 1 ? "is-current" : ""}`}
            onClick={() => onNavigate(i)}
            disabled={i === labels.length - 1}
          >
            {label}
          </button>
        </span>
      ))}
    </nav>
  );
}
