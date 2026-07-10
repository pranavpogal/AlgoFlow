export function MetricCard({ label, value, note }: { label: string; value: string; note: string }) {
  return (
    <article className="card">
      <p className="kicker">{label}</p>
      <div className="metric">{value}</div>
      <p>{note}</p>
    </article>
  );
}
