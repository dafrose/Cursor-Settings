# alyf-frappe-app-ci — reference

Copy-paste templates for ALYF Frappe app CI. See [SKILL.md](SKILL.md) for scope, checklist, and policy.

## GitHub Actions version pins (defaults)

| Action | Version |
| --- | --- |
| `actions/checkout` | `@v6` |
| `actions/cache` | `@v5` |
| `actions/setup-python` | `@v6` |
| `actions/setup-node` | `@v6` |
| `pre-commit/action` | `@v3.0.1` |

Match `python-version` in workflows to `requires-python` in `pyproject.toml`.

## `pyproject.toml` template

Match `target-version`, `requires-python`, and `[tool.bench.frappe-dependencies]` to the Frappe branch:

| Frappe branch | `requires-python` | ruff `target-version` | `frappe` pin (example) |
| --- | --- | --- | --- |
| `version-15` | `>=3.10` | `py310` | `>=15.0.0,<16.0.0` |
| `version-16` | `>=3.14` | `py314` | `>=16.0.0,<17.0.0` |
| `develop` (v17+) | `>=3.14` | `py314` | align with active develop |

Add `erpnext` (and other apps) under `[tool.bench.frappe-dependencies]` only when the app depends on them.

```toml
[project]
name = "<app_name>"
authors = [{ name = "ALYF GmbH", email = "hallo@alyf.de" }]
description = "<one line>"
requires-python = ">=3.14"
readme = "README.md"
license = { text = "MIT" }
dynamic = ["version"]
dependencies = [
    # "frappe~=16.0.0" # Installed and managed by bench.
]

[build-system]
requires = ["flit_core >=3.4,<4"]
build-backend = "flit_core.buildapi"

[tool.bench.frappe-dependencies]
frappe = ">=16.0.0,<17.0.0"

[tool.ruff]
line-length = 110
target-version = "py314"

[tool.ruff.lint]
select = ["F", "E", "W", "I", "UP", "B", "RUF"]
ignore = [
    "B017",
    "B018",
    "B023",
    "B904",
    "E101",
    "E402",
    "E501",
    "E741",
    "F401",
    "F403",
    "F405",
    "F722",
    "W191",
    "UP030",
    "UP031",
    "UP032",
    "UP037",
    "UP040",
]
typing-modules = ["frappe.types.DF"]

[tool.ruff.format]
quote-style = "double"
indent-style = "tab"
docstring-code-format = true
```

Copy the ignore list verbatim — do not invent your own.

## `commitlint.config.mjs`

```js
export default { extends: ["@commitlint/config-conventional"] };
```

## `.pre-commit-config.yaml` template

Default for Desk apps (includes JS hooks). **Drop** the prettier and eslint blocks for server-only integrations with no frontend.

Substitute `<app_name>` throughout. List each hygiene hook **once** (do not duplicate `check-yaml`).

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

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.1.0
    hooks:
      - id: prettier
        types_or: [javascript, vue, scss]
        exclude: |
          (?x)^(
              <app_name>/public/dist/.*|
              .*node_modules.*|
              .*boilerplate.*|
              <app_name>/templates/includes/.*|
              <app_name>/public/js/lib/.*
          )$

  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v9.39.1
    hooks:
      - id: eslint
        types_or: [javascript]
        args: ["--quiet", "--config", "eslint.config.mjs"]
        additional_dependencies:
          - "eslint@9.17.0"
          - "@eslint/js@9.17.0"
          - "globals@15.14.0"
        exclude: |
          (?x)^(
              <app_name>/public/dist/.*|
              cypress/.*|
              .*node_modules.*|
              .*boilerplate.*|
              <app_name>/templates/includes/.*|
              <app_name>/public/js/lib/.*
          )$

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

## `eslint.config.mjs`

Copy from an existing org app's `eslint.config.mjs` (or start from the template in this file). Replace the app-specific readonly global (`<app_name>`). Remove `.eslintrc` when migrating to eslint v9.

## Bootstrap smoke test

`<app_package>/tests/test_smoke.py`:

```python
from frappe.tests import UnitTestCase

from <app_package> import hooks


class TestSmoke(UnitTestCase):
	def test_app_name(self):
		self.assertEqual(hooks.app_name, "<app_name>")
```

Add `<app_package>/tests/__init__.py` if missing.

## `.github/workflows/linter.yml` template

Four jobs on pull requests. **`deps-vulnerable-check`** also runs on `workflow_dispatch`.

Semgrep uses [frappe/semgrep-rules](https://github.com/frappe/semgrep-rules) (`./frappe-semgrep-rules/rules`) plus `r/python.lang.correctness`.

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
      - uses: actions/checkout@v6
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
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: '3.14'
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
          python-version: '3.14'
      - uses: actions/checkout@v6
      - name: Cache pip
        uses: actions/cache@v5
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/*requirements.txt', '**/pyproject.toml', '**/setup.py') }}
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
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: '3.14'
          cache: pip
      - uses: pre-commit/action@v3.0.1
```

**Branch protection check names:** `Linters / Semantic Commits`, `Linters / Semgrep Rules`, `Linters / Vulnerable Dependency Check`, `Linters / Pre-Commit`.

### pip-audit notes

- Audits declared dependencies from `pyproject.toml` / understood lockfiles — not the full bench transitive tree unless you export requirements.
- On failure: bump direct pins first; use narrow `--ignore-vuln` only with a comment citing the advisory.

## `.github/workflows/ci.yml` template

Default triggers: **`pull_request`** + **`workflow_dispatch`** only (no `push` to `develop`).

**`Run Tests` is enabled** — unlike some legacy org CI where that step is commented out.

```yaml
name: CI

on:
  workflow_dispatch:
  pull_request:
    paths-ignore:
      - '**.js'
      - '**.css'
      - '**.md'
      - '**.html'
      - '**.csv'
      - '**.po'
      - '**.pot'
      - '.editorconfig'
      - 'eslint.config.mjs'
      - '.gitattributes'
      - '.gitignore'
      - '.pre-commit-config.yaml'
      - 'commitlint.config.js'
      - 'commitlint.config.mjs'
      - 'license.txt'
      - 'README.md'
      - '.github/workflows/linter.yml'

concurrency:
  group: develop-<app_name>-${{ github.event.number }}
  cancel-in-progress: true

jobs:
  tests:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
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
          python-version: '3.14'
      - uses: actions/setup-node@v6
        with:
          node-version: 24
          check-latest: true
      - uses: actions/cache@v5
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/*requirements.txt', '**/pyproject.toml', '**/setup.py', '**/setup.cfg') }}
          restore-keys: |
            ${{ runner.os }}-pip-
            ${{ runner.os }}-
      - name: Get yarn cache directory path
        id: yarn-cache-dir-path
        run: 'echo "dir=$(yarn cache dir)" >> $GITHUB_OUTPUT'
      - uses: actions/cache@v5
        id: yarn-cache
        with:
          path: ${{ steps.yarn-cache-dir-path.outputs.dir }}
          key: ${{ runner.os }}-yarn-${{ hashFiles('**/yarn.lock') }}
          restore-keys: |
            ${{ runner.os }}-yarn-
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

**Branch protection check name:** `CI / Server`.

Optional: add `push: branches: [version-XX]` when stable-branch CI is required for releases.

## `.github/dependabot.yml` (recommended)

Monthly `pip` and `github-actions` update PRs — enough cadence for small teams without weekly triage noise.

```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "monthly"
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "monthly"
```

## `.github/workflows/codeql.yml` (recommended)

Python + JavaScript matrix; pin checkout/setup versions to the defaults table above.

Limit `push` to `develop` so feature-branch pushes do not spawn duplicate scans (PRs still run CodeQL). Add `version-XX` under `push.branches` when stable-branch direct pushes need the same gate.

```yaml
name: "CodeQL"

on:
  push:
    branches:
      - develop
  pull_request:
  schedule:
    - cron: "43 13 * * 0"

jobs:
  analyze:
    name: Analyze
    runs-on: ubuntu-latest
    permissions:
      actions: read
      contents: read
      security-events: write
    strategy:
      fail-fast: false
      matrix:
        language: [javascript, python]
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: "3.14"
      - uses: actions/setup-node@v6
        with:
          node-version: "24"
      - uses: github/codeql-action/init@v4
        with:
          languages: ${{ matrix.language }}
          queries: +security-and-quality
      - uses: github/codeql-action/autobuild@v4
        if: ${{ matrix.language == 'javascript' || matrix.language == 'python' }}
      - uses: github/codeql-action/analyze@v4
        with:
          category: "/language:${{ matrix.language }}"
```

**Branch protection:** `CodeQL / Analyze (python)`, `CodeQL / Analyze (javascript)` — exact labels from GitHub UI.

## Branch protection (`develop`)

Apply after the first green CI run on a pull request:

| Required check | Workflow |
| --- | --- |
| Semantic Commits | Linters |
| Semgrep Rules | Linters |
| Vulnerable Dependency Check | Linters |
| Pre-Commit | Linters |
| Server | CI |
| Analyze (python) | CodeQL |
| Analyze (javascript) | CodeQL |

Also: require PR before merge, conversation resolution, restrict direct pushes as org policy allows. Duplicate the ruleset on `version-XX` when the stable branch exists. Add CodeQL checks only after `codeql.yml` is merged.

## Optional add-on: `.github/workflows/release.yaml`

For **customer-facing alyf-de** apps using semantic-release on the active stable branch. Requires `RELEASE_TOKEN` and a dedicated release-bot git identity (`<RELEASE_BOT_NAME>` / `<RELEASE_BOT_EMAIL>`).

```yaml
name: Generate Semantic Release
on:
  push:
    branches:
      - version-16
jobs:
  release:
    name: Release
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
        with:
          fetch-depth: 0
          persist-credentials: false
      - uses: actions/setup-node@v6
        with:
          node-version: "lts/*"
      - run: npm install @semantic-release/git @semantic-release/exec --no-save
      - name: Create Release
        env:
          GITHUB_TOKEN: ${{ secrets.RELEASE_TOKEN }}
          GIT_AUTHOR_NAME: "<RELEASE_BOT_NAME>"
          GIT_AUTHOR_EMAIL: "<RELEASE_BOT_EMAIL>"
          GIT_COMMITTER_NAME: "<RELEASE_BOT_NAME>"
          GIT_COMMITTER_EMAIL: "<RELEASE_BOT_EMAIL>"
        run: npx semantic-release
```

Copy `.releaserc` from an existing org repo that already uses semantic-release, or author one from the [semantic-release docs](https://semantic-release.gitbook.io/). Skip until release automation is agreed.

## Greenfield bootstrap commit

One initial commit covering all CI files + smoke test:

```
ci: align pre-commit, workflows, and smoke test with ALYF baseline
```

Inherited/forked apps use the great-reformat sequence in [SKILL.md](SKILL.md) instead.
