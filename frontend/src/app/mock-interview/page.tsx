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

type InterviewProblem = {
  id: string;
  title: string;
  difficulty: string;
  pattern: string;
  prompt: string;
  constraints: string[];
  examples: string[];
};

const PROBLEMS: InterviewProblem[] = [
  {
    id: "house-robber",
    title: "House Robber",
    difficulty: "Medium",
    pattern: "1D Dynamic Programming",
    prompt:
      "You are given an integer array nums where nums[i] is the amount of money in the ith house. Adjacent houses cannot both be robbed. Return the maximum amount you can rob tonight.",
    constraints: ["1 <= nums.length <= 10^5", "0 <= nums[i] <= 10^4"],
    examples: ["Input: nums = [1,2,3,1] -> Output: 4", "Input: nums = [2,7,9,3,1] -> Output: 12"],
  },
  {
    id: "number-of-islands",
    title: "Number of Islands",
    difficulty: "Medium",
    pattern: "Graph Traversal",
    prompt:
      "Given an m x n grid of '1's and '0's, return the number of islands. An island is surrounded by water and connected horizontally or vertically.",
    constraints: ["1 <= m, n <= 300", "grid[i][j] is '0' or '1'"],
    examples: ["Input: grid with one connected land mass -> Output: 1", "Input: grid with three separated land masses -> Output: 3"],
  },
  {
    id: "minimum-window-substring",
    title: "Minimum Window Substring",
    difficulty: "Hard",
    pattern: "Sliding Window",
    prompt:
      "Given strings s and t, return the minimum window substring of s such that every character in t, including duplicates, is included in the window.",
    constraints: ["1 <= s.length, t.length <= 10^5", "s and t consist of English letters"],
    examples: ['Input: s = "ADOBECODEBANC", t = "ABC" -> Output: "BANC"'],
  },
];

export default function MockInterview() {
  const [problem, setProblem] = useState<InterviewProblem>(PROBLEMS[0]);
  const [persona, setPersona] = useState<"Google" | "Meta" | "Amazon" | "Generic">("Google");
  const [started, setStarted] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [turns, setTurns] = useState<string[]>([]);
  const [scorecard, setScorecard] = useState<InterviewTurnResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function startInterview() {
    setSessionId(null);
    setScorecard(null);
    setError(null);
    setStarted(true);
    setTurns(openingTurns(problem));
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    const formData = new FormData(event.currentTarget);
    const message = String(formData.get("message"));
    const baseTurns = started ? turns : openingTurns(problem);
    if (!started) setStarted(true);
    try {
      const response = await apiPost<InterviewTurnResponse>("/mock-interview/turn", {
        user_id: "demo-user",
        session_id: sessionId,
        persona,
        problem_title: problem.title,
        message
      });
      setSessionId(response.session_id);
      setScorecard(response);
      setTurns([...baseTurns, `You: ${message}`, `Interviewer: ${response.interviewer_message}`]);
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
        <div className="grid two" style={{ marginTop: 18, marginBottom: 18 }}>
          <article className="card">
            <p className="kicker">Interview setup</p>
            <label className="muted" htmlFor="problem-select">Problem</label>
            <select
              id="problem-select"
              className="select"
              value={problem.id}
              onChange={(event) => {
                const nextProblem = PROBLEMS.find((item) => item.id === event.target.value) ?? PROBLEMS[0];
                setProblem(nextProblem);
                setStarted(false);
                setTurns([]);
                setSessionId(null);
                setScorecard(null);
              }}
            >
              {PROBLEMS.map((item) => <option value={item.id} key={item.id}>{item.title}</option>)}
            </select>
            <label className="muted" htmlFor="persona-select">Interviewer persona</label>
            <select
              id="persona-select"
              className="select"
              value={persona}
              onChange={(event) => setPersona(event.target.value as typeof persona)}
            >
              <option>Google</option>
              <option>Meta</option>
              <option>Amazon</option>
              <option>Generic</option>
            </select>
            <button className="btn" type="button" onClick={startInterview}>Start interview</button>
          </article>
          <article className="card">
            <p className="kicker">{problem.difficulty} · {problem.pattern}</p>
            <h3>{problem.title}</h3>
            <p>{problem.prompt}</p>
            {problem.examples.map((item) => <p className="mono" key={item}>{item}</p>)}
            {problem.constraints.map((item) => <span className="tag blue" key={item}>{item}</span>)}
          </article>
        </div>
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
        {!started && <StatusCallout title="Start with the problem" tone="info">Choose a problem and persona, then click Start interview. AlgoFlow will open like a real interviewer before scoring your answer.</StatusCallout>}
        <div className="timeline">{turns.map((turn) => {
          const isUser = turn.startsWith("You:");
          return <div className={`timeline-item ${isUser ? "user" : "interviewer"}`} key={turn}>{turn}</div>;
        })}</div>
        <form onSubmit={submit} className="form" style={{ marginTop: 16 }}>
          <textarea className="textarea" name="message" placeholder={`Explain your approach for ${problem.title}. Include invariant, complexity, and edge cases.`} />
          <button className="btn" disabled={loading}>{loading ? "Interviewer is evaluating..." : "Send answer"}</button>
        </form>
        {error && <StatusCallout title="Interview unavailable" tone="danger">{error}. Make sure the backend is running on http://localhost:8000.</StatusCallout>}
        {scorecard && <JsonDisclosure title="Structured interview turn" data={scorecard} />}
      </section>
    </PageShell>
  );
}

function openingTurns(problem: InterviewProblem): string[] {
  return [
    `Interviewer: Let's work on ${problem.title}. ${problem.prompt}`,
    "Interviewer: Before coding, explain your approach and the invariant or data structure you would rely on.",
  ];
}
