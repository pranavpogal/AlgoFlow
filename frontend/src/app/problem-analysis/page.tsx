"use client";

import type { FormEvent } from "react";
import { useState } from "react";
import { JsonDisclosure } from "../../components/JsonDisclosure";
import { PageShell } from "../../components/PageShell";
import { StatusCallout } from "../../components/StatusCallout";
import { apiErrorMessage, apiPost } from "../../lib/api";

type TopicAnalysis = {
  problem: string;
  difficulty: string;
  pattern: string;
  sub_patterns: string[];
  prerequisites: string[];
  reasoning: string;
  confidence?: number;
  provenance?: string[];
};

export default function ProblemAnalysis() {
  const [result, setResult] = useState<TopicAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    const formData = new FormData(event.currentTarget);
    const payload = {
      user_id: "demo-user",
      problem_number: String(formData.get("number") ?? "198"),
      title: String(formData.get("title") ?? "House Robber"),
      url: String(formData.get("url") ?? ""),
      description: String(formData.get("description") ?? "")
    };
    try {
      setResult(await apiPost<TopicAnalysis>("/problems/analyze", payload));
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <PageShell>
      <section className="page panel">
        <p className="kicker">Topic detection agent</p>
        <h2>Find the pattern hiding underneath the wording.</h2>
        <form onSubmit={submit} className="form">
          <input className="input" name="number" placeholder="Problem number" defaultValue="198" />
          <input className="input" name="title" placeholder="Problem title" defaultValue="House Robber" />
          <input className="input" name="url" placeholder="Problem URL" />
          <textarea className="textarea" name="description" placeholder="Paste the problem description" defaultValue="You are a professional robber planning to rob houses. Find the maximum amount without robbing adjacent houses." />
          <button className="btn" disabled={loading}>{loading ? "Analyzing..." : "Analyze problem"}</button>
        </form>
        {error && <StatusCallout title="Analysis unavailable" tone="danger">{error}. Make sure the backend is running on http://localhost:8000.</StatusCallout>}
      </section>
      {result && <section className="grid">
        <article className="card">
          <p className="kicker">Primary pattern</p>
          <h3>{result.pattern}</h3>
          <p>{result.problem} · {result.difficulty} · confidence {Math.round((result.confidence ?? 0) * 100)}%</p>
        </article>
        <article className="card">
          <p className="kicker">Sub-patterns</p>
          {result.sub_patterns.map((item) => <span className="tag blue" key={item}>{item}</span>)}
        </article>
        <article className="card">
          <p className="kicker">Prerequisites</p>
          {result.prerequisites.map((item) => <span className="tag green" key={item}>{item}</span>)}
        </article>
      </section>}
      {result && <section className="page panel" style={{ marginTop: 22 }}>
        <p className="kicker">Reasoning</p>
        <h2>Why AlgoFlow classified it this way.</h2>
        <p>{result.reasoning}</p>
        <JsonDisclosure title="Structured response" data={result} />
      </section>}
    </PageShell>
  );
}
