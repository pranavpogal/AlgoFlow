# ADR 0001: Agent, Skill, Tool, and Workflow Boundaries

Status: Proposed

## Context

Current code defines 10 specialist agents plus a coordinator, but live FastAPI requests bypass `backend/app/agents/adk_agents.py` and execute deterministic service methods. Whitepaper principles require using the least autonomous primitive that satisfies the job.

## Decision

Retain product concepts, but classify runtime primitives as follows:

- Coordinator: future ADK-backed agent after contracts, policy, tracing, and evals exist.
- Mock interviewer: future stateful agent or workflow-agent hybrid after session state exists.
- Progressive hinting: Skill + workflow, not autonomous agent initially.
- Code review: Skill + deterministic tools + later LLM interpretation.
- Problem classification: deterministic/LLM structured classifier Skill, not autonomous agent.
- Analytics: deterministic analytics engine + interpretation Skill.
- Memory: service/tool boundary, not free-form agent mutation.

## Alternatives

- Keep all current named agents as runtime agents: rejected as decorative and over-autonomous.
- Remove all agent vocabulary: rejected because coordinator/interviewer may genuinely need agent behavior later.

## Consequences

- Documentation must distinguish current prototype from target runtime.
- Skills need contracts, evals, and activation rules.
- ADK integration becomes more meaningful but later.

## Security Impact

Reduces ambient authority by avoiding unnecessary agent access to tools/data.

## Operational Impact

Lowers model cost and runtime complexity until autonomy is justified.

## Evaluation Impact

Requires Skill trigger/collision evals and routing evals.
