---
name: milestone-phase-planning
description: >-
  Structures project plans into independently shippable feature milestones with
  document → refactor → implement phases. Use when planning, revising, or
  breaking down implementation work (plans, vault project notes, roadmaps, PR
  scoping).
---

# Milestone and phase planning

## Scope

Use when breaking implementation work into a plan. Each milestone ships as one independent feature (typically one PR). Milestones 2–5 in issue-76 follow this pattern; see vault [[Milestones follow document refactor implement]] for a concrete roadmap.

## Milestones

- A milestone is a part that can be implemented and shipped as an **independent feature** — typically **one PR**.
- Order milestones by dependency; mark milestones that are independent and can be reordered or pulled forward.
- Behaviour-changing milestones come after the milestone that introduces the data/structure they need (e.g. ship a feature with old mechanics + new source first; change the mechanics in a later milestone).

## Phases within a milestone

Each milestone follows three phases, starting from existing behaviour where applicable:

1. **Document** — characterization tests pin the current behaviour of the area about to change. Assert observable output only (API results, XML fragments, file contents), never implementation details.
2. **Refactor** — extract what is reusable *with respect to the planned changes* into standalone functions with unit tests. The phase 1 characterization tests stay green, unmodified.
3. **Implement** — the new behaviour, with its own unit tests plus integration tests that mirror the phase 1 suite for the new path.

For greenfield milestones (no existing behaviour), phase 1 shrinks or drops; keep phases 2–3.

## Branching inside implementations

When old and new behaviour coexist behind a toggle, the **caller** of a branch-specific function decides which path runs — not the callee. Data-model changes (tables, fields, settings flags) land together in one phase, inert, before any behaviour branches on them; migrations land in a later phase than the data model they migrate to.

Release-only milestones (backports, translations, rollout) follow the phase structure loosely — apply it fully only where behaviour changes (e.g. removing a feature toggle).
