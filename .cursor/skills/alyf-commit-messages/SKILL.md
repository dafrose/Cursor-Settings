---
name: alyf-commit-messages
description: >-
  Drafts git commit messages for ALYF repos that pass Conventional Commits and
  commitlint (@commitlint/config-conventional). Covers subject format, body
  line length, footer rules, and optional Jira key placement. Use when writing
  or revising commit messages, “generate commit message”, pre-commit
  commitlint failures, or ALYF PR commit history hygiene.
disable-model-invocation: true
---

# ALYF — commit messages (Conventional Commits + commitlint)

## When this applies

Use for any commit message that must pass **commitlint** in ALYF Frappe apps and sibling repos where `commitlint.config.mjs` extends `@commitlint/config-conventional` (no local overrides). If a repository overrides rules in `commitlint.config.mjs`, follow that file instead of the defaults below.

## Before drafting: Jira issue key (required step)

**Use the AskQuestion tool** (or ask in chat if AskQuestion is unavailable) so the user picks how to reference a Jira ticket, if at all:

| User choice | Result |
| --- | --- |
| No ticket reference | Subject + body without any issue key |
| In the **subject** | Append the key in parentheses after the description: `(XYZ-123)`. Example: `fix(invoicing): handle empty tax id (EU-42)` |
| In the **body** | Add a line (typically near the top of the body or with other references): `Ref: XYZ-123` |

Do **not** assume a ticket key from branch name or context unless the user confirmed one of the above. If they choose title placement, keep the **entire subject line** within the header length limit (see below).

## Subject line (header)

Format:

```text
<type>[optional scope]: <description>
```

Rules:

- Use a valid Conventional Commits **type** (for example: `feat`, `fix`, `docs`, `refactor`, `test`, `ci`, `chore`, `perf`, `build`, `style`, `revert`).
- **Scope** is optional; when present, use **lowercase**.
- **Description**: imperative mood, **lowercase**, no trailing period.
- Use exactly one **`:`** then a **space** after the type (and scope): `: ` — not `:` glued to the description.
- Do not end the subject with a period.

## Body and footer (commitlint defaults)

ALYF’s standard preset is **`@commitlint/config-conventional`** with default limits:

| Rule | Requirement |
| --- | --- |
| **Header max length** | Whole first line ≤ **100** characters (includes scope, Jira suffix in title if used). |
| **Body line length** | Each body line ≤ **100** characters; wrap prose manually. |
| **Blank line after subject** | One empty line between subject and body. |
| **Footer** | If you use footers (`BREAKING CHANGE:`, `Reviewed-by:`, etc.), separate them from the body with a blank line; footer lines also respect typical line-length behavior — keep footer lines ≤ **100** characters. |

Write the body in **complete sentences** where it helps (ALYF preference: clear PR-style prose, not keyword dumps). Explain *what* changed and *why* when non-obvious.

## Self-check before sending the message to the user

1. Subject matches `<type>[scope]: <description>` and commitlint header rules.
2. No trailing period on the subject; scope lowercase if present.
3. Blank line between subject and body when a body exists.
4. No body or footer line exceeds **100** characters.
5. Jira placement matches the user’s AskQuestion answer (`(KEY)` in subject vs `Ref: KEY` in body vs none).

## Examples

**Minimal fix, no ticket, no body**

```text
fix(api): return 404 for missing document
```

**Ticket in subject**

```text
feat(einvoice): add peppol endpoint discovery (EU-123)
```

**Ticket in body**

```text
fix(einvoice): validate schematron before upload

Ref: EU-123

Previously invalid XML could be sent and rejected only downstream.
```

## Privacy

Do not put internal site names, customer identifiers, or private paths in commit text. Ticket keys and product-level summaries are fine.
