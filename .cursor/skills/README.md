# Project skills (`.cursor/skills/`)

Cursor Agent Skills for Frappe development in this workspace. They teach the agent team-specific workflows, APIs, and policies that are not obvious from generic Frappe docs.

**Do not** add skills under `~/.cursor/skills-cursor/` — that directory is reserved for Cursor built-in skills.

**Template:** copy [`_template/SKILL.md`](_template/SKILL.md) when adding a skill. Use [`_template/reference.md`](_template/reference.md) when the main file would exceed ~400 lines. See [`create-skill`](create-skill/SKILL.md) for content policy and Cursor skill cross-reference.

---

## When to add a skill

Add a skill when knowledge is:

- **Stable** — unlikely to change every week without an intentional update
- **Non-obvious** — pitfalls, house style, or tool surfaces the model would not reliably infer
- **Repeated** — the same questions or mistakes come up across tasks

Skip a skill for one-off tasks, generic Frappe documentation, or content that belongs in app `README` / official docs only.

---

## Naming and layout

| Rule | Detail |
|------|--------|
| **Path** | `.cursor/skills/<skill-id>/SKILL.md` |
| **Folder = `name`** | `name` in frontmatter must match the directory (`frappe-background-jobs`) |
| **Pattern** | `{domain}-{topic}` — `frappe-*`, `alyf-*`, `github-mcp-*` |
| **Commands** | `.cursor/commands/bench-*.md` for bench CLI entry points; defer to a `frappe-*` skill when the workflow needs AskQuestion or multi-step guidance (e.g. `bench-new-app` → `frappe-new-app`) |
| **Length** | `name` max 64 chars; lowercase letters, numbers, hyphens only |

### Skill archetypes

Pick sections from the template; not every skill needs every block.

| Archetype | Examples | Typical sections |
|-----------|----------|------------------|
| **Reference** | `frappe-db-permissions`, `frappe-permissions` | Mental model → tables → pitfalls |
| **Recipe** | `frappe-list-views`, `frappe-document-field-changes` | Quick rules → workflow → patterns |
| **Workflow** | `frappe-testing`, `frappe-backport-merge-conflicts`, `frappe-new-app` | Phases → AskQuestion policy → commands |
| **Integration** | `github-mcp-*` | Server selection → tool tables → examples |
| **Policy / org** | `alyf-commit-messages`, `alyf-frappe-app-ci` | Scope → rules → self-check → examples |

---

## Frontmatter

```yaml
---
name: <skill-id>
description: >-
  <WHAT: third person, one sentence on capabilities>.
  <WHEN: trigger phrases, paths, DocTypes, user phrases>.
# disable-model-invocation: true   # see table below
---
```

### Description checklist

- **Third person** — “Explains…”, “Uses…”, not “I can help…” or “You should…”
- **WHAT** — specific capabilities
- **WHEN** — trigger terms so discovery works without reading the body
- Prefer folded `description: >-` when the description spans multiple lines

### `disable-model-invocation`

| Set `disable-model-invocation: true` | Omit (default auto-discovery) |
|--------------------------------------|-------------------------------|
| Narrow procedural workflows (backport conflicts, gettext regen) | Domain reference (permissions, hooks, list views) |
| Policy / format-only (commit message drafting) | MCP tool catalogs matched by description triggers |
| Would mislead if applied without explicit user intent | |

Current skills with `true`: `alyf-commit-messages`, `draft-github-issue-texts`, `frappe-gettext-localization`, `frappe-backport-merge-conflicts`.

---

## Body structure

1. **`#` title** — short human title (avoid redundant `Frappe` prefix unless needed for disambiguation)
2. **`## Scope`** — required; when to use / not use; defer to siblings
3. **Core sections** — per archetype (`## Quick rules`, `## Mental model`, `## Workflow`, …)
4. **`## Related skills`** — required when any sibling is referenced in description or body; use markdown links: `` [`skill-id`](skill-id/SKILL.md) ``
5. **`## Additional resources`** — link to `reference.md` when split

### Length

- Target **&lt; 300 lines** in `SKILL.md`
- Split to **`reference.md`** around **400+** lines or for large static templates (YAML, workflow copies)

### Frappe prose

When mentioning Frappe concepts in skills, follow the workspace **Frappe Markdown** rule:

- **DocType** names in bold
- _Field labels_ in italics
- Field names in `` `inline code` ``

### AskQuestion

Use **AskQuestion** (or ask in chat if unavailable) when:

- Multiple benches or MCP servers could apply
- Git branch / dependency alignment must be confirmed before irreversible work
- Policy requires a user choice (e.g. Jira key placement — see `alyf-commit-messages`)

### Do not duplicate workspace rules

Point to existing **rules** (brief reminders) and **skills** (full detail) instead of copying them:

- Bench / app working directory — rule *command-working-directory-selection* → skill `command-working-directory-selection`
- Conventional Commits — rule *generate-commit-message-commitlint* → skill `alyf-commit-messages`
- Milestone / phase planning — rule *milestone-phase-planning*
- DocType JSON — edit via `bench console`, not hand-edited JSON files
- Less defensive code — workspace rule *Less defensive code*

---

## Inventory

Update this table when adding or renaming a skill.

| Skill | Purpose |
|-------|---------|
| [`alyf-commit-messages`](alyf-commit-messages/SKILL.md) | Conventional Commits + commitlint + optional Jira keys for ALYF repos |
| [`alyf-frappe-app-ci`](alyf-frappe-app-ci/SKILL.md) | ALYF CI/pre-commit/ruff baseline, four-job linter, Run Tests + smoke test, branch protection; optional release.yaml |
| [`frappe-new-app`](frappe-new-app/SKILL.md) | Interactive `bench new-app` scaffold: AskQuestion, license intent, user-run command, CI nudge |
| [`command-working-directory-selection`](command-working-directory-selection/SKILL.md) | Bench vs app `cd` before shell commands; ambiguity → AskQuestion |
| [`create-skill`](create-skill/SKILL.md) | Author workspace skills; content policy; defers mechanics to Cursor `create-skill` |
| [`frappe-background-jobs`](frappe-background-jobs/SKILL.md) | `frappe.enqueue`, queues, deduplication, Desk RQ Job links, tests |
| [`frappe-backport-merge-conflicts`](frappe-backport-merge-conflicts/SKILL.md) | Backport PR conflicts, bench alignment, locale replay via `po_branch_maps.py` |
| [`frappe-db-permissions`](frappe-db-permissions/SKILL.md) | ORM/db APIs vs default permission enforcement |
| [`frappe-docstrings`](frappe-docstrings/SKILL.md) | Google vs reST docstring style in Frappe apps |
| [`frappe-document-field-changes`](frappe-document-field-changes/SKILL.md) | `has_value_changed`, hook placement, insert vs update |
| [`frappe-form-custom-events`](frappe-form-custom-events/SKILL.md) | Custom form events + `frm.trigger` instead of standalone JS helpers |
| [`frappe-form-defaults-from-settings`](frappe-form-defaults-from-settings/SKILL.md) | Defaults from Single settings on new forms / insert |
| [`frappe-gettext-localization`](frappe-gettext-localization/SKILL.md) | gettext POT/PO/MO, `bench` locale commands, header metadata |
| [`frappe-http-response`](frappe-http-response/SKILL.md) | `frappe.local.response`, API v1/v2, downloads, status codes |
| [`frappe-list-views`](frappe-list-views/SKILL.md) | `*_list.js`, indicators, listview_settings |
| [`frappe-notifications`](frappe-notifications/SKILL.md) | Desk **Notification**, email Jinja, test assertions |
| [`frappe-permissions`](frappe-permissions/SKILL.md) | Permission layers, `has_permission` vs `check_permission`, pitfalls |
| [`frappe-print-formats`](frappe-print-formats/SKILL.md) | Print Format JSON, fixtures, migrate, PDF tests |
| [`frappe-realtime-website`](frappe-realtime-website/SKILL.md) | `publish_realtime`, website JS, boot injection |
| [`frappe-reqd-fields`](frappe-reqd-fields/SKILL.md) | Skip empty checks on mandatory (`reqd`) fields in Desk save hooks |
| [`frappe-testing`](frappe-testing/SKILL.md) | `FrappeTestCase`, `ensure_*` + `atexit`, no `test_records.json` policy |
| [`frappe-web-forms`](frappe-web-forms/SKILL.md) | Web Forms, routes, `get_context`, query-param defaults |
| [`frappe-web-view-templates`](frappe-web-view-templates/SKILL.md) | Has Web View Jinja templates, portal lists |
| [`frappe-whitelist`](frappe-whitelist/SKILL.md) | `@frappe.whitelist` decorator, guest/HTTP/type options, handler security |
| [`prefer-positive-conditions`](prefer-positive-conditions/SKILL.md) | Positive `if` branches over early negation returns when equally clear |
| [`python-postponed-annotations`](python-postponed-annotations/SKILL.md) | Unquoted type hints with `from __future__ import annotations` (UP037) |
| [`draft-github-issue-texts`](draft-github-issue-texts/SKILL.md) | Self-contained issue/FR copy; no private-note / transcript / local-only refs |
| [`github-mcp-issues`](github-mcp-issues/SKILL.md) | GitHub issues via MCP (`issue_write`, `issue_read`, …) |
| [`github-mcp-pull-requests`](github-mcp-pull-requests/SKILL.md) | GitHub PRs via MCP; default base `develop` |

---

## Checklist for a new skill

1. Read [`create-skill`](create-skill/SKILL.md) (workspace policy) and Cursor `~/.cursor/skills-cursor/create-skill/SKILL.md` (mechanics)
2. Copy `_template/SKILL.md` → `.cursor/skills/<skill-id>/SKILL.md`
3. Set `name` and `description` (WHAT + WHEN)
4. Decide `disable-model-invocation` (usually omit)
5. Write **Scope** and core content; add **Related skills**
6. Add row to the inventory table above
7. If `SKILL.md` grows past ~400 lines, move detail to `reference.md` and link it
8. Sanitize: no client/project/person/private-site names — see `create-skill`
