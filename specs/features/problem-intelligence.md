# Problem Intelligence Specification

Status: Draft
Owner: AlgoFlow
Phase: 4C

Implementation note:

Phase 4C implemented a deterministic Problem Intelligence Skill/workflow with typed taxonomy, structural evidence, confidence, provenance, compatibility response fields, learning-event integration, and a 30-case deterministic evaluation dataset. Gemini/ADK classification is not integrated yet.

## Purpose

Classify coding interview problems into evidence-backed topics, patterns, subpatterns, prerequisites, and structural cues without collapsing everything into one free-form label.

## Taxonomy Distinctions

- Topic: broad DSA area, such as Dynamic Programming or Graphs.
- Pattern: concrete solving strategy, such as LIS-style DP or Union Find.
- Subpattern: narrower implementation shape, such as Path Reconstruction.
- Structural cue: observed prompt evidence supporting the classification.
- Prerequisite concept: knowledge the learner should understand first.
- Related pattern: nearby idea useful for future transfer.

## Current Inputs

- Problem title.
- Problem description.
- Optional problem number and URL.
- Optional future known tags.

The current runtime does not parse trusted external tags, constraints, or examples as separate fields.

## Current Output

The public response remains backward-compatible with `pattern`, `sub_patterns`, and `prerequisites`, while adding confidence, evidence, provenance, structural cues, secondary topics, related patterns, and taxonomy version.

## Security and Learner-State Policy

- Classification does not imply learner mastery.
- Problem exposure is weaker than solve, review, or interview evidence.
- Curated metadata must not directly mutate mastery.
- Model output, if introduced later, must be validated against taxonomy IDs.

## Evaluation Strategy

Evaluate primary-topic accuracy, pattern precision/recall, multi-label precision/recall, confidence calibration, unsupported-claim rate, provenance completeness, and structured-output validity against the retained legacy heuristic baseline.

## Acceptance Criteria

- Typed taxonomy exists for topic, pattern, subpattern, cue, prerequisite, and related pattern.
- Classification includes evidence, confidence, and provenance.
- Ambiguous problems can return secondary topics and lower confidence.
- Learning events identify classification-only evidence.
- Deterministic tests and evals do not require Gemini access.
