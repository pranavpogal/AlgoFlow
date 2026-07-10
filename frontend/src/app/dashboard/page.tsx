"use client";

import { useEffect, useState } from "react";
import { MetricCard } from "../../components/MetricCard";
import { PageShell } from "../../components/PageShell";
import { StatusCallout } from "../../components/StatusCallout";
import { apiGet } from "../../lib/api";

type Analytics = {
  readiness_score: number;
  confidence: string;
  evidence_count: number;
  weakest_topics: string[];
  mistake_trends: Array<{ category: string; risk: string; count: number }>;
  learning_velocity: Array<{ week: string; activity_count: number; trend: string }>;
  interview_readiness: { score_percent?: number; summary?: string };
  next_best_actions: Array<{ action: string; why: string; priority: string; source: string }>;
};

export default function Dashboard() {
  const [data, setData] = useState<Analytics | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet<Analytics>("/analytics/demo-user").then(setData).catch(() => setError("Backend analytics are unavailable."));
  }, []);

  const latestVelocity = data?.learning_velocity.at(-1);
  const topMistake = data?.mistake_trends[0];

  return (
    <PageShell>
      <section className="page panel">
        <p className="kicker">Learning command center</p>
        <h2>Your interview prep, with memory.</h2>
        <p>Track readiness, weak topics, current plan, and the next best action recommended by AlgoFlow.</p>
        {!data && !error && <p>Loading learner analytics...</p>}
        {error && <StatusCallout title="Dashboard running in preview mode" tone="warning">{error} Start the backend on port 8000 to load live learner metrics.</StatusCallout>}
      </section>
      <section className="grid">
        <MetricCard
          label="Readiness score"
          value={String(data?.readiness_score ?? "--")}
          note={data ? `${data.confidence} confidence from ${data.evidence_count} evidence signals.` : "Waiting for learner evidence."}
        />
        <MetricCard
          label="Recent activity"
          value={String(latestVelocity?.activity_count ?? "--")}
          note={latestVelocity ? `${latestVelocity.week} activity is ${latestVelocity.trend}.` : "No velocity evidence yet."}
        />
        <MetricCard
          label="Top mistake"
          value={topMistake ? topMistake.risk : "--"}
          note={topMistake ? `${topMistake.category} has appeared ${topMistake.count} time(s).` : "No repeated mistakes recorded yet."}
        />
      </section>
      {data && <section className="grid">
        <article className="card">
          <p className="kicker">Weakest topics</p>
          <h3>Practice focus</h3>
          {data.weakest_topics.length === 0 && <p>No weak topic claim yet. AlgoFlow needs more reviewed solves or interview turns.</p>}
          {data.weakest_topics.map((topic) => <span className="tag" key={topic}>{topic}</span>)}
        </article>
        <article className="card">
          <p className="kicker">Mock interview</p>
          <h3>{data.interview_readiness.score_percent ?? 0}/100</h3>
          <p>{data.interview_readiness.summary ?? "No scored mock interview yet."}</p>
        </article>
        <article className="card">
          <p className="kicker">Evidence boundary</p>
          <h3>No fake mastery</h3>
          <p>Dashboard claims are derived from stored attempts, learning events, mistakes, and mock-interview scorecards.</p>
        </article>
      </section>}
      <section className="grid">
        {(data?.next_best_actions ?? [
          {
            action: "Create baseline evidence",
            why: "Analyze a problem, request hints, review code, or complete a mock turn.",
            priority: "high",
            source: "learner_state",
          },
        ]).map((item) => <article className="card" key={`${item.source}-${item.action}`}><p className="kicker">{item.priority} priority</p><h3>Next action</h3><p>{item.action}</p><p>{item.why}</p></article>)}
      </section>
    </PageShell>
  );
}
