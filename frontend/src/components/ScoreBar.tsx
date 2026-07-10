export function ScoreBar({ label, value, max = 100 }: { label: string; value: number; max?: number }) {
  const percent = Math.max(0, Math.min(100, Math.round((value / max) * 100)));

  return (
    <div className="score-row">
      <div className="score-label">
        <span>{label}</span>
        <strong>{value}/{max}</strong>
      </div>
      <div className="score-track">
        <div className="score-fill" style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}
