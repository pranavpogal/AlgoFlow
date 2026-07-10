import { Nav } from "./Nav";

export function PageShell({ children }: { children: React.ReactNode }) {
  return (
    <main className="shell">
      <Nav />
      {children}
    </main>
  );
}
