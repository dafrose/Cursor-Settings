---
name: alyf-frappe-app-ci
description: Sets up the standard ALYF GmbH CI / pre-commit / lint baseline for a Frappe Framework app, including pyproject.toml (flit + ruff), .pre-commit-config.yaml (ruff + commitlint), .github/workflows/linter.yml (commitlint, semgrep, pip-audit deps check, pre-commit), ci.yml, release.yaml, and the develop + version-XX branch convention. Use when bootstrapping a new alyf-de Frappe/ERPNext app, forking an external app into the alyf-de org, or aligning an inherited app with ALYF house style. Also covers the "great reformat" pattern when adopting a non-conformant upstream codebase.
---

# ALYF GmbH — Frappe App CI & Linting Baseline

## What ALYF ships in every Frappe app

| File | Purpose | Required? |
| --- | --- | --- |
| `pyproject.toml` | flit-based `[project]` + `[build-system]`, `[tool.bench.frappe-dependencies]`, `[tool.ruff]` config | Yes |
| `.pre-commit-config.yaml` | ruff lint+format, conventional-commit lint, basic hygiene checks | Yes |
| `commitlint.config.mjs` | One-liner that `extends` `@commitlint/config-conventional` so the commitlint hook actually has rules to apply | Yes (whenever `.pre-commit-config.yaml` includes the commitlint hook) |
| `.github/workflows/linter.yml` | PR-time commit-lint + semgrep + **`pip-audit` vulnerable-deps job** + pre-commit | Yes |
| `.github/workflows/ci.yml` | Server tests with MariaDB + Redis, runs `bench --site test_site run-tests --app <app>` | Yes if the app has tests |
| `.github/workflows/release.yaml` | `npx semantic-release` on push to `version-XX`, run as `alyf-linus` bot | Yes for customer-facing apps |
| `.github/workflows/codeql.yml` | GitHub-hosted CodeQL security scan | Recommended |
| `.github/dependabot.yml` | Weekly bumps for `pip` + `github-actions` | Recommended |
| `.github/ISSUE_TEMPLATE/` | Bug + feature templates | Recommended |
| `license.txt` | MIT (default) | Yes |

The newest reference implementation is [`alyf-de/eu_einvoice`](https://github.com/alyf-de/eu_einvoice). Prefer copying from there over older repos like `banking` (which still has v3 actions and prettier/eslint hooks the newer apps dropped).

## Branch convention

Mirror Frappe core: **`develop`** is the default and target of all PRs. Long-lived stable branches are **`version-15`**, **`version-16`**, … — created when a major Frappe version is cut. Tags are cut from the `version-XX` branch, not from `develop`. Older repos use `version-XX-hotfix`; new repos drop the suffix. Customer installs use `bench get-app <url> --branch version-XX`.

## `pyproject.toml` template

Use the flit layout from [`develop/apps/eu_einvoice/pyproject.toml`](develop/apps/eu_einvoice/pyproject.toml). Match `target-version` and `requires-python` to the Frappe version the branch targets:

| Frappe branch | `requires-python` | ruff `target-version` |
| --- | --- | --- |
| `version-14` | `>=3.10` | `py310` |
| `version-15` | `>=3.10` | `py310` |
| `version-16` (when released) | likely `>=3.11` | `py311` |
| `develop` (currently v17) | `>=3.14` | `py314` |

```toml
[project]
name = "<app_name>"
authors = [{ name = "ALYF GmbH", email = "hallo@alyf.de" }]
description = "<one line>"
requires-python = ">=3.10"
readme = "README.md"
license = { text = "MIT" }
dynamic = ["version"]
dependencies = [
    # "frappe~=15.0.0" # Installed and managed by bench.
]

[build-system]
requires = ["flit_core >=3.4,<4"]
build-backend = "flit_core.buildapi"

[tool.bench.frappe-dependencies]
frappe = ">=15.0.0,<16.0.0"

[tool.ruff]
line-length = 110
target-version = "py310"

[tool.ruff.lint]
select = ["F", "E", "W", "I", "UP", "B"]
ignore = [
    "B017", # assertRaises(Exception) - should be more specific
    "B018", # useless expression, not assigned to anything
    "B023", # function doesn't bind loop variable
    "B904", # raise inside except without from
    "E101", # indentation contains mixed spaces and tabs
    "E402", # module level import not at top of file
    "E501", # line too long
    "E741", # ambiguous variable name
    "F401", # "unused" imports
    "F403", # can't detect undefined names from * import
    "F405", # can't detect undefined names from * import
    "F722", # syntax error in forward type annotation
    "W191", # indentation contains tabs
]
typing-modules = ["frappe.types.DF"]

[tool.ruff.format]
quote-style = "double"
indent-style = "tab"
docstring-code-format = true
```

Do **not** invent your own ruff ignore list — the one above is the agreed ALYF set, tuned to Frappe's tabs-and-DF-types conventions. New apps copy it verbatim.

## `.pre-commit-config.yaml` template

```yaml
exclude: "node_modules|.git"
default_stages: [pre-commit]
default_install_hook_types: [pre-commit, commit-msg]
fail_fast: false

repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: trailing-whitespace
        files: "<app_name>.*"
        exclude: ".*json$|.*txt$|.*csv|.*md|.*svg"
      - id: check-yaml
      - id: check-merge-conflict
      - id: check-ast
      - id: check-json
      - id: check-toml
      - id: debug-statements

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.14.13
    hooks:
      - id: ruff
        name: "Run ruff linter and apply fixes"
        args: ["--fix"]
      - id: ruff-format
        name: "Format Python code"

  - repo: https://github.com/alessandrojcm/commitlint-pre-commit-hook
    rev: v9.24.0
    hooks:
      - id: commitlint
        stages: [commit-msg]
        additional_dependencies: ["@commitlint/config-conventional"]

ci:
  autoupdate_schedule: weekly
  skip: []
  submodules: false
```

Add the `mirrors-prettier` and `mirrors-eslint` blocks from `eu_einvoice` only if the app actually ships JS / Vue / SCSS. Apps with no frontend (most server-only integrations) drop them.

`default_install_hook_types: [pre-commit, commit-msg]` is required so a developer's `pre-commit install` also installs the `commit-msg` hook — without it commitlint never runs locally.

## `commitlint.config.mjs` (required alongside the commitlint hook)

The commitlint pre-commit hook only declares `@commitlint/config-conventional` as an additional dependency — it does **not** auto-load it. Without a config file in the repo root, commitlint runs with empty rules and aborts every commit with `[empty-rules]: Please add rules to your commitlint.config.js`, no matter how well-formed the message is. Ship the same one-liner `eu_einvoice` uses, at the repo root:

```js
export default { extends: ["@commitlint/config-conventional"] };
```

Use the `.mjs` extension so Node parses it as ESM (commitlint v18+ default). `commitlint.config.js` (CJS) also works but only if the repo's `package.json` doesn't set `"type": "module"`. When in doubt, prefer `.mjs` — it's unambiguous.

## `.github/workflows/linter.yml` template

Modeled on [`develop/apps/eu_einvoice/.github/workflows/linter.yml`](develop/apps/eu_einvoice/.github/workflows/linter.yml). **Four jobs** on pull requests: semantic commits, Semgrep, **vulnerable dependency check** (`pip-audit`), and pre-commit. The `deps-vulnerable-check` job has **no** `if: github.event_name == 'pull_request'`, so it also runs on **`workflow_dispatch`** (same as eu_einvoice).

```yaml
name: Linters

on:
  workflow_dispatch:
  pull_request:
    paths-ignore:
      - '**.md'
      - '**.html'
      - '**.csv'
      - '**.po'
      - '**.pot'
      - '.editorconfig'
      - '.gitattributes'
      - '.gitignore'
      - 'license.txt'
      - 'README.md'

permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  commit-lint:
    name: 'Semantic Commits'
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v5
        with:
          fetch-depth: 200
      - uses: actions/setup-node@v6
        with:
          node-version: 24
          check-latest: true
      - name: Check commit titles
        run: |
          npm install @commitlint/cli @commitlint/config-conventional
          npx commitlint --verbose --from ${{ github.event.pull_request.base.sha }} --to ${{ github.event.pull_request.head.sha }}

  linter:
    name: 'Semgrep Rules'
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v6
        with:
          python-version: '3.10'  # match pyproject requires-python
          cache: pip
      - name: Download Semgrep rules
        run: git clone --depth 1 https://github.com/frappe/semgrep-rules.git frappe-semgrep-rules
      - name: Run Semgrep rules
        run: |
          pip install semgrep
          semgrep ci --config ./frappe-semgrep-rules/rules --config r/python.lang.correctness

  deps-vulnerable-check:
    name: 'Vulnerable Dependency Check'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/setup-python@v6
        with:
          python-version: '3.10'
      - uses: actions/checkout@v5
      - name: Cache pip
        uses: actions/cache@v5
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/*requirements.txt', '**/pyproject.toml', '**/setup.py', '**/setup.cfg') }}
          restore-keys: |
            ${{ runner.os }}-pip-
            ${{ runner.os }}-
      - name: Install and run pip-audit
        run: |
          pip install pip-audit
          cd "${GITHUB_WORKSPACE}"
          pip-audit --desc on .

  precommit:
    name: 'Pre-Commit'
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v6
        with:
          python-version: '3.10'
          cache: pip
      - uses: pre-commit/action@v3.0.1
```

The filename is **`linter.yml`** in newer apps (eu_einvoice) and **`linters.yaml`** in older ones (banking). Use `linter.yml` for new apps.

### Vulnerable dependency check (`pip-audit`)

- **What it does:** the `deps-vulnerable-check` job installs [`pip-audit`](https://pypi.org/project/pip-audit/) and runs `pip-audit --desc on .` from the repository root. That audits **declared** dependencies (e.g. from `pyproject.toml` / lockfiles pip-audit understands), not the full transitive tree of a running bench unless you point it at a lockfile or requirements export.
- **GitHub check name:** `Linters / Vulnerable Dependency Check` (workflow `name:` + job `name:`). Add it to **branch protection / rulesets** alongside `Linters / Semantic Commits`, `Linters / Semgrep Rules`, and `Linters / Pre-Commit` when you want merges gated on a clean audit.
- **Python version:** keep the job’s `setup-python` version **aligned** with the Semgrep and pre-commit jobs in the same workflow (typically `3.10` for v15-era apps). eu_einvoice uses `3.14` for some jobs; match whatever the rest of `linter.yml` uses for consistency.
- **When it fails:** prefer bumping the affected **direct** pin in `pyproject.toml`, or upgrading Frappe/bench-resolved deps if the finding is real. If you must suppress a known false positive, add a **narrow** `pip-audit --ignore-vuln VULN-ID` (or equivalent) in the workflow step with a one-line comment citing the advisory — avoid blanket ignores.
- **Complements Dependabot:** Dependabot opens upgrade PRs; `pip-audit` fails CI on known CVEs in the current resolution. Both together are better than either alone.

## `.github/workflows/ci.yml` template (server tests)

Modeled on [`develop/apps/eu_einvoice/.github/workflows/ci.yml`](develop/apps/eu_einvoice/.github/workflows/ci.yml). Spins up real MariaDB + Redis, builds a bench, installs the app, runs the suite. Tests must be runnable without external services (mock boto3, HTTP, etc.).

```yaml
name: CI

on:
  workflow_dispatch:
  pull_request:
    paths-ignore:
      - '**.md'
      - '**.html'
      - '**.csv'
      - '**.po'
      - '**.pot'
      - '.editorconfig'
      - '.gitattributes'
      - '.gitignore'
      - '.pre-commit-config.yaml'
      - 'license.txt'
      - 'README.md'
      - '.github/workflows/linter.yml'

concurrency:
  group: develop-<app_name>-${{ github.event.number }}
  cancel-in-progress: true

jobs:
  tests:
    runs-on: ubuntu-latest
    name: Server
    services:
      redis-cache:
        image: redis:alpine
        ports: ['13000:6379']
      redis-queue:
        image: redis:alpine
        ports: ['11000:6379']
      mariadb:
        image: mariadb:11.8
        env:
          MYSQL_ROOT_PASSWORD: root
        ports: ['3306:3306']
        options: --health-cmd="mariadb-admin ping" --health-interval=5s --health-timeout=2s --health-retries=3
    steps:
      - uses: actions/checkout@v6
      - name: Find tests
        run: grep -rn "def test" > /dev/null
      - uses: actions/setup-python@v6
        with:
          python-version: '3.10'
      - uses: actions/setup-node@v6
        with:
          node-version: 24
          check-latest: true
      - uses: actions/cache@v5
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/*requirements.txt', '**/pyproject.toml', '**/setup.py', '**/setup.cfg') }}
      - name: Install MariaDB Client
        run: sudo apt update && sudo apt-get install mariadb-client
      - name: Setup
        run: |
          pip install frappe-bench
          bench init --skip-redis-config-generation --skip-assets --python "$(which python)" ~/frappe-bench
          mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "SET GLOBAL character_set_server = 'utf8mb4'"
          mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "SET GLOBAL collation_server = 'utf8mb4_unicode_ci'"
      - name: Install
        working-directory: /home/runner/frappe-bench
        run: |
          bench get-app --resolve-deps <app_name> $GITHUB_WORKSPACE
          bench setup requirements --dev
          bench new-site --db-root-password root --admin-password admin test_site
          bench --site test_site install-app <app_name>
          bench build
        env:
          CI: 'Yes'
      - name: Run Tests
        working-directory: /home/runner/frappe-bench
        run: |
          bench --site test_site set-config allow_tests true
          bench --site test_site run-tests --app <app_name>
        env:
          TYPE: server
```

Trigger on `push` to `version-XX` as well, on apps that release from a stable branch:

```yaml
on:
  push:
    branches: [develop, version-15]
  pull_request:
    ...
```

## `.github/workflows/release.yaml` template

Semantic-release on push to the active stable branch. Requires the org's `RELEASE_TOKEN` secret and the `alyf-linus` bot identity.

```yaml
name: Generate Semantic Release
on:
  push:
    branches:
      - version-15
jobs:
  release:
    name: Release
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
          persist-credentials: false
      - uses: actions/setup-node@v3
        with:
          node-version: "lts/*"
      - run: npm install @semantic-release/git @semantic-release/exec --no-save
      - name: Create Release
        env:
          GITHUB_TOKEN: ${{ secrets.RELEASE_TOKEN }}
          GIT_AUTHOR_NAME: "alyf-linus"
          GIT_AUTHOR_EMAIL: "136631072+alyf-linus@users.noreply.github.com"
          GIT_COMMITTER_NAME: "alyf-linus"
          GIT_COMMITTER_EMAIL: "136631072+alyf-linus@users.noreply.github.com"
        run: npx semantic-release
```

A matching `.releaserc` (or `release.config.js`) at the repo root tells semantic-release which plugins to use; copy the one from [`alyf-de/banking`](https://github.com/alyf-de/banking) as a starting point.

## Adopting the baseline on an inherited / forked app (the "great reformat")

When you fork an upstream app that does **not** follow ALYF style, doing the lint/format pass naively destroys upstream-merge ergonomics. Recommended sequence:

1. Land the new `pyproject.toml`, `.pre-commit-config.yaml`, `linter.yml` on `develop` in **separate, additive commits** — no Python file touched yet.
2. Run `pre-commit run --all-files`.
3. Commit the resulting whitespace/format diff as a single `chore: apply ruff format and lint to upstream baseline` commit. Push it. **Record the SHA in the README** (e.g. in a "Changes vs. upstream" section), so future merges from upstream can use `git diff <SHA>..HEAD -- <path>` to isolate semantic deltas from formatting.
4. Use `git merge -X ignore-all-space` (and let `git rerere` learn the resolution) when pulling upstream into `develop` afterwards. Or do a single squashed merge commit per upstream sync with a conventional message like `chore: rebase from upstream@<sha>`.
5. Cherry-pick the format commit into `version-XX` and re-tag, so customers on the stable line also get the formatted base.

Commitlint will reject upstream's non-conventional commits if you ever surface them in a PR. The squashed-merge pattern above keeps the PR's commit range fully conventional.

## Dependabot + CodeQL (recommended add-ons)

`.github/dependabot.yml`:

```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

`.github/workflows/codeql.yml`: use the GitHub-suggested template for Python; no ALYF-specific tweaks.

## Setup checklist for a new (or newly-adopted) alyf-de Frappe app

- [ ] `pyproject.toml` migrated to flit `[project]` + `[build-system]`, ALYF ruff config in place, `target-version` / `requires-python` matching the branch
- [ ] `.pre-commit-config.yaml` from template, `<app_name>.*` substituted, JS hooks dropped if no frontend
- [ ] `commitlint.config.mjs` at repo root extending `@commitlint/config-conventional` (skipping it is the most common cause of the `[empty-rules]` commit-msg failure)
- [ ] `.github/workflows/linter.yml` (commit-lint + semgrep + **`deps-vulnerable-check` / `pip-audit`** + pre-commit)
- [ ] `.github/workflows/ci.yml` if app has tests; uses bench services and `--resolve-deps`
- [ ] `.github/workflows/release.yaml` triggered on the active `version-XX` branch; `RELEASE_TOKEN` secret confirmed in repo settings
- [ ] `.github/dependabot.yml` for `pip` and `github-actions`
- [ ] `.github/workflows/codeql.yml` (optional but recommended)
- [ ] Default branch set to `develop`; `version-XX` branches created and protected (require PR + green CI)
- [ ] `master` deleted **only after** confirming no external bench installs reference it
- [ ] If forking from non-ALYF code: one-time `chore: apply ruff format and lint to upstream baseline` commit, SHA recorded in README "Changes vs. upstream"
