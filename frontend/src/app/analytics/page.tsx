"use client";

import { useEffect, useState } from "react";
import { PageShell } from "../../components/PageShell";
import { apiGet } from "../../lib/api";

type Analytics = {
  readiness_score: number;
  confidence: string;
  evidence_count: number;
  strongest_topics: string[];
  weakest_topics: string[];
  common_mistakes: Array<{ category: string; count: number; confidence?: string }>;
  topic_mastery: Array<{ topic: string; score: number; confidence?: string; evidence_count?: number }>;
  recommendations: string[];
  evidence_summary?: Record<string, number>;
};

export default function Analytics() {
  const [data, setData] = useState<Analytics | null>(null);
  useEffect(() => { apiGet<Analytics>("/analytics/demo-user").then(setData).catch(() => undefined); }, []);

  return (
    <PageShell>
      <section className="page panel">
        <p className="kicker">Learning analytics agent</p>
        <h2>See the shape of your preparation.</h2>
        {!data && <p>Loading analytics from memory...</p>}
        {data && <>
          <div className="metric">{data.readiness_score}</div>
          <p>Interview readiness score · {data.confidence} confidence · {data.evidence_count} evidence signals</p>
          <div>{data.strongest_topics.map((topic) => <span className="tag" key={topic}>Strong: {topic}</span>)}</div>
          <div>{data.weakest_topics.map((topic) => <span className="tag" key={topic}>Weak: {topic}</span>)}</div>
          {data.strongest_topics.length === 0 && data.weakest_topics.length === 0 && <p>Not enough evidence yet to claim strong or weak topics. Analyze problems, request hints, or review code to build the learner model.</p>}
        </>}
      </section>
      {data && <section className="grid">
        {data.topic_mastery.map((item) => <article className="card" key={item.topic}><h3>{item.topic}</h3><div className="metric">{item.score}</div><p>{item.confidence ?? "unknown"} confidence · {item.evidence_count ?? 0} evidence signals</p></article>)}
      </section>}
    </PageShell>
  );
}
