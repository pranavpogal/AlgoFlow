import Link from "next/link";
import { MetricCard } from "../components/MetricCard";
import { PageShell } from "../components/PageShell";

export default function Home() {
  return (
    <PageShell>
      <section className="hero">
        <div className="panel">
          <p className="kicker">Multi-agent interview mentor</p>
          <h1>Practice patterns, not memorized answers.</h1>
          <p>
            AlgoFlow combines governed Google ADK routing, deterministic mentoring workflows,
            memory retrieval, and evidence-backed analytics to coach interview preparation without
            collapsing into a solution generator.
          </p>
          <div className="actions">
            <Link className="btn" href="/problem-analysis">Analyze a problem</Link>
            <Link className="btn secondary" href="/mock-interview">Start a mock interview</Link>
            <Link className="btn secondary" href="/trajectory">Inspect trajectory</Link>
          </div>
        </div>
        <div className="panel">
          <p className="kicker">Governed runtime</p>
          <h2>Agents where justified. Workflows where safer.</h2>
          <p>
            The coordinator captures routing trajectory, policy-gated tool calls, and deterministic fallbacks.
            Skills handle hinting, code review, problem intelligence, transfer, analytics, and mock interviews
            with structured outputs.
          </p>
          <span className="tag">ADK Route</span><span className="tag">Tool Gateway</span><span className="tag">Semantic Policy</span>
          <span className="tag">RAG Memory</span><span className="tag">Skill Workflows</span><span className="tag">Eval Gates</span>
        </div>
      </section>
      <section className="grid">
        <MetricCard label="Runtime" value="ADK" note="Narrow coordinator slice with trajectory capture and deterministic fallback." />
        <MetricCard label="Evaluation" value="66/66" note="Accepted deterministic baseline stayed green in the latest phase." />
        <MetricCard label="Memory" value="RAG" note="Same-user retrieval and structured learner evidence personalize responses." />
      </section>
    </PageShell>
  );
}
