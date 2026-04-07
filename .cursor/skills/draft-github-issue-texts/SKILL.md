---
name: draft-github-issue-texts
description: >-
  Drafts self-contained GitHub issue bodies and titles for implementers who
  only see the tracker. Forbids offline-only references (private notes, transcripts,
  local paths, unmerged spike scripts). Requires public URLs or inlined facts.
  Use when the user asks to write, draft, or refine issue text, feature
  requests, or bug reports before filing via GitHub MCP or the web UI.
disable-model-invocation: true
---

# Draft GitHub issue texts

## Scope

Use when the user wants **issue copy** (title + body) ready to paste or file with **`github-mcp-issues`**. Applies to any repo; common targets are Frappe app repos under the user's org.

**Not in scope:** filing the issue (see **github-mcp-issues**), PR descriptions (**github-mcp-pull-requests**), commit messages (**alyf-commit-messages**), or long-term knowledge in private notes / wikis.

## Core rule: self-contained for the tracker audience

The reader is a **contributor or maintainer who only has the GitHub issue** (and the public repo). They must be able to understand the problem, the intended solution, and how to verify it **without** private notes, local wikis, or conversation history.

**Offline-only knowledge is invalid in issue text.** If a fact exists only in private notes, agent transcripts, or a local spike run, either:

1. **Inline** the fact in the issue (concise, factual), or  
2. **Cite** a **public** source (normative spec, upstream doc, merged code on the default branch, another GitHub issue/PR with full URL), or  
3. **Omit** it.

Do not tell the reader to “see our private wiki”, “spike step N”, “internal MOC”, or “ask a maintainer offline”.

## Forbidden references (treat as invalid)

| Do not use | Why |
| ---------- | --- |
| Private wiki / Obsidian paths, `[[wikilinks]]`, “permanent note X” | Not on GitHub |
| Agent transcript IDs or “as discussed in chat” | Not on GitHub |
| Local machine paths (`/Users/…`, `~/verapdf/…`) | Not reproducible |
| Private site names, internal bench labels | Use generic “Frappe site” or omit |
| Unmerged or local-only scripts/tests | Reader cannot run them |
| “Spike proved …” without inlined outcome | Spike is offline unless published |
| Vague “see documentation” without URL | Not self-contained |

## Allowed references

| Use | How |
| --- | --- |
| **Related GitHub issues/PRs** | Full URL: `https://github.com/<owner>/<repo>/issues/<n>` |
| **Normative / vendor docs** | Full `https://` URL + short label (what the link establishes) |
| **PyPI / upstream source** | Full URL (e.g. project README on GitHub) |
| **In-repo symbols** | Path relative to repo root **after merge** (e.g. `my_app/.../sales_invoice.py`) plus function name; prefer linking via `https://github.com/<owner>/<repo>/blob/<default-branch>/...` when helpful |
| **README / docs in repo** | Path or blob URL on default branch |
| **Jira / internal keys** | Only if the user explicitly wants them; prefer `Ref: KEY` in body, not as sole spec |

When the user’s source material is offline-only, **rewrite**: extract requirements and decisions into the issue; do not link private notes.

## Workflow

1. **Clarify target** — `owner/repo`, issue type (feature / bug / chore), optional parent issue URL, repo issue template (if any).
2. **Gather facts** — from user message, **public** GitHub issues, merged code, README. Use offline notes only as **input** to you; output must not depend on them.
3. **Draft** — title + body using the template below (or the repo’s template).
4. **Self-check** (required before delivering):

   - [ ] Problem and solution understandable with **zero** private-note / transcript access  
   - [ ] Every external claim has a **URL** or is **inlined**  
   - [ ] No wikilinks, private note paths, or “step N” without explanation  
   - [ ] Acceptance criteria are testable from the issue text alone  
   - [ ] No private site names or local paths  
   - [ ] Related work linked with **full GitHub URLs**  
   - [ ] Frappe terms follow **Frappe Markdown** (bold **DocType**, _field labels_, `field_name`)

5. **Deliver** — paste-ready markdown; suggest labels/milestone only if the user asked. File via **github-mcp-issues** only when requested.

## Default body structure

Adapt to the repo template. When the repo uses a four-section feature-request form, mirror those headings:

```markdown
**Is your feature request related to a problem? Please describe.**
…

**Describe the solution you'd like**
…

**Describe alternatives you've considered**
…

**Additional context**
…
```

For other repos, prefer:

```markdown
## Summary
One paragraph: what and why.

## Requirements
Numbered, testable bullets.

## Acceptance criteria
- [ ] …

## Out of scope
…

## References
- [Label](https://full-url) — what this source supports
```

Keep issues **concise** unless the user asks for depth; put optional tables in **Alternatives** or **Additional context**.

## Title line

- Imperative, specific, ≤ ~72 characters when possible  
- Many Frappe app repos use plain English: `Feature: …`, `Fix: …`  
- Do not encode offline-only IDs in the title (private note names, spike codenames)

## Cross-repo features

- State **which repo owns** schema vs hook vs UI  
- Link parent/coordination issue on the other repo with full URL  
- Do not assume the reader has both checkouts

## Related skills

- [`github-mcp-issues`](github-mcp-issues/SKILL.md) — create/update issues after copy is approved  
- [`github-mcp-pull-requests`](github-mcp-pull-requests/SKILL.md) — PR bodies (same self-contained rules apply)  
- [`alyf-commit-messages`](alyf-commit-messages/SKILL.md) — commit subject format, not issue format

## Additional resources

- [reference.md](reference.md) — bad vs good examples, checklist expansion
