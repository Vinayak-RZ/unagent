import {
  canPlay,
  canStepBack,
  canStepForward,
  playbackLabel,
} from "../state/playback";
import type { SimulationEvent } from "../types/report";

interface PlaybackStripProps {
  events: SimulationEvent[];
  index: number;
  playing: boolean;
  onPlay: () => void;
  onPause: () => void;
  onStep: (direction: 1 | -1) => void;
  onReset: () => void;
}

export default function PlaybackStrip({
  events,
  index,
  playing,
  onPlay,
  onPause,
  onStep,
  onReset,
}: PlaybackStripProps) {
  const label = playbackLabel(events, index);
  const progress =
    events.length && index >= 0
      ? `${index + 1} / ${events.length}`
      : events.length
        ? `0 / ${events.length}`
        : "";

  return (
    <div className="playback-strip" role="region" aria-label="Simulation playback">
      <button
        type="button"
        className="btn btn-ghost"
        onClick={() => onStep(-1)}
        disabled={!canStepBack(events, index)}
        aria-label="Previous step"
      >
        ← Step
      </button>
      {playing ? (
        <button type="button" className="btn btn-accent" onClick={onPause} aria-label="Pause">
          Pause
        </button>
      ) : (
        <button
          type="button"
          className="btn btn-accent"
          onClick={onPlay}
          disabled={!canPlay(events, index) && index >= events.length - 1}
          aria-label="Play"
        >
          ▶ Play
        </button>
      )}
      <button
        type="button"
        className="btn btn-ghost"
        onClick={() => onStep(1)}
        disabled={!canStepForward(events, index)}
        aria-label="Next step"
      >
        Step →
      </button>
      <button type="button" className="btn btn-ghost" onClick={onReset} disabled={!events.length}>
        Reset
      </button>
      <span className="playback-label" title={label}>
        {label}
      </span>
      {progress ? <span className="playback-progress">{progress}</span> : null}
    </div>
  );
}
