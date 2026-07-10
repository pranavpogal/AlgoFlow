"use client";

import type { FormEvent } from "react";
import { useState } from "react";
import { PageShell } from "../../components/PageShell";
import { apiPost } from "../../lib/api";

export default function CodeReview() {
  const [result, setResult] = useState<object | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    const formData = new FormData(event.currentTarget);
    try {
      setResult(await apiPost("/code-review", {
        user_id: "demo-user",
        title: String(formData.get("title")),
        language: String(formData.get("language")),
        user_intent: String(formData.get("user_intent")),
        code: String(formData.get("code"))
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to review the solution.");
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
        {error && <div className="result">Error: {error}. Make sure the backend is running on http://localhost:8000.</div>}
        {result && <pre className="result">{JSON.stringify(result, null, 2)}</pre>}
      </section>
    </PageShell>
  );
}
