"use client";

import type { FormEvent } from "react";
import { useState } from "react";
import { PageShell } from "../../components/PageShell";
import { apiPost } from "../../lib/api";

type InterviewTurnResponse = {
  session_id: string;
  interviewer_message: string;
  follow_up_focus: string;
  stage: string;
  turn_index: number;
  rubric_scores: Record<string, number>;
  evaluation_summary?: string | null;
};

export default function MockInterview() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [turns, setTurns] = useState<string[]>(["Interviewer: Explain your approach."]);
  const [scorecard, setScorecard] = useState<InterviewTurnResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    const formData = new FormData(event.currentTarget);
    const message = String(formData.get("message"));
    try {
      const response = await apiPost<InterviewTurnResponse>("/mock-interview/turn", {
        user_id: "demo-user",
        session_id: sessionId,
        persona: "Google",
        problem_title: "House Robber",
        message
      });
      setSessionId(response.session_id);
      setScorecard(response);
      setTurns([...turns, `You: ${message}`, `Interviewer: ${response.interviewer_message}`]);
      event.currentTarget.reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to send the interview turn.");
    }
  }

  return (
    <PageShell>
      <section className="page panel">
        <p className="kicker">Mock interview agent</p>
        <h2>Practice the signal interviewers actually evaluate.</h2>
        {scorecard && (
          <div className="result" style={{ marginBottom: 16 }}>
            <strong>Turn {scorecard.turn_index}</strong> · Stage: {scorecard.stage} · Focus: {scorecard.follow_up_focus}
            <br />
            {scorecard.evaluation_summary}
            <div className="metric-grid" style={{ marginTop: 12 }}>
              {Object.entries(scorecard.rubric_scores).map(([label, value]) => (
                <div className="metric-card" key={label}>
                  <span>{label.replaceAll("_", " ")}</span>
                  <strong>{value}/5</strong>
                </div>
              ))}
            </div>
          </div>
        )}
        <div className="timeline">{turns.map((turn) => <div className="timeline-item" key={turn}>{turn}</div>)}</div>
        <form onSubmit={submit} className="form" style={{ marginTop: 16 }}>
          <textarea className="textarea" name="message" placeholder="Explain your approach, complexity, edge cases, or optimization." />
          <button className="btn">Send answer</button>
        </form>
        {error && <div className="result">Error: {error}. Make sure the backend is running on http://localhost:8000.</div>}
      </section>
    </PageShell>
  );
}
