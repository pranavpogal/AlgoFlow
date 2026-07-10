"use client";

import type { FormEvent } from "react";
import { useState } from "react";
import { JsonDisclosure } from "../../components/JsonDisclosure";
import { PageShell } from "../../components/PageShell";
import { StatusCallout } from "../../components/StatusCallout";
import { apiErrorMessage, apiPost } from "../../lib/api";

type CodeReviewResponse = {
  correctness: string;
  time_complexity: string;
  space_complexity: string;
  edge_cases: string[];
  optimization_opportunities: string[];
  readability_feedback: string[];
  suspected_mistakes: string[];
  senior_engineer_summary: string;
  unsupported_claims: string[];
};

export default function CodeReview() {
  const [result, setResult] = useState<CodeReviewResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    const formData = new FormData(event.currentTarget);
    try {
      setResult(await apiPost<CodeReviewResponse>("/code-review", {
        user_id: "demo-user",
        title: String(formData.get("title")),
        language: String(formData.get("language")),
        user_intent: String(formData.get("user_intent")),
        code: String(formData.get("code"))
      }));
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <PageShell>
      <section className="page panel">
        <p className="kicker">Code review agent</p>
        <h2>Senior-engineer feedback, not just pass/fail.</h2>
        <form onSubmit={submit} className="form">
          <input className="input" name="title" defaultValue="House Robber" />
          <select className="select" name="language" defaultValue="Python"><option>Python</option><option>Java</option><option>C++</option><option>JavaScript</option><option>Go</option></select>
          <input className="input" name="user_intent" defaultValue="Find the bug but don't rewrite my code" />
          <textarea className="textarea" name="code" defaultValue={"def rob(nums):\n    dp = [0] * len(nums)\n    for i in range(len(nums)):\n        dp[i] = max(dp[i-1], nums[i] + dp[i-2])\n    return dp[-1]"} />
          <button className="btn" disabled={loading}>{loading ? "Reviewing..." : "Review solution"}</button>
        </form>
        {error && <StatusCallout title="Review unavailable" tone="danger">{error}. Make sure the backend is running on http://localhost:8000.</StatusCallout>}
      </section>
      {result && <section className="grid">
        <article className="card">
          <p className="kicker">Correctness</p>
          <h3>{result.correctness}</h3>
          <p>{result.senior_engineer_summary}</p>
        </article>
        <article className="card">
          <p className="kicker">Complexity</p>
          <h3>{result.time_complexity}</h3>
          <p>Space: {result.space_complexity}</p>
        </article>
        <article className="card">
          <p className="kicker">Mistake signals</p>
          {result.suspected_mistakes.length === 0 && <p>No recurring mistake signal was detected.</p>}
          {result.suspected_mistakes.map((item) => <span className="tag red" key={item}>{item}</span>)}
        </article>
      </section>}
      {result && <section className="grid two">
        <article className="card">
          <p className="kicker">Edge cases</p>
          {result.edge_cases.map((item) => <p key={item}>{item}</p>)}
        </article>
        <article className="card">
          <p className="kicker">Optimization</p>
          {result.optimization_opportunities.map((item) => <p key={item}>{item}</p>)}
        </article>
      </section>}
      {result && <section className="page panel" style={{ marginTop: 22 }}>
        <p className="kicker">Evidence boundary</p>
        <h2>Review without executing learner code.</h2>
        {result.unsupported_claims.map((item) => <p key={item}>{item}</p>)}
        <JsonDisclosure title="Structured review response" data={result} />
      </section>}
    </PageShell>
  );
}
