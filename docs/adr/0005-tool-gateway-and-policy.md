# ADR 0005: Tool Gateway and Hybrid Policy Enforcement

Status: Proposed

## Context

Tools are currently plain functions called directly by services or listed on ADK agents. There is no centralized authorization, validation, timeout, or observability.

## Decision

Introduce a tool gateway with structural policy first, then semantic policy where needed. Every tool should declare identity, input/output schema, permission scope, timeout behavior, and risk level.

## Alternatives

- Let agents call Python functions directly: rejected for production.
- Rely on prompts for policy: rejected.

## Consequences

- Existing tools become registered capabilities.
- Services/agents call gateway, not raw tools, for sensitive or observable operations.

## Security Impact

Critical for least privilege, intent preservation, and tenant isolation.

## Operational Impact

Adds a small control-plane layer and logs.

## Evaluation Impact

Tool-use evals can inspect allowed/denied calls and trajectory quality.
