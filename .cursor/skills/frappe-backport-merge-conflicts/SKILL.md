---
name: frappe-backport-merge-conflicts
description: >-
  Resolves merge conflicts on Frappe app backport PRs (Mergify, version-*-hotfix):
  uses AskQuestion to pick or create a matching bench, confirm dependency app branches,
  then fixes corrupted JSON, merges target, and regenerates gettext catalogs.
  po_branch_maps.py can build maps from two refs or conflicted POs and replay via bench (polib in bench env per skill workflow).
  Feature-introduced msgstr must match the original develop merge commit exactly.
  Hotfix code may use branch-local helpers instead of missing Frappe symbols—avoid try/import guards.
  Use for backport conflicts, mergify/bp branches, version-*-hotfix merges, or locale conflicts.
disable-model-invocation: true
---

# Frappe backport merge conflicts

Use when a backport PR (often `mergify/bp/<target>/pr-*`) conflicts with its target branch, especially `locale/main.pot` and `locale/*.po`.

**Related skills:** [frappe-gettext-localization](frappe-gettext-localization/SKILL.md) for POT/PO commands and translation quality.

**Script:** `<frappe-workspace>/.cursor/scripts/po_branch_maps.py` — subcommands **`build`**, **`replay`**, **`clean`**.

- **`build`** — writes one `<locale>.json` per PO. JSON keys: **`target`** = **base** (integration / `--target-ref` branch), **`source`** = **incoming** (PR / `--source-ref` or feature side). Inputs: **two clean git refs** (`--source-ref` incoming, `--target-ref` base) **or** a working-tree `.po` with conflict markers (`--conflict-po`, repeatable; optional `--discover-conflicts`). For hunks, **`--pr-maps-first-side`** maps the first conflict side to JSON `source` or `target` (incoming vs base) — align with merge/rebase ours/theirs in §3.1.
- **`replay`** — runs `bench generate-pot-file`, per-locale `bench update-po-files`, applies maps with **polib** (required; install per §3.3.1 before first use), then `bench compile-po-to-mo` unless `--skip-*`. **Invoke with** **`<bench-root>/env/bin/python …/po_branch_maps.py replay …`**: the script verifies **`sys.executable`** is that bench venv’s Python (resolved / `samefile`) and exits with a copy-paste example if not. **polib** must import there. Tie-break: **`--prefer base`** (default) vs **`--prefer incoming`**. If both sides disagree on a non-empty `msgstr` for the same `msgid`, stderr prints an **ambiguous translation** block for escalation. Deprecated: **`--source-first`** (same as **`--prefer incoming`**).
- **`clean`** — removes the temporary map directory when finished.

Invoke **`build`** / **`clean`** with any suitable `python3`. For **`replay`**, use the bench **`env/bin/python`** only (see §3.3.1). The script must reach **`main()`** (older copies missing `if __name__ == "__main__"` run but do nothing).

**GitHub:** Use the **GitHub MCP** (`user-github-alyf` or `user-github-dafrose`) to read PR metadata, head SHA, and base branch. Do **not** use `gh` — it is not installed on the local machine. See [github-mcp-pull-requests](github-mcp-pull-requests/SKILL.md).

## AskQuestion policy

Use **`AskQuestion`** (not assumptions) when:

- More than one bench could work, or none clearly matches the target line.
- **New bench vs existing bench** is not obvious from context.
- Detected **git branches** for any app in the dependency tree need human confirmation.
- The **next step** is ambiguous (merge vs rebase, drop vs keep a hunk, push target, locale replay choice).
- Backport **scope** is unclear (field/commit from `develop` vs hotfix intent).

If `AskQuestion` is unavailable, ask the same questions in chat. **Do not proceed** past Phase 0 until bench and branches are confirmed.

---

## Principles

1. **Match the bench to the target branch** before any `bench` or merge work.
2. **Merge source code first**; treat locale files as generated artifacts.
3. **Never hand-merge** conflict markers in `.pot` / `.po`.
4. **Backport scope only** — do not pull unrelated `develop` fields or commits into a hotfix backport.
5. Compare regenerated locale files to **`upstream/<target-branch>`**, not to a corrupted PR commit.
6. **Feature translations must mirror develop.** Every `msgstr` tied to strings **introduced by the backported feature** (same `msgid` as on the original feature merge into `develop`) must stay **exactly** the same as on that **`develop` merge commit** — same wording, HTML, placeholders (`{0}`), newlines, and punctuation. Prefer copying from ``git show <develop-feature-merge-sha>:…/locale/<locale>.po`` or from a **`po_branch_maps.py` source ref** pinned to that SHA. Do **not** rephrase or “improve” German (or other locales) unless the human explicitly overrides parity.
7. **Hotfix code can be branch-specific.** A change on `version-*-hotfix` is **not** automatically carried forward to `version-16` / `develop`. Prefer solutions that are **clear on the hotfix line** even if they differ from newer branches.
8. **Missing Frappe helpers on older majors — avoid import guards.** If the backport wants a symbol that exists only on newer Frappe (e.g. a new helper in core), **do not** default to `try/except ImportError` around the import to paper over versions. **Prefer removing that import** and using a **small local helper** (module-level `_…`) or the **target-line API** instead. Import-fallback stacks are harder to read, easy to get wrong, and obscure intent. Newer version branches can switch to the real Frappe helper when the backport is not the same patch.

---

## Phase 0 — Bench and dependency alignment (mandatory)

Do not run `bench generate-pot-file`, `bench migrate`, or tests until Phase 0 is **confirmed via AskQuestion**.

### 0.1 Identify PR targets (read-only)

From the PR via **GitHub MCP** (`pull_request_read`: `get`, `get_files`, …) or GitHub REST API — not `gh`:

| Field | Example |
|-------|---------|
| Target branch | `version-15-hotfix` |
| Backport head | `mergify/bp/version-15-hotfix/pr-253` or head SHA |
| App under backport | `eu_einvoice` (repo name) |
| `required_apps` | From `<app>/<app>/hooks.py` (e.g. `frappe`, `erpnext`) |

Infer **expected Frappe major** from target branch name (`version-15-*` → v15, `version-16-*` → v16, `develop` → develop).

### 0.2 Discover candidate benches

Scan workspace for directories with `apps/` and `sites/`. For each candidate record:

- Bench path
- Apps in `sites/apps.txt` (is target app installed?)
- Per dependency app: **current branch** (`git -C apps/<name> branch --show-current`), **short SHA**, **whether `required_apps` are present**

```bash
cd "<bench-root>" && test -f sites/apps.txt && cat sites/apps.txt
cd "<bench-root>/apps/frappe" && git branch --show-current && git rev-parse --short HEAD
cd "<bench-root>/apps/erpnext" && git branch --show-current && git rev-parse --short HEAD   # if installed
cd "<bench-root>/apps/<app>" && git branch --show-current && git rev-parse --short HEAD
```

### 0.3 AskQuestion — existing bench or new bench?

Present discovered benches (or “none found”). Example prompt:

**“How should we run this backport?”**

| Option | When |
|--------|------|
| Use existing bench `<path>` | Bench matches target major; all `required_apps` installed |
| Set up a new bench | No matching bench; user will create `bench init` / `get-app` on correct branches |
| Other | User specifies a different path or workflow |

If **new bench**: stop automated merge work; give the user a short checklist (Frappe branch, ERPNext branch, `get-app` target app at backport branch, site install). Re-run Phase 0.2–0.4 after the bench exists.

If **existing bench**: continue to 0.4.

### 0.4 Infer expected branches per dependency app

Build a **branch plan** before asking the user to confirm:

| App | Role | Expected branch (infer from target) |
|-----|------|-------------------------------------|
| `frappe` | Framework | `version-15` / `version-16` / `develop` matching target major |
| `erpnext` | Dependency (if in `required_apps`) | Same major line as Frappe on that bench |
| `<backport-app>` | App under fix | Backport head branch or local tracking branch (not target until after merge) |

Use remotes when helpful:

```bash
cd "<bench>/apps/<name>" && git fetch upstream 2>/dev/null; git branch -r | rg 'version-15|hotfix'
```

Document **detected** vs **expected** for each row.

### 0.5 AskQuestion — confirm dependency branches

Show a compact table in the question prompt, e.g.:

```
frappe:     detected version-15 @ abc1234  →  expected version-15
erpnext:    detected version-15 @ def5678  →  expected version-15
eu_einvoice: detected pr-258 @ 4ac1f3d   →  expected mergify/bp/.../pr-253
```

**“Confirm branches for this backport (or pick Other to correct):”**

- One option per **fully matching** configuration (all apps aligned).
- Include **“Adjust branches”** / **Other** if any app mismatches — then ask in chat for the correct branch per mismatched app.

Do **not** checkout or merge until the user confirms.

After confirmation, checkout mismatched apps:

```bash
cd "<bench>/apps/<name>" && git fetch upstream && git checkout -B <branch> upstream/<branch>
```

### 0.6 Preflight commands (after confirmation)

```bash
cd "<bench>/apps/<app>" && pwd && git rev-parse --show-toplevel
cd "<bench-root>" && bench version
cd "<bench-root>" && grep -E '^<app>$' sites/apps.txt
```

### 0.7 Why alignment matters

- `ignore_translatable_strings_from` reads **installed** apps' `locale/main.pot`. Wrong ERPNext branch → wrong excluded msgids.
- Tests and `bench migrate` differ across Frappe majors.
- gettext scans the app tree on disk; wrong app branch → wrong catalog.

---

## Phase 1 — Check out the backport branch (app repo only)

On the **confirmed bench**, in `apps/<app>`:

```bash
git fetch upstream
git fetch upstream "<backport-branch>:<local-branch>"   # if ref missing locally
git checkout -B "<local-branch>" upstream/"<backport-branch>"
```

If upstream ref is missing, fetch the PR head SHA via **GitHub MCP** (or REST API), then `git fetch upstream <sha>`.

Inspect for **committed** conflict markers (Mergify accidents):

```bash
git grep -n '<<<<<<<' -- '*.json' '*.po' '*.pot' || echo "OK"
python3 -m json.tool "<app>/<module>/.../*.json" > /dev/null
```

**AskQuestion** if you find conflict markers in unexpected files (e.g. Python): fix now vs merge target first?

---

## Phase 2 — Scope and non-locale fixes

### 2.1 Backport scope check

Compare backport to **`upstream/<target>`**, not `develop`.

- Fields/commits on `develop` but **not** on `<target>` must **not** ship in the backport.
- Remove orphan field defs not in `field_order` (they still affect gettext).

**AskQuestion** when a conflict hunk adds fields/commits you cannot tie to the backport PR: keep (justify) vs drop (develop-only)?

### 2.2 Fix committed JSON conflicts before merge

If `<<<<<<<` is in tracked JSON:

1. Resolve with **target + backport intent** only.
2. `python3 -m json.tool ...`
3. Commit: `fix: remove merge conflict markers from <doctype>`

### 2.3 Merge target into backport

**AskQuestion** if user preference for **merge** vs **rebase** onto target is unknown. Default: **merge** `upstream/<target>` into backport branch (typical for Mergify PRs).

```bash
git merge upstream/<target-branch>
```

Resolve non-locale conflicts (`*.py`, `*.js`, `*.json`, `hooks.py`). Ensure target hooks (e.g. `ignore_translatable_strings_from`) are present.

**AskQuestion** for ambiguous hunks: ours (backport) vs theirs (target) vs manual combine.

---

## Phase 3 — Locale conflicts (regenerate, do not merge)

Expected: `locale/main.pot`, `locale/<locale>.po`.

### 3.0 Translation parity with the original feature merge (mandatory read)

Scope here: **messages that belong to the backported PR** — new `_()` strings, DocType labels/descriptions shipped by that PR, etc.

- Identify the **`develop` commit that merged the feature** (squash-merge SHA from the GitHub PR, or equivalent). Call it **`<develop-feature-sha>`**.
- After regenerating POT/PO, `msgstr` for those feature `msgid`s must match **`<develop-feature-sha>`** for each locale (`de.po`, …). Treat as an **exact copy**: no editorial drift in replay or post-regeneration edits.
- **Do not use `upstream/develop` HEAD by default for that parity check.** `develop` can move on; POT dedup hooks and follow-up churn may shrink or reshuffle catalogs so **latest develop `*.po`** no longer carries the same entries or `msgstr`s as `<develop-feature-sha>`. Cherry-pick / diff against **`git show <develop-feature-sha>:<app>/locale/<locale>.po`** for the affected `msgid`s.
- **`po_branch_maps.py` and refs:** Two clean refs are ideal. If **`locale/*.po` still contains conflict markers** in the working tree, **`build`** can still extract maps: use **`--conflict-po <app>/locale/de.po`** (repeatable for each file) or **`--discover-conflicts`** under **`--locale-dir`**, and set **`--pr-maps-first-side`** so the JSON `source` / `target` keys match your merge/rebase semantics (see script `--help`). If the tree is **committed** with markers inside PO/JSON, repair that commit or use **`git show <good-sha>:path`** — do not feed broken refs to **`replay`**.
- **Committed** conflict markers in DocType JSON still require manual resolution before any gettext step.

### 3.1 Build msgid maps (before unblocking locale)

From the **app repo root** (`<bench>/apps/<app>`), write one temporary JSON file per `*.po` locale (e.g. `de.json`). Maps contain non-empty `msgstr` values only (unless `build --include-empty`).

**Option A — in-progress merge with clean refs (typical):**

```bash
cd "<bench>/apps/<app>"
MAP_DIR=".po-branch-maps-tmp"
WORKSPACE="<frappe-workspace>"   # meta repo root that contains .cursor/scripts/

python3 "$WORKSPACE/.cursor/scripts/po_branch_maps.py" build \
  --repo . \
  --locale-dir <app>/locale \
  --source-ref HEAD \
  --target-ref MERGE_HEAD \
  --out-dir "$MAP_DIR"
```

**Option B — conflict markers still in `*.po` (working tree):**

```bash
python3 "$WORKSPACE/.cursor/scripts/po_branch_maps.py" build \
  --repo . \
  --locale-dir <app>/locale \
  --discover-conflicts \
  --pr-maps-first-side source \
  --out-dir "$MAP_DIR"
```

Adjust **`--pr-maps-first-side`** for rebase vs merge (see **During `git merge` / `git rebase`** below). Or pass explicit paths: **`--conflict-po <app>/locale/de.po`** (repeat per locale).

| Ref / mode | Role |
|------------|------|
| `--source-ref` | **Incoming** (PR / feature) → JSON ``source`` |
| `--target-ref` | **Base** (integration / target branch) → JSON ``target`` |
| `--conflict-po` / `--discover-conflicts` | Split hunks into synthetic POs; map sides with **`--pr-maps-first-side`** to ``source`` / ``target`` (incoming / base) |

If **not** in a merge yet, use the branch refs instead, e.g. `--source-ref upstream/<backport-branch>` and `--target-ref upstream/<target-branch>`.

When **replay must match develop wording for the PR**, prefer `--source-ref <develop-feature-sha>` (and the correct path in the repo at that revision) instead of a corrupt **backport** ref. Pair with **`--target-ref` = `upstream/<target>` or `MERGE_HEAD`** per your workflow.

During **`git merge`** with conflicts in locale files only, **ours/theirs semantics** follow Git merge: typically **`--ours` = current branch**, **`--theirs` = branch being merged in**. During **`git rebase`**, **`--ours` = the branch rebased onto (onto / upstream)** and **`--theirs` = the commit being replayed** — before regenerating catalog, **`git checkout --ours`** on `locale/` often means **target-line catalog**, not PR side. Prefer explicit refs over memorizing flipped ours/theirs during rebase.

Each `<locale>.json` has `source` and `target` objects (`msgid` → `msgstr`). Use them for replay in §3.4 — do not hand-copy PO files into `/tmp`.

**AskQuestion** which locales to process if more than one `*.po` exists.

### 3.2 Unblock locale merge

Prefer **one side** plus full regen (markers must not be merged by hand). **`git checkout --theirs "$LOCALE/"`** matches **in-progress `git merge`** when you want the other branch’s version before `bench generate-pot-file`. On **`git rebase`**, swapped **ours/theirs** (see §3.1) — pick the **onto**-line files if you regenerate from target baseline, or remove conflicted paths and regen from scratch.

### 3.3 Regenerate (confirmed bench only)

```bash
cd "<bench-root>"
bench generate-pot-file --app <app>
bench update-po-files --app <app> --locale <locale>
```

Preconditions: `ignore_translatable_strings_from` on target; ERPNext installed; no stray scan paths (e.g. `frappe-semgrep-rules/` in `.gitignore`).

### 3.3.1 polib (before `replay`)

**`po_branch_maps.py replay`** needs **polib** in the **bench** virtualenv. Install once per bench (persists in `env/`); do **not** rely on the script to run `pip`:

```bash
cd "<bench-root>" && ./env/bin/python -m pip install polib
./env/bin/python -c "import polib"
```

Run **`replay`** with the bench venv’s Python so it matches **`--bench-root`** (the script enforces this on startup).

**Optional — one command after `build`:** `po_branch_maps.py replay` runs the same bench steps, applies maps with **polib**, then compiles MO files. Use **`--locales de`** or omit for all `*.json` in **`--maps-dir`**; **`--skip-generate`** only if POT/PO are already fresh. Tie-break: default **`--prefer base`**; use **`--prefer incoming`** when PR wording must win for overlapping msgids.

```bash
cd "<bench>/apps/<app>"
PY="<bench-root>/env/bin/python"
"$PY" "$WORKSPACE/.cursor/scripts/po_branch_maps.py" replay \
  --repo . \
  --bench-root "<bench-root>" \
  --app <app> \
  --maps-dir "$MAP_DIR"
```

### 3.4 Replay translations

Prefer **`replay`** (§3.3) so regeneration and map application stay consistent. If doing it manually, for each locale read `.po-branch-maps-tmp/<locale>.json` and update the regenerated `<locale>.po`:

1. **`source` map** — **incoming** side; when `§3.0` applies for feature strings, **`source` may be keyed from `<develop-feature-sha>`** so those `msgstr`s match **develop** verbatim (then use **`--prefer incoming`** in **`replay`** for overlapping keys if you need that wording to win).
2. **`target` map** — **base** (integration branch) side.
3. Default in **`replay`**: **`--prefer base`** — for the same msgid, if both maps have a non-empty `msgstr`, the **base** (`target`) value wins; incoming (`source`) fills gaps. Use **`--prefer incoming`** for the opposite. (Deprecated flag: **`--source-first`** ↔ **`--prefer incoming`**.)
4. **`#, fuzzy` + `#| msgid "..."`** — look up previous msgid in either map and adapt wording.
5. Else translate (or leave empty and report).

Remove `#, fuzzy` only when `msgstr` is correct. Preserve `{0}`, HTML, and whitespace **exactly as on `<develop-feature-sha>`** for feature strings.

For **tie-breaks affecting feature `msgid`s**, default to **develop merge `msgstr`**, not improvised wording. **AskQuestion** only when **`source` and `develop-feature` disagree** due to tooling/parsing gaps, not for stylistic preference.

If you did **not** use `replay`, still run:

```bash
cd "<bench-root>"
bench compile-po-to-mo --app <app> --locale <locale>
```

### 3.4.1 Remove temporary map files

After all locales are translated and `de.po` (etc.) have no unintended empty `msgstr` entries:

```bash
cd "<bench>/apps/<app>"
python3 "$WORKSPACE/.cursor/scripts/po_branch_maps.py" clean --out-dir .po-branch-maps-tmp
```

Do not commit `.po-branch-maps-tmp/`. If the directory was already removed, `clean` is a no-op.

### 3.5 Legitimate msgid removals

Compare to `upstream/<target>`, not corrupt PR `HEAD`. Removals are OK for corrupt POT, ERPNext dedup via ignore hook, or real code removal on target.

**AskQuestion** if a removed msgid is app-specific (not in Frappe/ERPNext POT) and still has a live `_()` / DocType label in source.

### 3.6 Finish merge

```bash
git add <app>/locale/ <app>/hooks.py
git merge --continue
```

**AskQuestion** before push: remote (`upstream` / `origin`), branch name (Mergify branch vs fork), and whether user wants a single commit or separate fix/regen commits.

---

## Phase 4 — Verification

```bash
git grep -n '<<<<<<<' || echo "OK"
python3 -m json.tool <touched-doctype>.json > /dev/null
cd "<bench-root>" && bench run-tests --app <app> --module <module>
```

Report: confirmed bench path; **confirmed branches** for frappe / erpnext / app; fixes; locale counts; `main.pot` diff vs `upstream/<target>`.

---

## AskQuestion quick reference

| Situation | Ask |
|-----------|-----|
| Multiple or zero benches | Existing which path, or create new bench? |
| After branch detection | Confirm frappe / erpnext / app branches (table) |
| Conflict markers in code | Fix before merge or after? |
| develop-only hunks | Keep or drop? |
| merge vs rebase | Which workflow? |
| Ambiguous conflict hunk | Ours / theirs / manual? |
| Multiple locales | Which `*.po` to update? |
| Translation tie-break | Prefer **exact** `msgstr` from **`<develop-feature-sha>`** for backport strings |
| Push destination | Remote + branch name? |
| `source-ref` / `target-ref` during merge | `HEAD` + `MERGE_HEAD` vs branch names? |
| Locale file still conflicted on disk | `build --discover-conflicts` / `--conflict-po` + `--pr-maps-first-side`? |
| Regen + replay automation | Run `po_branch_maps.py replay` **with** bench `env/bin/python`; **`polib`** per §3.3.1; **`--prefer base`** (default) vs **`--prefer incoming`** |

---

## Anti-patterns

- Skipping Phase 0 confirmation and using `develop` bench for `version-15-hotfix`
- Hand-editing conflict markers in `.po` / `.pot`
- `git diff HEAD` on locale when HEAD is Mergify-corrupted
- Guessing branch names when `upstream/mergify/...` is not fetched locally
- Using `gh` for PR data (not installed; use GitHub MCP instead)
- Shipping develop DocType fields “because they were in the conflict”
- **Rephrasing** `msgstr` for **`msgid`s from the original feature merge** (`develop`) instead of **byte-identical parity** with **`<develop-feature-sha>`**, or validating parity only against **latest `develop` HEAD**
- Passing **`--source-ref`** a commit whose **committed** `*.po` / JSON still contains **`<<<<<<<`** — use **`build --conflict-po`** on a checked-out file, or **`git show <good-sha>`**, or repair the commit first
- Defaulting to **`try/except ImportError`** around Frappe imports on hotfix when **Principle 8** above applies — prefer **dropping the import** and a **local `_…` helper** (branch-specific is OK)

---

## When to escalate

- User chooses new bench but does not have one ready — provide setup steps, pause merge
- Conflict markers in Python with failing tests outside locale scope
- Missing dependency app on bench after AskQuestion (need `bench get-app`)
- User rejects ERPNext msgid dedup — explain hook; only override if explicitly requested
- **Backport code** imports symbols that exist only on newer Frappe — **remove the import**, add a **small branch-local helper** or use **target-line APIs** (see **§ Principles 7–8**); reserve import shims for rare cases where behavior must differ by version at runtime
