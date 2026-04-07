---
name: frappe-new-app
description: >-
  Guides interactive scaffolding of a new Frappe app via bench new-app: discovers
  benches, uses AskQuestion to collect app metadata, license intent, git/CI
  choices, prints the exact command for the user to run, applies proprietary
  license defaults after scaffold when needed, and nudges CI setup next. Use when
  creating a new Frappe app, running bench new-app, bootstrapping an app repo, or
  replacing MIT scaffold license with proprietary text.
---

# Frappe new-app — scaffold a Frappe application

## Scope

Use when the user wants a **new Frappe app** on an existing bench (`bench new-app`).
Covers interactive input gathering, license clarification (open source vs proprietary),
printing the scaffold command for **the user to run**, post-scaffold license fixes,
and pointing to CI setup next.

**Do not** run `bench new-app` yourself — the interactive prompts must happen in the
user's terminal.

Defer to [`alyf-frappe-app-ci`](alyf-frappe-app-ci/SKILL.md) for GitHub Actions /
pre-commit alignment after scaffold. Defer to [`command-working-directory-selection`](command-working-directory-selection/SKILL.md) for bench vs app `cd` on later commands.

## Prerequisites

- An existing bench with **frappe** installed (`apps/frappe` present).
- **App name** in snake_case (CLI argument to `bench new-app`); derive a default
  _App Title_ from it unless the user overrides.

## AskQuestion policy

**Skip AskQuestion** only when the user's message already states a value unambiguously
(same turn as invoking this workflow).

Use **AskQuestion** for every choice that fits a short option list. Use **normal chat**
for free-text only when the user picks **Other** or a value cannot be enumerated.

**Clarify until complete:** if license intent, publisher, or email remain ambiguous,
ask again before printing the final command. Do not print the command with TBD placeholders.

## Phase 0 — Bench

1. Discover bench roots (directories containing `apps/frappe`). Typical layout:
   `<workspace>/version-15`, `<workspace>/version-16`.
2. **AskQuestion — Bench:** one option per candidate (label: folder name; id: absolute bench root).
3. If the chosen bench is ambiguous, stop and ask — do not guess.

Detect the frappe branch for later defaults:

```bash
git -C "<bench-root>/apps/frappe" branch --show-current
```

## Phase 1 — App identity

Collect (AskQuestion + chat as needed):

| Field | Maps to scaffold prompt | Default / rule |
| --- | --- | --- |
| **App name** | CLI argument | snake_case; from user or project context |
| **App Title** | `App Title` | `app_name.replace("_", " ").title()` |
| **App Description** | `App Description` | One line; verb-led (e.g. "European e-invoicing for ERPNext") |
| **App Publisher** | `App Publisher` | Company / org name |
| **App Email** | `App Email` | Valid email for publisher |

If description or publisher is missing, ask before continuing.

## Phase 2 — License intent (clarify loop)

`bench new-app` offers SPDX open-source licenses from GitHub's API (e.g. `mit`,
`apache-2.0`, `gpl-3.0`, `agpl-3.0`, …). **None of these declare proprietary /
closed-source.** Handle intent explicitly:

### Step 2a — Intent

**AskQuestion — License intent:**

- **Open source (Recommended for alyf-de public apps)** — permissive or copyleft OSS
- **Proprietary / closed** — customer or internal; not OSS
- **Not sure yet** — agent explains tradeoffs briefly, then re-ask Step 2a

Repeat Step 2a until intent is **Open source** or **Proprietary**. Do not proceed with
"Not sure yet".

### Step 2b — Scaffold choice (based on intent)

**Open source** — **AskQuestion — App License** with options informed by prior input:

| Context | Suggest first (Recommended) |
| --- | --- |
| ALYF / alyf-de house app, Frappe ecosystem default | `mit` |
| Patent / explicit grant concerns, still permissive | `apache-2.0` |
| Copyleft, same license for derivatives | `gpl-3.0` |
| Network copyleft (SaaS trigger) | `agpl-3.0` |
| User named another SPDX id | that id as **Other** follow-up |

Always include **Other** → ask for exact SPDX id in chat.

**Proprietary** — explain and confirm:

1. At the scaffold prompt, pick **`mit`** (or any listed license) **only as a
   placeholder** to finish `bench new-app`.
2. **Immediately after scaffold** (before first commit / push), replace license files
   with the proprietary defaults in [reference.md](reference.md).
3. Optionally **AskQuestion — Apply proprietary license now?**
   - **Yes** — agent edits files per reference (user must confirm scaffold finished)
   - **No** — user applies manually; agent still prints the checklist

Re-ask if the user tries to pick `agpl-3.0` / `gpl-3.0` for a proprietary app without
acknowledging the placeholder overwrite step.

## Phase 3 — Remaining scaffold options

**AskQuestion** when not already given:

| Prompt | Maps to | Default |
| --- | --- | --- |
| Create GitHub Workflow action for unittests? | `create_github_workflow` | **No** — Frappe stock workflow; ALYF apps usually align via **alyf-frappe-app-ci** instead |
| Branch Name | `branch_name` | current frappe branch on bench (Phase 0) |
| Initialize git? | `--no-git` flag | **Yes** init git (omit `--no-git`) unless user wants no git |

## Phase 4 — Print command (user runs)

Summarize all collected values in a short table, then print **one exact command** for
the user to copy into their terminal.

```bash
cd "<bench-root>" && bench new-app <app_name> [--no-git]
```

Tell the user what to answer at each interactive prompt (title, description,
publisher, email, license, GitHub workflow, branch) using the collected values.

**Do not** run this command. **Do not** use `bench new-app --help` as a substitute for
the interactive wizard.

### Prompt cheat sheet

| Scaffold prompt | User should enter |
| --- | --- |
| App Title | collected title |
| App Description | collected description |
| App Publisher | collected publisher |
| App Email | collected email |
| App License | collected SPDX id (or `mit` placeholder if proprietary) |
| Create GitHub Workflow… | Yes/No per Phase 3 |
| Branch Name | collected branch |

## Phase 5 — After scaffold

When the user confirms scaffolding finished:

1. **Proprietary intent** — apply or verify [proprietary license defaults](reference.md).
2. Confirm `apps/<app_name>/` exists under the bench (user can `ls` — agent may verify
   only if asked).
3. **CI next step** — tell the user to consider CI pipelines:
   - **alyf-de / ALYF house apps:** follow [`alyf-frappe-app-ci`](alyf-frappe-app-ci/SKILL.md)
     (pre-commit, `linter.yml`, `ci.yml`, `develop` + `version-XX` branches).
   - **Customer org apps:** confirm org CI expectations; the ALYF baseline is a
     sensible starting point but license and release workflow may differ (no
     `release.yaml` until agreed).
   - Stock Frappe scaffold may already include basic `.github/workflows/` if they
     answered Yes to GitHub Workflow — still review against house style.

Use **AskQuestion — Set up CI next?** when appropriate: **Yes (alyf-frappe-app-ci)** /
**Later** / **Not needed**.

## Pitfalls

- Picking **mit** (or any OSS license) for a proprietary app and **committing without
  overwrite** — grants open-source rights.
- Running **`bench new-app` in the agent shell** — steals interactive prompts from the user.
- **`agpl-3.0` / `gpl-3.0`** for proprietary apps — wrong at scaffold *and* after overwrite
  unless legal explicitly wants copyleft OSS.
- Skipping **email validation** — scaffold rejects invalid addresses.
- App folder already exists — ask **Skip** vs **Remove / new name** before printing command.

## Related skills

- [`alyf-frappe-app-ci`](alyf-frappe-app-ci/SKILL.md) — CI / pre-commit baseline after scaffold
- [`command-working-directory-selection`](command-working-directory-selection/SKILL.md) — bench vs app `cd`
- [`alyf-commit-messages`](alyf-commit-messages/SKILL.md) — first commit subject after scaffold

## Additional resources

- [reference.md](reference.md) — proprietary license template, post-scaffold file checklist
