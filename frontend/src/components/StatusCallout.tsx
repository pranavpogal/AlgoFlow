export function StatusCallout({
  title,
  children,
  tone = "info",
}: {
  title: string;
  children: React.ReactNode;
  tone?: "info" | "success" | "warning" | "danger";
}) {
  return (
    <div className={`callout ${tone}`}>
      <strong>{title}</strong>
      <div>{children}</div>
    </div>
  );
}
