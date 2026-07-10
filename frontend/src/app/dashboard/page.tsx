import { MetricCard } from "../../components/MetricCard";
import { PageShell } from "../../components/PageShell";

export default function Dashboard() {
  return (
    <PageShell>
      <section className="page panel">
        <p className="kicker">Learning command center</p>
        <h2>Your interview prep, with memory.</h2>
        <p>Track readiness, weak topics, current plan, and the next best action recommended by AlgoFlow.</p>
      </section>
      <section className="grid">
        <MetricCard label="Readiness score" value="72" note="Strong enough for mocks; DP and graphs still need reps." />
        <MetricCard label="Solved recently" value="18" note="Velocity is improving over the last three weeks." />
        <MetricCard label="Top mistake" value="DP init" note="Base-case drills should happen before more hard problems." />
      </section>
      <section className="grid">
        {[
          "Analyze House Robber and capture its decision-DP pattern.",
          "Do one hint-limited solve without revealing the solution.",
          "Run a Google-style mock focused on explaining invariants."
        ].map((item) => <article className="card" key={item}><h3>Next action</h3><p>{item}</p></article>)}
      </section>
    </PageShell>
  );
}
