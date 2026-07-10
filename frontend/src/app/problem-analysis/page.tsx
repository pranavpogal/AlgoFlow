"use client";

import type { FormEvent } from "react";
import { useState } from "react";
import { PageShell } from "../../components/PageShell";
import { apiPost } from "../../lib/api";

export default function ProblemAnalysis() {
  const [result, setResult] = useState<object | null>(null);
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
      setResult(await apiPost("/problems/analyze", payload));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to analyze the problem.");
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
        {error && <div className="result">Error: {error}. Make sure the backend is running on http://localhost:8000.</div>}
        {result && <pre className="result">{JSON.stringify(result, null, 2)}</pre>}
      </section>
    </PageShell>
  );
}
