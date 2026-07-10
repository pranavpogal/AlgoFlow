# Problem Intelligence Skill

Use this Skill when AlgoFlow needs to classify a coding problem into topics, patterns, subpatterns, prerequisites, and structural cues.

Do not use this Skill for:

- Recommending a full study path.
- Pattern transfer instruction.
- Inferring learner mastery from exposure.
- Replacing deterministic evidence with unvalidated model labels.

## Procedure

1. Treat the problem title, statement, constraints, examples, and tags as separate evidence sources when available.
2. Prefer curated metadata when a known canonical problem is recognized.
3. Use structural cues before weak keywords.
4. Emit confidence and provenance for inferred labels.
5. Preserve uncertainty for ambiguous or multi-label problems.
6. Return backward-compatible topic/pattern fields for current runtime consumers.
7. Never convert problem classification into mastery evidence by itself.

## Safety

Classification may influence hints, planning, and future recommendations, but it must not directly prove competence. Problem exposure is weaker evidence than a correct solution, code review, or mock-interview performance.
