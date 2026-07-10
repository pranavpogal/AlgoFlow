export function JsonDisclosure({ title, data }: { title: string; data: unknown }) {
  return (
    <details className="json-disclosure">
      <summary>{title}</summary>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </details>
  );
}
