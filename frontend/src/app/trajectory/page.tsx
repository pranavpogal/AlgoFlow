"use client";

import type { FormEvent } from "react";
import { useState } from "react";
import { JsonDisclosure } from "../../components/JsonDisclosure";
import { PageShell } from "../../components/PageShell";
import { StatusCallout } from "../../components/StatusCallout";
import { apiErrorMessage, apiGet, apiPost } from "../../lib/api";

type TrajectoryEvent = {
  event_type: string;
  message: string;
  selected_skill?: string | null;
  tool_name?: string | null;
  latency_ms?: number | null;
  metadata?: Record<string, unknown>;
};

type MentorRouteResponse = {
  selected_capability: string;
  selected_skill: string;
  result: Record<string, unknown>;
  trajectory: {
    trajectory_id: string;
    runtime_mode: string;
    fallback_used: boolean;
    event_count?: number;
    events: TrajectoryEvent[];
  };
};

type PolicyDecision = {
  id: string;
  tool_id: string;
  caller: string;
  operation: string;
  risk: string;
  decision: string;
  policy_id: string;
  reason: string;
  success: boolean;
  latency_ms?: number | null;
};

export default function TrajectoryPage() {
  const [route, setRoute] = useState<MentorRouteResponse | null>(null);
  const [policy, setPolicy] = useState<PolicyDecision[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setPolicy([]);
    const formData = new FormData(event.currentTarget);
    try {
      const response = await apiPost<MentorRouteResponse>("/mentor/route", {
        user_id: "demo-user",
        requested_capability: String(formData.get("capability")),
        title: String(formData.get("title")),
        description: String(formData.get("description")),
        user_message: String(formData.get("message")),
        current_hint_level: 0,
        reveal_solution: false,
      });
      setRoute(response);
      try {
        const decisions = await apiGet<PolicyDecision[]>(`/agent-trajectories/${response.trajectory.trajectory_id}/policy-decisions`);
        setPolicy(decisions);
      } catch {
        setPolicy([]);
      }
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <PageShell>
      <section className="page panel">
        <p className="kicker">Trajectory and policy visibility</p>
        <h2>Watch the governed mentor route make a decision.</h2>
        <p>This page exercises the narrow ADK coordinator route and shows routing trajectory, fallback status, tool events, and persisted policy decisions when available.</p>
        <form onSubmit={submit} className="form">
          <select className="select" name="capability" defaultValue="problem_analysis">
            <option value="problem_analysis">Problem analysis</option>
            <option value="next_hint">Next hint</option>
            <option value="recommendations">Recommendations</option>
            <option value="pattern_transfer">Pattern transfer</option>
            <option value="code_review">Code review</option>
            <option value="study_plan">Study plan</option>
          </select>
          <input className="input" name="title" defaultValue="House Robber" />
          <input className="input" name="message" defaultValue="Analyze the pattern and explain the next safe mentoring step." />
          <textarea className="textarea" name="description" defaultValue="Find the maximum amount without robbing adjacent houses. Adjacent houses cannot both be chosen." />
          <button className="btn" disabled={loading}>{loading ? "Tracing route..." : "Run governed route"}</button>
        </form>
        {error && <StatusCallout title="Route unavailable" tone="danger">{error}. Make sure the backend is running on http://localhost:8000.</StatusCallout>}
      </section>
      {route && <section className="grid">
        <article className="card">
          <p className="kicker">Selected capability</p>
          <h3>{route.selected_capability}</h3>
          <p>{route.selected_skill}</p>
        </article>
        <article className="card">
          <p className="kicker">Runtime</p>
          <h3>{route.trajectory.runtime_mode}</h3>
          <p>Fallback used: {String(route.trajectory.fallback_used)}</p>
        </article>
        <article className="card">
          <p className="kicker">Trace identity</p>
          <h3 className="mono">{route.trajectory.trajectory_id.slice(0, 18)}...</h3>
          <p>{route.trajectory.events.length} trajectory events</p>
        </article>
      </section>}
      {route && <section className="split">
        <div className="panel">
          <p className="kicker">Trajectory events</p>
          <h2>Execution path</h2>
          <div className="event-rail">
            {route.trajectory.events.map((event, index) => (
              <div className="event-row" key={`${event.event_type}-${index}`}>
                <code>{event.event_type}</code>
                <div>
                  <strong>{event.tool_name ?? event.selected_skill ?? "runtime"}</strong>
                  <p>{event.message}</p>
                  {event.latency_ms !== null && event.latency_ms !== undefined && <span className="tag">{event.latency_ms} ms</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="stack">
          <article className="card">
            <p className="kicker">Policy decisions</p>
            {policy.length === 0 && <p>No persisted policy records returned for this trajectory. Some safe routes may not request a gateway tool.</p>}
            {policy.map((item) => <p key={item.id}><strong>{item.tool_id}</strong>: {item.decision} via {item.policy_id}. {item.reason}</p>)}
          </article>
          <article className="card">
            <p className="kicker">Mentor result</p>
            <JsonDisclosure title="Route response" data={route.result} />
          </article>
        </div>
      </section>}
      {route && <section className="page panel" style={{ marginTop: 22 }}>
        <JsonDisclosure title="Full trajectory payload" data={route.trajectory} />
      </section>}
    </PageShell>
  );
}
