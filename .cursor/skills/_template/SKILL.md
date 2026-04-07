---
name: <skill-id>
description: >-
  <WHAT: one sentence, third person, specific capabilities>.
  <WHEN: trigger phrases, file paths, user phrases, related DocTypes/APIs>.
# disable-model-invocation: true
# Uncomment only for narrow procedural or policy-only skills that should not
# auto-load from ambient context (backport workflows, gettext regen, commit drafting).
---

# <Human-readable title>

<!-- REQUIRED: Scope — when this skill applies and when it does not (1–3 sentences). -->

## Scope

<When to use this skill. When to defer to a sibling skill instead.>

<!-- OPTIONAL: Prerequisites — bench/site assumptions, Frappe major, tools. -->

## Prerequisites

- **Frappe version:** v15 (change if major-specific)
- **Workspace:** run bench commands from the correct bench root (workspace rule *command-working-directory-selection*)

<!-- REQUIRED: Core content — pick one or combine archetype sections below. -->

## Quick rules

<!-- Recipe archetype: bullets the agent must not skip. -->

## Mental model

<!-- Reference archetype: layers, evaluation order, request lifecycle. -->

## Workflow

<!-- Recipe / workflow: numbered steps or checklist. -->

## Phase 0 — <title>

<!-- Long workflow archetype: mandatory gates before destructive work. -->

## Reference

<!-- Tables, API matrices, MCP argument lists. -->

<!-- OPTIONAL: copy-paste examples only when non-obvious. -->

## Patterns

```python
# Minimal example
```

<!-- OPTIONAL: short anti-patterns. -->

## Pitfalls

- <Common mistake and fix>

<!-- REQUIRED when any sibling skill is referenced in body or description. -->

## Related skills

- [`<skill-id>`](<skill-id>/SKILL.md) — <why link>

<!-- OPTIONAL: progressive disclosure when SKILL.md would exceed ~400 lines. -->

## Additional resources

- [reference.md](reference.md) — extended templates, full command reference
