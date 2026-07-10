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
            AlgoFlow uses specialized Google ADK agents for topic detection, progressive hints,
            code review, mistake tracking, mock interviews, analytics, and long-term learning memory.
          </p>
          <div className="actions">
            <Link className="btn" href="/problem-analysis">Analyze a problem</Link>
            <Link className="btn secondary" href="/mock-interview">Start a mock interview</Link>
          </div>
        </div>
        <div className="panel">
          <p className="kicker">Coordinator agent</p>
          <h2>One mentor brain, ten specialist agents.</h2>
          <p>
            The coordinator delegates intent to narrow agents, then memory and retrieval personalize the next move.
            The result feels less like a solver and more like a patient senior engineer sitting beside you.
          </p>
          <span className="tag">Topic Agent</span><span className="tag">Hint Agent</span><span className="tag">Review Agent</span>
          <span className="tag">Planner Agent</span><span className="tag">Memory Agent</span><span className="tag">Mock Interview Agent</span>
        </div>
      </section>
      <section className="grid">
        <MetricCard label="Readiness" value="72" note="Composite score from mastery, consistency, and mistakes." />
        <MetricCard label="Agents" value="10" note="Specialized workers orchestrated by a root coordinator." />
        <MetricCard label="Memory" value="RAG" note="Structured profile plus vector retrieval for personalization." />
      </section>
    </PageShell>
  );
}
