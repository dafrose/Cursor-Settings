---
name: alyf-frappe-app-ci
description: >-
  Sets up the standard ALYF GmbH CI / pre-commit / lint baseline for a Frappe
  Framework app, including pyproject.toml (flit + ruff), .pre-commit-config.yaml
  (ruff + commitlint + optional JS hooks), .github/workflows/linter.yml (commitlint,
  Frappe semgrep, pip-audit, pre-commit), ci.yml with Run Tests, and the develop +
  version-XX branch convention. Use when bootstrapping a new alyf-de Frappe app,
  aligning CI after frappe-new-app, forking into the alyf-de org, or adopting the
  baseline on inherited code. Optional add-on: release.yaml (semantic-release).
---

# ALYF Frappe app CI and linting

## Scope

Use when bootstrapping or aligning an **alyf-de** Frappe app with the shared CI,
pre-commit, ruff, and GitHub Actions baseline. Covers branch convention (`develop`
+ `version-XX`), required workflow files, bootstrap smoke tests, and the one-time
"great reformat" when forking non-ALYF upstream code.

Not for: customer org license or release policy (adapt templates locally),
day-to-day commit wording (**alyf-commit-messages**), app scaffolding prompts
(**frappe-new-app**), or opening PRs via MCP (**github-mcp-pull-requests**).

## What ALYF ships in every Frappe app

| File | Purpose | Required? |
| --- | --- | --- |
| `pyproject.toml` | flit `[project]` + `[build-system]`, `[tool.bench.frappe-dependencies]`, ALYF `[tool.ruff]` | Yes |
| `commitlint.config.mjs` | `extends: @commitlint/config-conventional` — without it the commit-msg hook fails with `[empty-rules]` | Yes |
| `.pre-commit-config.yaml` | ruff `--fix` + format, commitlint, hygiene hooks; prettier + eslint when the app ships or will ship Desk JS | Yes |
| `eslint.config.mjs` | Flat config for eslint v9 pre-commit hook | Yes when eslint hook is present |
| `.github/workflows/linter.yml` | Four PR jobs: semantic commits, **Frappe semgrep**, pip-audit, pre-commit | Yes |
| `.github/workflows/ci.yml` | Bench install + **`bench run-tests --app <app>`** (MariaDB utf8mb4, `--resolve-deps`) | Yes |
| `license.txt` | MIT (default for alyf-de public apps) | Yes |
| `.github/dependabot.yml` | Monthly `pip` + `github-actions` bumps | Recommended |
| `.github/workflows/codeql.yml` | Python + JavaScript security scan; `push` limited to `develop` | Recommended |
| `.github/ISSUE_TEMPLATE/` | Bug + feature templates | Recommended |
| `.github/workflows/release.yaml` | `semantic-release` on push to `version-XX` via release bot | **Optional** — customer-facing alyf-de apps with `RELEASE_TOKEN` |

Copy templates from [reference.md](reference.md). Prefer those defaults over literal copies of older repo files.

**Reference repos:** Use an existing **alyf-de** app in the org for structure (full ERPNext dependency pins vs frappe-only `pyproject.toml`). Do **not** copy legacy CI gaps from older repos blindly — follow this skill's defaults.

## Defaults chosen for new apps (2026 baseline)

| Area | Default |
| --- | --- |
| **GitHub Actions** | `actions/checkout@v6`, `actions/cache@v5`, `pre-commit/action@v3.0.1`, Python/Node versions matching the Frappe branch (3.14 / 24 on v16) |
| **Linter workflow** | Four separate jobs; Frappe rules from [`frappe/semgrep-rules`](https://github.com/frappe/semgrep-rules) + `r/python.lang.correctness` |
| **CI triggers** | `pull_request` + `workflow_dispatch` only — not `push` to `develop` |
| **Dependabot** | Monthly `pip` + `github-actions` update PRs |
| **CodeQL triggers** | `pull_request`, `push` to `develop` only, weekly schedule |
| **CI install** | `bench get-app --resolve-deps` using `[tool.bench.frappe-dependencies]` |
| **MariaDB** | After `bench init`, `SET GLOBAL character_set_server/collation_server` to utf8mb4 **before** `bench new-site` |
| **Tests in CI** | **`Run Tests` enabled** — ship a bootstrap `UnitTestCase` smoke test so `grep def test` and `run-tests` pass from day one |
| **Pre-commit JS** | Include prettier v3 + eslint v9 hooks for typical Desk apps; drop only for server-only integrations with no JS |
| **Initial commit** | One conventional commit for the full CI bootstrap on a greenfield app, e.g. `ci: align pre-commit, workflows, and smoke test with ALYF baseline` |
| **Branch protection** | After first green PR: require Linters (4 checks) + `CI / Server` + CodeQL when present — see [reference.md](reference.md) |

**Legacy note:** Some older org repos still have **`Run Tests` commented out** or mix `checkout@v5`/`@v6`. New apps follow this skill's defaults, not that legacy state.

## Branch convention

Mirror Frappe core: **`develop`** is the default and target of all PRs. Long-lived stable branches are **`version-15`**, **`version-16`**, … Tags are cut from the `version-XX` branch, not from `develop`. Customer installs use `bench get-app <url> --branch version-XX`.

## Config templates

Copy from [reference.md](reference.md) unless the app documents an exception:

- `pyproject.toml`, `commitlint.config.mjs`, `.pre-commit-config.yaml`, `eslint.config.mjs` (when using eslint)
- `.github/workflows/linter.yml`, `ci.yml`
- Recommended: `dependabot.yml`, `codeql.yml`, `ISSUE_TEMPLATE/`
- Optional: `release.yaml` + `.releaserc` (semantic-release)

Match `requires-python`, ruff `target-version`, workflow Python version, and `[tool.bench.frappe-dependencies]` to the Frappe branch (table in reference).

## Bootstrap smoke test

Greenfield apps include `<app_package>/tests/test_smoke.py` — a `UnitTestCase` asserting `hooks.app_name` — so CI's **Find tests** step and **`bench run-tests`** succeed before feature tests exist. See [reference.md](reference.md) and **frappe-testing**.

## Adopting the baseline on inherited / forked code ("great reformat")

When merging ALYF CI into an upstream fork, use **separate commits** (config first, then one `chore: apply ruff format and lint to upstream baseline` commit). Record the format SHA in README for future upstream merges. Do **not** use the single-commit bootstrap pattern — that is for greenfield apps only.

## Optional add-on: semantic release

For customer-facing alyf-de apps that tag from `version-XX`: add `.github/workflows/release.yaml` and `.releaserc`, configure the org `RELEASE_TOKEN` secret and release-bot git identity. Template in [reference.md](reference.md). Skip until release automation is agreed.

## Setup checklist

- [ ] `pyproject.toml`: flit layout, ALYF ruff config, `[tool.bench.frappe-dependencies]` for the target Frappe major
- [ ] `commitlint.config.mjs` at repo root
- [ ] `.pre-commit-config.yaml`: ruff v0.14.13, commitlint, `default_install_hook_types: [pre-commit, commit-msg]`; prettier/eslint unless server-only
- [ ] `eslint.config.mjs` when eslint hook is present (not `.eslintrc`)
- [ ] `.github/workflows/linter.yml`: four jobs, `checkout@v6`, semgrep + pip-audit + pre-commit
- [ ] `.github/workflows/ci.yml`: `--resolve-deps`, utf8mb4 MariaDB, **Run Tests** enabled
- [ ] Bootstrap smoke test under `<app_package>/tests/`
- [ ] `.github/dependabot.yml` and `.github/workflows/codeql.yml` (recommended)
- [ ] `.github/ISSUE_TEMPLATE/` (recommended)
- [ ] Default branch `develop`; branch protection after first green CI (reference)
- [ ] `release.yaml` only when semantic-release is in scope (optional)
- [ ] Inherited upstream: great-reformat sequence instead of single bootstrap commit

## Related skills

- [`frappe-new-app`](frappe-new-app/SKILL.md) — scaffold prompts; nudge CI setup after `bench new-app`
- [`alyf-commit-messages`](alyf-commit-messages/SKILL.md) — Conventional Commits enforced by commitlint
- [`frappe-testing`](frappe-testing/SKILL.md) — smoke test and suite patterns
- [`github-mcp-pull-requests`](github-mcp-pull-requests/SKILL.md) — open PRs against `develop` by default

## Additional resources

- [reference.md](reference.md) — full copy-paste templates and branch protection table
