# Prompt-Injection Boundary

Status: Current
Owner: AlgoFlow

## Scope

Phase 19 adds bounded deterministic suspicion signals for obvious instruction-override pressure relevant to tool execution. This is not a complete prompt-injection solution.

## Current Detection

The semantic policy evaluator scans untrusted user/problem text for patterns such as:

- ignore previous instructions
- bypass policy
- pretend I am an admin
- call every available tool
- reveal hidden instructions
- override system policy
- change caller identity
- disable safety checks

Matching content is recorded as `PROMPT_INJECTION_SUSPECTED` when it attempts to override policy/tool boundaries.

## Instruction / Data Separation

User prompts, problem statements, submitted code, retrieved text, and future model-generated arguments are treated as data. They cannot redefine:

- caller identity
- principal identity
- tool allowlists
- operation type
- mentoring mode
- reveal authorization
- policy version

## Current Mitigation Level

MITIGATED:

- obvious tool-policy override strings in governed gateway calls
- caller spoofing through untrusted text
- reveal authorization spoofing through model/user arguments

PARTIALLY MITIGATED:

- indirect prompt injection in problem statements
- malicious text that does not match the bounded pattern list
- tool confusion from future model-generated arguments

DEFERRED:

- LLM-based or learned injection classifier
- external-content provenance scoring
- admin review UI for policy decisions

OUT OF SCOPE:

- arbitrary web/tool output sanitization
- secure code execution sandboxing
