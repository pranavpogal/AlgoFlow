import { PageShell } from "../../components/PageShell";

export default function Profile() {
  return (
    <PageShell>
      <section className="page panel">
        <p className="kicker">Personalized memory agent</p>
        <h2>The learner model behind the mentor.</h2>
        <p>AlgoFlow tracks strengths, weak spots, solved history, repeated mistakes, interview history, and pattern mastery. In production this page connects auth, consent controls, exports, and memory deletion.</p>
        <div className="actions">
          <span className="tag">Strong: Sliding Window</span>
          <span className="tag">Strong: Hash Maps</span>
          <span className="tag">Weak: Graphs</span>
          <span className="tag">Weak: DP State Design</span>
          <span className="tag">Mistake: Off-by-one</span>
        </div>
      </section>
    </PageShell>
  );
}
