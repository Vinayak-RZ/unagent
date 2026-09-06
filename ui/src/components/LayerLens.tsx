export type LayerId = "L0" | "L1" | "L2";

const LAYERS: { id: LayerId; label: string; hint: string }[] = [
  { id: "L0", label: "Orchestrator", hint: "Supervisor / task router" },
  { id: "L1", label: "Agents", hint: "Specialist subagents" },
  { id: "L2", label: "Tools & MCPs", hint: "Tools, MCPs, skills per agent" },
];

interface LayerLensProps {
  activeLayer: LayerId;
  onSelect: (layer: LayerId) => void;
  disabled?: boolean;
}

export default function LayerLens({ activeLayer, onSelect, disabled }: LayerLensProps) {
  return (
    <div className="layer-lens" role="tablist" aria-label="Architecture layer">
      {LAYERS.map((layer) => (
        <button
          key={layer.id}
          type="button"
          role="tab"
          className={`layer-lens-btn ${activeLayer === layer.id ? "is-active" : ""}`}
          aria-selected={activeLayer === layer.id}
          title={layer.hint}
          disabled={disabled}
          onClick={() => onSelect(layer.id)}
        >
          <span className="layer-lens-id">{layer.id}</span>
          <span className="layer-lens-label">{layer.label}</span>
        </button>
      ))}
    </div>
  );
}
