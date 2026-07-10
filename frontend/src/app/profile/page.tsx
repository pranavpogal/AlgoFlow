"use client";

import { useEffect, useState } from "react";
import { PageShell } from "../../components/PageShell";
import { ScoreBar } from "../../components/ScoreBar";
import { StatusCallout } from "../../components/StatusCallout";
import { apiErrorMessage, apiGet } from "../../lib/api";

type Analytics = {
  confidence: string;
  evidence_count: number;
  strongest_topics: string[];
  weakest_topics: string[];
  topic_mastery: Array<{ topic: string; score: number; confidence?: string; evidence_count?: number; risk?: string }>;
  mistake_trends: Array<{ category: string; count: number; risk: string; trend: string }>;
  evidence_summary?: Record<string, number>;
  limitations: string[];
};

export default function Profile() {
  const [data, setData] = useState<Analytics | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet<Analytics>("/analytics/demo-user").then(setData).catch((err) => setError(apiErrorMessage(err)));
  }, []);

  return (
    <PageShell>
      <section className="page panel">
        <p className="kicker">Personalized memory agent</p>
        <h2>The learner model behind the mentor.</h2>
        <p>AlgoFlow builds profile claims only from stored attempts, learning events, mistakes, memory retrieval, and mock interview evidence.</p>
        {!data && !error && <p>Loading profile evidence...</p>}
        {error && <StatusCallout title="Profile unavailable" tone="danger">{error}. Make sure the backend is running on http://localhost:8000.</StatusCallout>}
        {data && <div className="actions">
          <span className="tag blue">{data.confidence} confidence</span>
          <span className="tag green">{data.evidence_count} evidence signals</span>
          <span className="tag">Attempts: {data.evidence_summary?.attempt_count ?? 0}</span>
          <span className="tag">Events: {data.evidence_summary?.learning_event_count ?? 0}</span>
        </div>}
      </section>
      {data && <section className="grid two">
        <article className="card">
          <p className="kicker">Strong topics</p>
          {data.strongest_topics.length === 0 && <p>No strong-topic claim yet. AlgoFlow needs more evidence before saying this confidently.</p>}
          {data.strongest_topics.map((topic) => <span className="tag green" key={topic}>{topic}</span>)}
        </article>
        <article className="card">
          <p className="kicker">Weak topics</p>
          {data.weakest_topics.length === 0 && <p>No weak-topic claim yet.</p>}
          {data.weakest_topics.map((topic) => <span className="tag red" key={topic}>{topic}</span>)}
        </article>
      </section>}
      {data && <section className="grid">
        {data.topic_mastery.slice(0, 6).map((item) => (
          <article className="card" key={item.topic}>
            <p className="kicker">{item.risk ?? "unknown"} risk</p>
            <h3>{item.topic}</h3>
            <ScoreBar label="Mastery" value={item.score} />
            <p>{item.confidence ?? "unknown"} confidence · {item.evidence_count ?? 0} evidence signals</p>
          </article>
        ))}
      </section>}
      {data && <section className="grid two">
        <article className="card">
          <p className="kicker">Repeated mistakes</p>
          {data.mistake_trends.length === 0 && <p>No repeated mistake evidence yet.</p>}
          {data.mistake_trends.map((item) => <p key={item.category}>{item.category}: {item.count} total · {item.risk} risk · {item.trend}</p>)}
        </article>
        <article className="card">
          <p className="kicker">Profile limits</p>
          {data.limitations.map((item) => <p key={item}>{item}</p>)}
        </article>
      </section>}
    </PageShell>
  );
}
