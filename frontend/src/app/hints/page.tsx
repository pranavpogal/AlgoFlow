"use client";

import { useState } from "react";
import { JsonDisclosure } from "../../components/JsonDisclosure";
import { PageShell } from "../../components/PageShell";
import { StatusCallout } from "../../components/StatusCallout";
import { apiErrorMessage, apiPost } from "../../lib/api";

type HintResponse = {
  level: number;
  max_level: number;
  hint: string;
  reveals_solution: boolean;
  mentor_note: string;
  memory_context?: { applied?: boolean; snippets?: string[]; provenance?: string[] };
};

export default function Hints() {
  const [level, setLevel] = useState(0);
  const [hint, setHint] = useState<HintResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function next(reveal = false) {
    setLoading(true);
    setError(null);
    try {
      const response = await apiPost<HintResponse>("/hints/next", {
        user_id: "demo-user",
        title: "House Robber",
        description: "Find maximum amount without robbing adjacent houses using choices at each index.",
        current_hint_level: level,
        reveal_solution: reveal
      });
      setLevel(response.level);
      setHint(response);
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <PageShell>
      <section className="page panel">
        <p className="kicker">Progressive hint agent</p>
        <h2>A ladder, not an elevator.</h2>
        <p>Hints escalate slowly so the learner still does the important thinking.</p>
        <div className="actions">
          <button className="btn" onClick={() => next(false)} disabled={loading}>{loading ? "Thinking..." : "Next hint"}</button>
          <button className="btn secondary" onClick={() => next(true)} disabled={loading}>Reveal solution-level hint</button>
        </div>
        {error && <StatusCallout title="Hint unavailable" tone="danger">{error}. Make sure the backend is running on http://localhost:8000.</StatusCallout>}
        {hint && <StatusCallout title={`Hint ${hint.level}/${hint.max_level}`} tone={hint.reveals_solution ? "warning" : "success"}>
          <p>{hint.hint}</p>
          <p>{hint.mentor_note}</p>
          {hint.memory_context?.applied && <span className="tag green">Personalized with memory</span>}
        </StatusCallout>}
        {hint && <JsonDisclosure title="Structured hint response" data={hint} />}
      </section>
    </PageShell>
  );
}
