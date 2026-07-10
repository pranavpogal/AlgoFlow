"use client";

import type { FormEvent } from "react";
import { useState } from "react";
import { JsonDisclosure } from "../../components/JsonDisclosure";
import { PageShell } from "../../components/PageShell";
import { StatusCallout } from "../../components/StatusCallout";
import { apiErrorMessage, apiPost } from "../../lib/api";

type StudyPlan = {
  weekly_plan?: Array<{ week?: number; focus?: string; mentor_goal?: string; workload?: string; drills?: string[] }>;
  checkpoints?: string[];
  personalization_notes?: string[];
};

export default function StudyPlanner() {
  const [plan, setPlan] = useState<StudyPlan | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    const formData = new FormData(event.currentTarget);
    try {
      setPlan(await apiPost<StudyPlan>("/study-plan", {
        user_id: "demo-user",
        target_company: String(formData.get("company")),
        days_remaining: Number(formData.get("days")),
        hours_per_week: Number(formData.get("hours"))
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
        <p className="kicker">Study planner agent</p>
        <h2>A schedule that respects weak spots and real life.</h2>
        <form onSubmit={submit} className="form">
          <input className="input" name="company" defaultValue="Google" />
          <input className="input" name="days" type="number" defaultValue={45} />
          <input className="input" name="hours" type="number" defaultValue={8} />
          <button className="btn" disabled={loading}>{loading ? "Generating..." : "Generate plan"}</button>
        </form>
        {error && <StatusCallout title="Planner unavailable" tone="danger">{error}. Make sure the backend is running on http://localhost:8000.</StatusCallout>}
      </section>
      {plan?.weekly_plan && <section className="split">
        <div className="panel">
          <p className="kicker">Weekly path</p>
          <h2>What to practice and why.</h2>
          <div className="timeline" style={{ marginTop: 18 }}>{plan.weekly_plan.map((week) => <div className="timeline-item" key={String(week.week)}><strong>Week {String(week.week)}: {String(week.focus)}</strong><p>{String(week.mentor_goal)}</p>{week.workload && <span className="tag">{week.workload}</span>}</div>)}</div>
        </div>
        <div className="stack">
          <article className="card">
            <p className="kicker">Checkpoints</p>
            {(plan.checkpoints ?? []).map((item) => <p key={item}>{item}</p>)}
          </article>
          <article className="card">
            <p className="kicker">Personalization</p>
            {(plan.personalization_notes ?? []).map((item) => <p key={item}>{item}</p>)}
          </article>
        </div>
      </section>}
      {plan && <section className="page panel" style={{ marginTop: 22 }}><JsonDisclosure title="Structured study plan" data={plan} /></section>}
    </PageShell>
  );
}
