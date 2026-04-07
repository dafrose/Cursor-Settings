---
name: create-skill
description: >-
  Authors new Agent Skills under .cursor/skills/ in this workspace: defers file
  structure and authoring mechanics to Cursor's create-skill skill, and enforces
  what content belongs in project skills vs rules or app docs. Use when
  adding, splitting, or reviewing a workspace skill, or when the user asks what
  may go in a skill.
disable-model-invocation: true
---

# Create a workspace skill

## Scope

Use when adding or revising a skill under **`.cursor/skills/`** in this workspace.

**Mechanics first:** read Cursor's built-in skill **`create-skill`** (`~/.cursor/skills-cursor/create-skill/SKILL.md`) for directory layout, frontmatter, descriptions, progressive disclosure, scripts, and the authoring checklist. This skill adds **workspace placement** and **content policy** only — do not duplicate that file.

**Not in scope:** personal skills (`~/.cursor/skills/`), Cursor built-ins (`~/.cursor/skills-cursor/`), `.cursor/rules/`, or app `README` / upstream Frappe docs.

## Where skills live

| Location | Use for |
| -------- | ------- |
| `.cursor/skills/<skill-id>/SKILL.md` | **This workspace** — shared Frappe / house workflows |
| `~/.cursor/skills/` | Personal skills across all projects |
| `~/.cursor/skills-cursor/` | **Cursor-managed only** — never write here |
| `.cursor/rules/*.mdc` | Short always-on or requestable reminders that point at skills |

Start from [`.cursor/skills/_template/SKILL.md`](../_template/SKILL.md). Register new skills in [`.cursor/skills/README.md`](../README.md) inventory.

Naming: `{domain}-{topic}` — `frappe-*`, `alyf-*`, `github-mcp-*`, or meta names like `create-skill`. Folder name must match frontmatter `name`.

## When to add a workspace skill

Add when knowledge is **stable**, **non-obvious**, and **repeated** (see [README](../README.md)). Skip one-off tasks and anything generic agents already know from official Frappe docs.

Prefer a **rule** (one paragraph + skill link) when a single constraint must be always visible. Put project research, roadmaps, and “why we decided X” in **private notes or wikis outside this repo** — not in `.cursor/skills/`.

## Allowed content

| Category | OK in `.cursor/skills/` | Notes |
| -------- | ------------------------ | ----- |
| Frappe Framework APIs, hooks, Desk behaviour | Yes | Link [Frappe docs](https://docs.frappe.io) for reference; skill = pitfalls and house workflow |
| Frappe core apps (**ERPNext**, **HRMS**, **Print Designer**, …) | Yes | As ecosystem examples |
| House workflows | Yes | `bench` sequences, AskQuestion gates, MCP tool choice |
| Org policy (`alyf-*` skills) | Yes | ALYF CI, commitlint, branch conventions — org is the subject |
| ALYF-published apps | Occasionally | Reference repos in `alyf-*` skills only when illustrating org baseline |
| Generic examples | Yes | `my_app`, `<my_app>`, `<site.name>`, `Example Corp GmbH`, `owner/repo`, `issue-{n}` |
| Placeholders to enquire about | Yes | Document that AskQuestion must resolve them (see `frappe-backport-merge-conflicts`) |
| Sibling skills and rules | Yes | Link, do not copy long rule bodies |
| `.cursor/scripts/` | Yes | Point to script path; keep script generic |

Use **Frappe Markdown** in prose: bold **DocType**, _field labels_, `` `field_name` ``.

## Forbidden content

Do **not** put the following in workspace skills (use generic placeholders or move elsewhere):

| Do not include | Why | Put it instead |
| -------------- | --- | -------------- |
| Client / customer company names | Not portable; leaks context into PRs | Generic org name or `<publisher>` |
| Named people | Privacy; stale quickly | “maintainer”, “user”, AskQuestion |
| Customer-specific apps as standing examples | Ties skill to one engagement | `my_app`, `consumer_app` |
| Private site or bench hostnames | Not reproducible | `<site.name>`, `<bench-root>` |
| Local user paths (`/Users/…`) | Not reproducible | `<workspace>`, `<bench-root>` |
| Live issue / PR / Jira ids as permanent examples | Becomes wrong | `issue-{n}`, `pr-{n}`, or ask user |
| Private wiki paths, `[[wikilinks]]`, offline note titles | Wrong medium for Cursor skills | Private notes / wikis outside `.cursor/` |
| Project roadmaps and “why we decided X” | Too project-specific; drifts | Private notes; milestone planning → rule *milestone-phase-planning* |
| Agent transcript ids, “as discussed in chat” | Ephemeral | Inline the fact in the skill or omit |
| Secrets, tokens, emails, internal URLs | Security | Describe setup steps; use placeholders |
| Full duplication of a workspace rule | Drifts | Rule + one-line reminder → skill |
| Generic Frappe tutorials | Wastes context | Official docs |

**Exception:** `alyf-commit-messages` and `alyf-frappe-app-ci` may name ALYF / `alyf-de` because the skill *is* org policy.

**Planning:** milestone / phase breakdown is **not** a workspace skill — use requestable rule *milestone-phase-planning* (do not re-home it under `.cursor/skills/`).

## Workflow

1. Read Cursor **`create-skill`** — confirm purpose, triggers, and structure.
2. Decide **workspace skill vs rule vs private notes** using tables above.
3. Copy **`_template/SKILL.md`** → `.cursor/skills/<skill-id>/SKILL.md`.
4. Write **`## Scope`** (required) and body; split to `reference.md` if > ~400 lines.
5. Set **`disable-model-invocation: true`** for narrow procedural or policy-only skills (see [README](../README.md)).
6. Add **Related skills** links; add inventory row in [README](../README.md).
7. **Sanitize pass:** replace any client/project/person/site names with placeholders; keep only allowed categories.

## Self-check before merge

- [ ] Follows Cursor `create-skill` structure and description (WHAT + WHEN, third person)
- [ ] `name` matches directory; under 300 lines in `SKILL.md` (or split reference)
- [ ] No forbidden names (clients, people, private sites, offline wikilinks, live ticket ids)
- [ ] Examples use generic placeholders where values vary per task
- [ ] Does not duplicate a rule or long private note — links to rules instead
- [ ] README inventory updated

## Related skills

- Cursor built-in **`create-skill`** — `~/.cursor/skills-cursor/create-skill/SKILL.md` (authoring mechanics)
- [`draft-github-issue-texts`](draft-github-issue-texts/SKILL.md) — same “no offline-only refs” bar for GitHub copy
- Rule *milestone-phase-planning* — milestone / phase planning (not a workspace skill)

## Additional resources

- [`.cursor/skills/README.md`](../README.md) — archetypes, frontmatter, inventory
- [`_template/SKILL.md`](../_template/SKILL.md) — starter skeleton
