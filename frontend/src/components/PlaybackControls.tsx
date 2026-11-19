import type { PlayMode } from "../types";

const SPEEDS = [0.5, 0.75, 1, 1.25, 1.5, 1.75, 2];

interface PlaybackControlsProps {
  speed: number;
  mode: PlayMode;
  onSpeedChange: (speed: number) => void;
  onModeChange: (mode: PlayMode) => void;
}

/**
 * 播放速度與循環／單次模式控制區。
 */
export default function PlaybackControls({
  speed,
  mode,
  onSpeedChange,
  onModeChange,
}: PlaybackControlsProps) {
  return (
    <div className="playback-controls">
      <label className="speed-label">
        播放速度控制
        <select
          value={speed}
          onChange={(e) => onSpeedChange(Number(e.target.value))}
          aria-label="播放速度"
        >
          {SPEEDS.map((value) => (
            <option key={value} value={value}>
              {value.toFixed(2).replace(/\.?0+$/, "")}×
            </option>
          ))}
        </select>
      </label>

      <div className="mode-buttons">
        <button
          type="button"
          className={mode === "loop" ? "active" : ""}
          onClick={() => onModeChange("loop")}
        >
          循環
        </button>
        <button
          type="button"
          className={mode === "once" ? "active" : ""}
          onClick={() => onModeChange("once")}
        >
          單次
        </button>
      </div>
    </div>
  );
}
