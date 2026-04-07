---
name: frappe-backport-merge-conflicts
description: >-
  Resolves merge conflicts on Frappe app backport PRs (Mergify, version-*-hotfix):
  uses AskQuestion to pick or create a matching bench, confirm dependency app branches,
  then fixes corrupted JSON, merges target, and regenerates gettext catalogs.
  po_branch_maps.py can build maps from two refs or conflicted POs and replay via bench.
  Feature-introduced msgstr must match the original develop merge commit exactly.
  Hotfix code may use branch-local helpers instead of missing Frappe symbols—avoid try/import guards.
  Phase 0 discovers bench sites and per-site installed apps; AskQuestion picks a test site that has the backport app.
  Use for backport conflicts, mergify/bp branches, version-*-hotfix merges, or locale conflicts.
disable-model-invocation: true
---

# Frappe backport merge conflicts

## Scope

Use when a backport PR (often `mergify/bp/<target>/pr-*`) conflicts with its target
branch—especially `locale/main.pot` and `locale/*.po`. Requires bench alignment (Phase 0),
code/JSON resolution (Phases 1–2), then locale regeneration (Phase 3)—never hand-merge
gettext conflict markers. Not for normal feature development on `develop` or generic
gettext without a backport merge (see **frappe-gettext-localization**).

**Script:** `<frappe-workspace>/.cursor/scripts/po_branch_maps.py` — subcommands **`build`**, **`replay`**, **`clean`**.

- **`build`** — writes one `<locale>.json` per PO. JSON keys: **`target`** = **base** (integration / `--target-ref` branch), **`source`** = **incoming** (PR / `--source-ref` or feature side). Inputs: **two clean git refs** (`--source-ref` incoming, `--target-ref` base) **or** a working-tree `.po` with conflict markers (`--conflict-po`, repeatable; optional `--discover-conflicts`). For hunks, **`--pr-maps-first-side`** maps the first conflict side to JSON `source` or `target` (incoming vs base) — align with merge/rebase ours/theirs in §3.1.
- **`replay`** — runs `bench generate-pot-file`, per-locale `bench update-po-files`, applies maps with **polib** (required; install per §3.3.1 before first use), then `bench compile-po-to-mo` unless `--skip-*`. **Invoke with** **`<bench-root>/env/bin/python …/po_branch_maps.py replay …`**: the script verifies **`sys.executable`** is that bench venv’s Python (resolved / `samefile`) and exits with a copy-paste example if not. **polib** must import there. Tie-break: **`--prefer base`** (default) vs **`--prefer incoming`**. If both sides disagree on a non-empty `msgstr` for the same `msgid`, stderr prints an **ambiguous translation** block for escalation. Deprecated: **`--source-first`** (same as **`--prefer incoming`**).
- **`clean`** — removes the temporary map directory when finished.

Invoke **`build`** / **`clean`** with any suitable `python3`. For **`replay`**, use the bench **`env/bin/python`** only (see §3.3.1). The script must reach **`main()`** (older copies missing `if __name__ == "__main__"` run but do nothing).

**GitHub:** Use the **GitHub MCP** (`user-github-<org>` or `user-github-<personal>`) to read PR metadata, head SHA, and base branch. Do **not** use `gh` — it is not installed on the local machine. See [github-mcp-pull-requests](github-mcp-pull-requests/SKILL.md).

## AskQuestion policy

Use **`AskQuestion`** (not assumptions) when:

- More than one bench could work, or none clearly matches the target line.
- **New bench vs existing bench** is not obvious from context.
- Detected **git branches** for any app in the dependency tree need human confirmation.
- **More than one site** on the confirmed bench has the backport app installed (or none do).
- The **next step** is ambiguous (merge vs rebase — **AskQuestion** before §2.3; default **rebase**, drop vs keep a hunk, push target, locale replay choice).
- Backport **scope** is unclear (field/commit from `develop` vs hotfix intent).

If `AskQuestion` is unavailable, ask the same questions in chat. **Do not proceed** past Phase 0 until bench, branches, and **test site** are confirmed.

### Placeholders (resolve before use)

Do **not** guess app or site names from examples. Resolve each placeholder via **AskQuestion** (or chat) in Phase 0:

| Placeholder | Meaning |
|-------------|---------|
| `<my_app>` | Repo / package name of the app under backport (`sites/apps.txt` entry, `apps/<my_app>/`) |
| `<site.name>` | Frappe site chosen in §0.7 for `bench --site …` and Phase 4 tests |
| `<bench-root>` | Confirmed bench path from §0.3 |
| `<target-branch>` | PR base branch (e.g. `version-15-hotfix`) |
| `<backport-branch>` | PR head / Mergify backport branch |

Examples below use these placeholders literally — substitute only after the user confirms values.

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

Do not run `bench generate-pot-file`, `bench migrate`, or tests until Phase 0 is **confirmed via AskQuestion** (bench, branches, test site).

### 0.1 Identify PR targets (read-only)

From the PR via **GitHub MCP** (`pull_request_read`: `get`, `get_files`, …) or GitHub REST API — not `gh`:

| Field | Example |
|-------|---------|
| Target branch | `version-15-hotfix` |
| Backport head | `mergify/bp/version-15-hotfix/pr-253` or head SHA |
| App under backport | `<my_app>` (repo name) |
| `required_apps` | From `<my_app>/<my_app>/hooks.py` (e.g. `frappe`, `erpnext`) |

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
cd "<bench-root>/apps/<my_app>" && git branch --show-current && git rev-parse --short HEAD
```

### 0.3 AskQuestion — existing bench or new bench?

Present discovered benches (or “none found”). Example prompt:

**“How should we run this backport?”**

| Option | When |
|--------|------|
| Use existing bench `<path>` | Bench matches target major; all `required_apps` installed |
| Set up a new bench | No matching bench; user will create `bench init` / `get-app` on correct branches |
| Other | User specifies a different path or workflow |

If **new bench**: stop automated merge work; give the user a short checklist (Frappe branch, ERPNext branch, `get-app` target app at backport branch, site + `install-app`). Re-run Phase 0.2–0.7 after the bench exists.

If **existing bench**: continue to 0.4.

### 0.4 Infer expected branches per dependency app

Build a **branch plan** before asking the user to confirm:

| App | Role | Expected branch (infer from target) |
|-----|------|-------------------------------------|
| `frappe` | Framework | `version-15` / `version-16` / `develop` matching target major |
| `erpnext` | Dependency (if in `required_apps`) | Same major line as Frappe on that bench |
| `<my_app>` | App under fix | Backport head branch or local tracking branch (not target until after merge) |

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
<my_app>: detected pr-258 @ 4ac1f3d   →  expected mergify/bp/.../pr-253
```

**“Confirm branches for this backport (or pick Other to correct):”**

- One option per **fully matching** configuration (all apps aligned).
- Include **“Adjust branches”** / **Other** if any app mismatches — then ask in chat for the correct branch per mismatched app.

Do **not** checkout or merge until the user confirms.

After confirmation, checkout mismatched apps:

```bash
cd "<bench>/apps/<name>" && git fetch upstream && git checkout -B <branch> upstream/<branch>
```

### 0.6 Discover sites and per-site app installs

On the **confirmed bench**, list **sites** (directories under `sites/` that contain `site_config.json` — not `assets`, `apps.txt`, etc.) and which apps each site has **installed** (bench-level `sites/apps.txt` only means the app is available on disk).

```bash
cd "<bench-root>"
for d in sites/*/; do
  n=$(basename "$d")
  test -f "sites/$n/site_config.json" || continue
  echo "=== $n ==="
  bench --site "$n" list-apps 2>/dev/null || echo "(list-apps failed — site may be broken)"
done
```

Build a table for the backport app (`<my_app>` from §0.1):

| Site | `<my_app>` installed? | Other installed apps (short) |
|------|--------------------|------------------------------|
| `<site.name>` | yes | frappe, erpnext, … |
| `…` | no | frappe, erpnext, … |

**Qualifying sites** = rows where `<my_app>` appears in that site's `bench --site <site.name> list-apps` output.

If **no qualifying site**: stop before tests; tell the user to `bench --site <site.name> install-app <my_app>` (or create a site) and re-run §0.6. Gettext / merge work may still proceed if the app is on the bench (`sites/apps.txt`).

### 0.7 AskQuestion — confirm test site

Even when only one site qualifies, **AskQuestion** (do not assume `default_site` from `common_site_config.json`).

**“Which site should we run tests against?”**

- One option per **qualifying** site (label: site name + short app list if helpful).
- **Other** if the user wants a different site (then install app or fix site first).
- If **zero** qualifying sites: options are “Install `<my_app>` on `<site.name>` first” / **Other** — do not pick an unqualified site silently.

Record the choice as **`<site.name>`** for Phase 4.

### 0.8 Preflight commands (after confirmation)

```bash
cd "<bench>/apps/<my_app>" && pwd && git rev-parse --show-toplevel
cd "<bench-root>" && bench version
cd "<bench-root>" && grep -E '^<my_app>$' sites/apps.txt
cd "<bench-root>" && bench --site <site.name> list-apps | grep -E '^<my_app>'
```

### 0.9 Why alignment matters

- `ignore_translatable_strings_from` reads **installed** apps' `locale/main.pot`. Wrong ERPNext branch → wrong excluded msgids.
- Tests and `bench migrate` differ across Frappe majors.
- gettext scans the app tree on disk; wrong app branch → wrong catalog.
- **`bench run-tests` needs a site** where `<my_app>` is installed; bench-level `apps.txt` alone is not enough.

---

## Phase 1 — Check out the backport branch (app repo only)

On the **confirmed bench**, in `apps/<my_app>`:

```bash
git fetch upstream
git fetch upstream "<backport-branch>:<local-branch>"   # if ref missing locally
git checkout -B "<local-branch>" upstream/"<backport-branch>"
```

If upstream ref is missing, fetch the PR head SHA via **GitHub MCP** (or REST API), then `git fetch upstream <sha>`.

Inspect for **committed** conflict markers (Mergify accidents):

```bash
git grep -n '<<<<<<<' -- '*.json' '*.po' '*.pot' || echo "OK"
python3 -m json.tool "<my_app>/<module>/.../*.json" > /dev/null
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

### 2.3 Integrate target into backport

**AskQuestion** — confirm **merge strategy** before integrating `upstream/<target>` (do not assume; even on Mergify branches):

**“How should we integrate the target branch?”**

| Option | When |
|--------|------|
| **Rebase** (default) | Linear history on the backport branch; preferred for commitlint-friendly subjects (`fix:`, `feat:`) |
| **Merge** | Preserve merge commit; use when the team explicitly wants a merge node |
| **Other** | User specifies a different workflow |

Default: **rebase** onto target.

```bash
# Rebase (default)
git rebase upstream/<target-branch>

# Merge (when chosen)
git merge upstream/<target-branch>
```

Resolve non-locale conflicts (`*.py`, `*.js`, `*.json`, `hooks.py`). Ensure target hooks (e.g. `ignore_translatable_strings_from`) are present.

During **rebase**, **ours/theirs are flipped** vs merge — see [reference.md](reference.md) §3.1 before `git checkout --ours` / `--theirs` on locale files.

**AskQuestion** for ambiguous hunks: ours (backport) vs theirs (target) vs manual combine.

Conflict-resolution commits must use **Conventional Commits** types (`fix:`, `feat:`, `chore:`, …) — never `merge:` (commitlint rejects it).

---

## Phase 3 — Locale conflicts (regenerate, do not merge)

Expected: `locale/main.pot`, `locale/<locale>.po`.

### 3.0 Translation parity with the original feature merge (mandatory read)

Scope here: **messages that belong to the backported PR** — new `_()` strings, DocType labels/descriptions shipped by that PR, etc.

- Identify the **`develop` commit that merged the feature** (squash-merge SHA from the GitHub PR, or equivalent). Call it **`<develop-feature-sha>`**.
- After regenerating POT/PO, `msgstr` for those feature `msgid`s must match **`<develop-feature-sha>`** for each locale (`de.po`, …). Treat as an **exact copy**: no editorial drift in replay or post-regeneration edits.
- **Do not use `upstream/develop` HEAD by default for that parity check.** `develop` can move on; POT dedup hooks and follow-up churn may shrink or reshuffle catalogs so **latest develop `*.po`** no longer carries the same entries or `msgstr`s as `<develop-feature-sha>`. Cherry-pick / diff against **`git show <develop-feature-sha>:<my_app>/locale/<locale>.po`** for the affected `msgid`s.
- **`po_branch_maps.py` and refs:** Two clean refs are ideal. If **`locale/*.po` still contains conflict markers** in the working tree, **`build`** can still extract maps: use **`--conflict-po <my_app>/locale/de.po`** (repeatable for each file) or **`--discover-conflicts`** under **`--locale-dir`**, and set **`--pr-maps-first-side`** so the JSON `source` / `target` keys match your merge/rebase semantics (see script `--help`). If the tree is **committed** with markers inside PO/JSON, repair that commit or use **`git show <good-sha>:path`** — do not feed broken refs to **`replay`**.
- **Committed** conflict markers in DocType JSON still require manual resolution before any gettext step.


## Additional resources

- [reference.md](reference.md) — Phase 3.1–3.4 locale replay (`po_branch_maps.py`, polib, checksum idempotency)

### 3.1–3.4 Locale replay (detail)

Follow **[reference.md](reference.md)** for `po_branch_maps.py` **build** / **replay** / **clean**,
ref selection (`HEAD` / `MERGE_HEAD`, `<develop-feature-sha>`), polib install, tie-break
(`--prefer base` vs `--prefer incoming`), §3.4.2 final gettext pass, and §3.4.3 checksum idempotency.

### 3.5 Legitimate msgid removals

Compare to `upstream/<target>`, not corrupt PR `HEAD`. Removals are OK for corrupt POT, ERPNext dedup via ignore hook, or real code removal on target.

**AskQuestion** if a removed msgid is app-specific (not in Frappe/ERPNext POT) and still has a live `_()` / DocType label in source.

### 3.6 Finish integration

Only after §3.4.3 **checksum idempotency** passes (and **`compile-po-to-mo`** is up to date), or an agreed exception:

```bash
git add <my_app>/locale/ <my_app>/hooks.py
# Rebase (default from §2.3):
git rebase --continue
# Merge (when §2.3 chose merge):
git merge --continue
```

Use a **Conventional Commits** subject on continue/amend (e.g. `fix: resolve … conflicts for backport #NNN`) — not `merge:`.

**AskQuestion** before push: remote (`upstream` / `origin`), branch name (Mergify branch vs fork), and whether user wants a single commit or separate fix/regen commits. After **rebase**, push with **`--force-with-lease`** when the branch was already on the remote.

---

## Phase 4 — Verification

Use **`<site.name>`** from §0.7 (must have `<my_app>` installed).

```bash
git grep -n '<<<<<<<' || echo "OK"
python3 -m json.tool <touched-doctype>.json > /dev/null
# Re-run §3.4.3 shasum diff (generate-pot-file + update-po-files twice, no byte change)
cd "<bench-root>" && bench --site <site.name> run-tests --app <my_app> --module <module>
```

Prefer **`--test-category unit`** when the backport only adds unit tests and full integration bootstrap fails on the chosen site (e.g. duplicate seed rows). Report that skip explicitly.

Report: confirmed bench path; **`<site.name>`**; **confirmed branches** for frappe / erpnext / app; fixes; **§3.4.3 idempotent gettext** ok; locale counts; `main.pot` sanity vs `upstream/<target>`; test result.

---

## AskQuestion quick reference

| Situation | Ask |
|-----------|-----|
| Multiple or zero benches | Existing which path, or create new bench? |
| After branch detection | Confirm frappe / erpnext / app branches (table) |
| Sites on confirmed bench | Which **`<site.name>`** among sites with `<my_app>` installed? (§0.6–0.7) |
| Zero sites with `<my_app>` | Install app on a site first, or create site — before Phase 4 tests |
| Conflict markers in code | Fix before merge or after? |
| develop-only hunks | Keep or drop? |
| merge vs rebase | **AskQuestion** before §2.3 — default **rebase** |
| Ambiguous conflict hunk | Ours / theirs / manual? |
| Multiple locales | Which `*.po` to update? |
| Translation tie-break | Prefer **exact** `msgstr` from **`<develop-feature-sha>`** for backport strings |
| Push destination | Remote + branch name? |
| `source-ref` / `target-ref` during merge | `HEAD` + `MERGE_HEAD` vs branch names? |
| Locale file still conflicted on disk | `build --discover-conflicts` / `--conflict-po` + `--pr-maps-first-side`? |
| Regen + replay automation | Run `po_branch_maps.py replay` **with** bench `env/bin/python`; **`polib`** per §3.3.1; **`--prefer base`** (default) vs **`--prefer incoming`** |
| After replay / hand edits | §3.4.2 final gettext + **`compile-po-to-mo`**, then §3.4.3 **checksum** idempotency (repeat gettext must not change **`.po`** / **`main.pot`** bytes)? |

---

## Anti-patterns

- Skipping Phase 0 confirmation and using `develop` bench for `version-15-hotfix`
- Running **`bench run-tests`** without §0.6–0.7 — guessing a site name or using **`default_site`** when that site does not have `<my_app>` installed
- Hand-editing conflict markers in `.po` / `.pot`
- `git diff HEAD` on locale when HEAD is Mergify-corrupted
- Guessing branch names when `upstream/mergify/...` is not fetched locally
- Using `gh` for PR data (not installed; use GitHub MCP instead)
- Shipping develop DocType fields “because they were in the conflict”
- **Rephrasing** `msgstr` for **`msgid`s from the original feature merge** (`develop`) instead of **byte-identical parity** with **`<develop-feature-sha>`**, or validating parity only against **latest `develop` HEAD**
- Passing **`--source-ref`** a commit whose **committed** `*.po` / JSON still contains **`<<<<<<<`** — use **`build --conflict-po`** on a checked-out file, or **`git show <good-sha>`**, or repair the commit first
- Defaulting to **`try/except ImportError`** around Frappe imports on hotfix when **Principle 8** above applies — prefer **dropping the import** and a **local `_…` helper** (branch-specific is OK)
- Skipping **§3.4.2–3.4.3** and committing locale churn from **polib** vs Babel or unstable gettext (repeat **`generate-pot-file`** / **`update-po-files`** should not change **`git diff`**)
- **`merge:`** commit subjects — use **`fix:`** / **`feat:`** / **`chore:`** so commitlint passes
- Defaulting to **`git merge`** without **AskQuestion** when **rebase** is the house default

---

## When to escalate

- User chooses new bench but does not have one ready — provide setup steps, pause merge
- Conflict markers in Python with failing tests outside locale scope
- Missing dependency app on bench after AskQuestion (need `bench get-app`)
- No site with `<my_app>` installed after §0.6 — provide `bench new-site` / `bench --site <site.name> install-app <my_app>` checklist; pause Phase 4 tests
- User rejects ERPNext msgid dedup — explain hook; only override if explicitly requested
- **Backport code** imports symbols that exist only on newer Frappe — **remove the import**, add a **small branch-local helper** or use **target-line APIs** (see **§ Principles 7–8**); reserve import shims for rare cases where behavior must differ by version at runtime

## Related skills

- [`frappe-gettext-localization`](frappe-gettext-localization/SKILL.md) — `bench generate-pot-file` / `update-po-files` / `compile-po-to-mo` and header metadata
- [`github-mcp-pull-requests`](github-mcp-pull-requests/SKILL.md) — PR metadata and base branch via MCP (not `gh`)
