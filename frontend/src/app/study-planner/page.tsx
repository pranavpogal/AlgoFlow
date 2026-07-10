"use client";

import type { FormEvent } from "react";
import { useState } from "react";
import { PageShell } from "../../components/PageShell";
import { apiPost } from "../../lib/api";

export default function StudyPlanner() {
  const [plan, setPlan] = useState<{ weekly_plan?: Array<Record<string, unknown>> } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    const formData = new FormData(event.currentTarget);
    try {
      setPlan(await apiPost("/study-plan", {
        user_id: "demo-user",
        target_company: String(formData.get("company")),
        days_remaining: Number(formData.get("days")),
        hours_per_week: Number(formData.get("hours"))
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to generate the study plan.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <PageShell>
      <section className="page panel">
        <p className="kicker">Study planner agent</p>
        <h2>A schedule that respects weak spots and real life.</h2>
        <form onSubmit={submit} className="form">
          <input className="input" name="company" defaultValue="Google" />
          <input className="input" name="days" type="number" defaultValue={45} />
          <input className="input" name="hours" type="number" defaultValue={8} />
          <button className="btn" disabled={loading}>{loading ? "Generating..." : "Generate plan"}</button>
        </form>
        {error && <div className="result">Error: {error}. Make sure the backend is running on http://localhost:8000.</div>}
        {plan?.weekly_plan && <div className="timeline" style={{ marginTop: 18 }}>{plan.weekly_plan.map((week) => <div className="timeline-item" key={String(week.week)}><strong>Week {String(week.week)}: {String(week.focus)}</strong><p>{String(week.mentor_goal)}</p></div>)}</div>}
      </section>
    </PageShell>
  );
}
