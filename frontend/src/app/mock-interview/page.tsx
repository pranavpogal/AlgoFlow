"use client";

import type { FormEvent } from "react";
import { useState } from "react";
import { PageShell } from "../../components/PageShell";
import { apiPost } from "../../lib/api";

export default function MockInterview() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [turns, setTurns] = useState<string[]>(["Interviewer: Explain your approach."]);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    const formData = new FormData(event.currentTarget);
    const message = String(formData.get("message"));
    try {
      const response = await apiPost<{ session_id: string; interviewer_message: string }>("/mock-interview/turn", {
        user_id: "demo-user",
        session_id: sessionId,
        persona: "Google",
        problem_title: "House Robber",
        message
      });
      setSessionId(response.session_id);
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
