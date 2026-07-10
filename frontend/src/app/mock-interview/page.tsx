"use client";

import type { FormEvent } from "react";
import { useState } from "react";
import { JsonDisclosure } from "../../components/JsonDisclosure";
import { PageShell } from "../../components/PageShell";
import { ScoreBar } from "../../components/ScoreBar";
import { StatusCallout } from "../../components/StatusCallout";
import { apiErrorMessage, apiPost } from "../../lib/api";

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
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setLoading(true);
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
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <PageShell>
      <section className="page panel">
        <p className="kicker">Mock interview agent</p>
        <h2>Practice the signal interviewers actually evaluate.</h2>
        <p>This session persists transcript state and rubric scoring, then uses the next turn to pressure-test communication, complexity, testing, and adaptability.</p>
        {scorecard && (
          <div className="callout success" style={{ marginBottom: 16 }}>
            <strong>Turn {scorecard.turn_index}</strong> · Stage: {scorecard.stage} · Focus: {scorecard.follow_up_focus}
            <br />
            {scorecard.evaluation_summary}
            {Object.entries(scorecard.rubric_scores).map(([label, value]) => (
              <ScoreBar key={label} label={label.replaceAll("_", " ")} value={value} max={5} />
            ))}
          </div>
        )}
        <div className="timeline">{turns.map((turn) => {
          const isUser = turn.startsWith("You:");
          return <div className={`timeline-item ${isUser ? "user" : "interviewer"}`} key={turn}>{turn}</div>;
        })}</div>
        <form onSubmit={submit} className="form" style={{ marginTop: 16 }}>
          <textarea className="textarea" name="message" placeholder="Explain your approach, complexity, edge cases, or optimization." />
          <button className="btn" disabled={loading}>{loading ? "Interviewer is evaluating..." : "Send answer"}</button>
        </form>
        {error && <StatusCallout title="Interview unavailable" tone="danger">{error}. Make sure the backend is running on http://localhost:8000.</StatusCallout>}
        {scorecard && <JsonDisclosure title="Structured interview turn" data={scorecard} />}
      </section>
    </PageShell>
  );
}
