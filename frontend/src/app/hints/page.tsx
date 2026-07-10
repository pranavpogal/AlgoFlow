"use client";

import { useState } from "react";
import { PageShell } from "../../components/PageShell";
import { apiPost } from "../../lib/api";

export default function Hints() {
  const [level, setLevel] = useState(0);
  const [hint, setHint] = useState<object | null>(null);

  async function next(reveal = false) {
    const response = await apiPost<{ level: number } & Record<string, unknown>>("/hints/next", {
      user_id: "demo-user",
      title: "House Robber",
      description: "Find maximum amount without robbing adjacent houses using choices at each index.",
      current_hint_level: level,
      reveal_solution: reveal
    });
    setLevel(response.level);
    setHint(response);
  }

  return (
    <PageShell>
      <section className="page panel">
        <p className="kicker">Progressive hint agent</p>
        <h2>A ladder, not an elevator.</h2>
        <p>Hints escalate slowly so the learner still does the important thinking.</p>
        <div className="actions">
          <button className="btn" onClick={() => next(false)}>Next hint</button>
          <button className="btn secondary" onClick={() => next(true)}>Reveal solution-level hint</button>
        </div>
        {hint && <pre className="result">{JSON.stringify(hint, null, 2)}</pre>}
      </section>
    </PageShell>
  );
}
