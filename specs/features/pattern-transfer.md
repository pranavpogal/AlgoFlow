# Pattern Transfer Specification

Status: Draft
Owner: AlgoFlow
Phase: 4D

Implementation note:

Phase 4D implemented a deterministic Pattern Transfer Skill/workflow with transfer taxonomy, structural relationship model, conservative learner-state integration, Problem Intelligence integration, learning events, and a 15-case deterministic eval dataset with development, held-out, and adversarial splits. Gemini/ADK model reasoning is not integrated yet.

## Purpose

Recommend structurally meaningful transfer opportunities between coding interview problems without reducing recommendation to same-topic or same-tag matching.

## Transfer Taxonomy

- `PREREQUISITE_REPAIR`: Repair missing prerequisite knowledge before progressing.
- `REINFORCEMENT`: Practice substantially similar structure to stabilize uncertain capability.
- `NEAR_TRANSFER`: Apply a known structural idea in a closely related formulation.
- `FAR_TRANSFER`: Apply a known structural idea in a substantially different surface formulation.
- `PATTERN_VARIATION`: Exercise a meaningful variation of an existing pattern.
- `DIFFICULTY_PROGRESSION`: Move to a harder variant after sufficient evidence.
- `MISCONCEPTION_REMEDIATION`: Select a problem that exposes or corrects a recurring misconception.
- `INTERLEAVING`: Mix related structures to improve pattern discrimination.
- `CONTRASTIVE_TRANSFER`: Compare similar-looking problems whose decision rules differ.
- `NOVEL_COMPOSITION`: Combine multiple previously encountered structures in a new way.

## Current Inputs

- Current problem title and description.
- Phase 4C Problem Intelligence classification.
- Derived learner state.
- User-scoped memory snapshot.
- Recent pattern-transfer recommendation events.
- Bounded static transfer corpus.

## Evidence Hierarchy

Current hierarchy, from weaker to stronger:

1. Passive exposure.
2. Pattern encountered.
3. Hint-assisted reasoning.
4. Approach submitted.
5. Review finding.
6. Repeated independent success.
7. Verified successful transfer.

The final two are target-state concepts and are not fully available in Phase 4D.

## Current Output

Each recommendation includes:

- recommendation type
- source and target problem IDs
- source and target patterns
- shared structures
- important differences
- learner evidence used
- classification, relationship, learner, and recommendation confidence
- transfer bridge
- expected learning goal
- evidence and provenance
- unsupported claims

## Current / Target / Deferred

Current:

- Deterministic transfer workflow.
- Static transfer corpus.
- Curated structural relationship edges.
- Conservative learner-state use.
- Learning events for shown recommendations.

Target:

- Larger problem corpus.
- Explicit solved/attempted/accepted/rejected transfer state.
- Stronger mastery and verified transfer signals.
- Shared evaluation reporting across Skills.

Deferred:

- Gemini/ADK model reasoning.
- Vector retrieval for transfer.
- Verified code execution or test-backed transfer success.
- Production auth/OIDC and tenant isolation beyond current local-safe principal scaffold.
