"use client";

import { useEffect, useState } from "react";
import { PageShell } from "../../components/PageShell";
import { ScoreBar } from "../../components/ScoreBar";
import { StatusCallout } from "../../components/StatusCallout";
import { apiErrorMessage, apiGet } from "../../lib/api";

type Analytics = {
  readiness_score: number;
  readiness_components: Record<string, number | string | Record<string, number>>;
  confidence: string;
  evidence_count: number;
  strongest_topics: string[];
  weakest_topics: string[];
  common_mistakes: Array<{ category: string; count: number; confidence?: string }>;
  mistake_trends: Array<{ category: string; count: number; recent_count: number; risk: string; trend: string }>;
  topic_mastery: Array<{ topic: string; score: number; confidence?: string; evidence_count?: number; risk?: string }>;
  topic_risk: Array<{ topic: string; score: number; risk: string; reason: string }>;
  learning_velocity: Array<{ week: string; activity_count: number; attempt_count: number; event_count: number; mistake_signal_count: number; trend: string; top_patterns?: string[] }>;
  interview_readiness: { score_percent?: number; confidence?: string; summary?: string; rubric_strengths?: string[]; rubric_weaknesses?: string[] };
  next_best_actions: Array<{ action: string; why: string; priority: string; source: string }>;
  recommendations: string[];
  evidence_summary?: Record<string, number>;
  limitations: string[];
};

export default function Analytics() {
  const [data, setData] = useState<Analytics | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { apiGet<Analytics>("/analytics/demo-user").then(setData).catch((err) => setError(apiErrorMessage(err))); }, []);

  return (
    <PageShell>
      <section className="page panel">
        <p className="kicker">Learning analytics agent</p>
        <h2>See the shape of your preparation.</h2>
        {!data && <p>Loading analytics from memory...</p>}
        {error && <StatusCallout title="Analytics unavailable" tone="danger">{error}. Make sure the backend is running on http://localhost:8000.</StatusCallout>}
        {data && <>
          <div className="metric">{data.readiness_score}</div>
          <p>Interview readiness score · {data.confidence} confidence · {data.evidence_count} evidence signals</p>
          <div className="grid two" style={{ marginTop: 20 }}>
            <ScoreBar label="Mastery" value={Number(data.readiness_components.mastery ?? 0)} />
            <ScoreBar label="Consistency" value={Number(data.readiness_components.consistency ?? 0)} />
            <ScoreBar label="Interview" value={Number(data.readiness_components.interview ?? 0)} />
            <ScoreBar label="Mistake penalty" value={Number(data.readiness_components.mistake_penalty ?? 0)} />
          </div>
          <div>{data.strongest_topics.map((topic) => <span className="tag" key={topic}>Strong: {topic}</span>)}</div>
          <div>{data.weakest_topics.map((topic) => <span className="tag" key={topic}>Weak: {topic}</span>)}</div>
          {data.strongest_topics.length === 0 && data.weakest_topics.length === 0 && <p>Not enough evidence yet to claim strong or weak topics. Analyze problems, request hints, or review code to build the learner model.</p>}
        </>}
      </section>
      {data && <section className="grid">
        {data.topic_mastery.map((item) => <article className="card" key={item.topic}><h3>{item.topic}</h3><div className="metric">{item.score}</div><p>{item.confidence ?? "unknown"} confidence · {item.evidence_count ?? 0} evidence signals · {item.risk ?? "unknown"} risk</p></article>)}
      </section>}
      {data && <section className="grid">
        <article className="card">
          <p className="kicker">Learning velocity</p>
          <h3>Recent activity</h3>
          {data.learning_velocity.length === 0 && <p>No velocity evidence yet.</p>}
          {data.learning_velocity.map((item) => <p key={item.week}>{item.week}: {item.activity_count} activities, {item.attempt_count} attempts, {item.mistake_signal_count} mistake signals · {item.trend}</p>)}
        </article>
        <article className="card">
          <p className="kicker">Mistake trends</p>
          <h3>Recurring risks</h3>
          {data.mistake_trends.length === 0 && <p>No repeated mistake evidence yet.</p>}
          {data.mistake_trends.map((item) => <p key={item.category}>{item.category}: {item.count} total, {item.recent_count} recent · {item.risk} risk</p>)}
        </article>
        <article className="card">
          <p className="kicker">Mock readiness</p>
          <h3>{data.interview_readiness.score_percent ?? 0}/100</h3>
          <p>{data.interview_readiness.summary ?? "No scored mock-interview evidence yet."}</p>
          {(data.interview_readiness.rubric_weaknesses ?? []).map((item) => <span className="tag" key={item}>Practice: {item}</span>)}
        </article>
      </section>}
      {data && <section className="grid">
        {data.next_best_actions.map((item) => <article className="card" key={`${item.source}-${item.action}`}><p className="kicker">{item.priority} priority</p><h3>{item.action}</h3><p>{item.why}</p><span className="tag">{item.source}</span></article>)}
      </section>}
      {data && data.limitations.length > 0 && <section className="page panel">
        <p className="kicker">Evidence limits</p>
        <h2>What this score does not claim.</h2>
        {data.limitations.map((item) => <p key={item}>{item}</p>)}
      </section>}
    </PageShell>
  );
}
