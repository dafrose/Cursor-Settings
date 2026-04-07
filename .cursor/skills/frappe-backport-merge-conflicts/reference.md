# frappe-backport-merge-conflicts — locale reference

Detailed locale replay for backport PRs. See [SKILL.md](SKILL.md) for Phase 0–2, principles, and Phase 3 overview.

### 3.1 Build msgid maps (before unblocking locale)

From the **app repo root** (`<bench>/apps/<my_app>`), write one temporary JSON file per `*.po` locale (e.g. `de.json`). Maps contain non-empty `msgstr` values only (unless `build --include-empty`).

**Option A — in-progress merge with clean refs (typical):**

```bash
cd "<bench>/apps/<my_app>"
MAP_DIR=".po-branch-maps-tmp"
WORKSPACE="<frappe-workspace>"   # meta repo root that contains .cursor/scripts/

python3 "$WORKSPACE/.cursor/scripts/po_branch_maps.py" build \
  --repo . \
  --locale-dir <my_app>/locale \
  --source-ref HEAD \
  --target-ref MERGE_HEAD \
  --out-dir "$MAP_DIR"
```

**Option B — conflict markers still in `*.po` (working tree):**

```bash
python3 "$WORKSPACE/.cursor/scripts/po_branch_maps.py" build \
  --repo . \
  --locale-dir <my_app>/locale \
  --discover-conflicts \
  --pr-maps-first-side source \
  --out-dir "$MAP_DIR"
```

Adjust **`--pr-maps-first-side`** for rebase vs merge (see **During `git merge` / `git rebase`** below). Or pass explicit paths: **`--conflict-po <my_app>/locale/de.po`** (repeat per locale).

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
bench generate-pot-file --app <my_app>
bench update-po-files --app <my_app> --locale <locale>
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
cd "<bench>/apps/<my_app>"
PY="<bench-root>/env/bin/python"
"$PY" "$WORKSPACE/.cursor/scripts/po_branch_maps.py" replay \
  --repo . \
  --bench-root "<bench-root>" \
  --app <my_app> \
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
bench compile-po-to-mo --app <my_app> --locale <locale>
```

### 3.4.1 Remove temporary map files

After all locales are translated and `de.po` (etc.) have no unintended empty `msgstr` entries:

```bash
cd "<bench>/apps/<my_app>"
python3 "$WORKSPACE/.cursor/scripts/po_branch_maps.py" clean --out-dir .po-branch-maps-tmp
```

Do not commit `.po-branch-maps-tmp/`. If the directory was already removed, `clean` is a no-op.

### 3.4.2 Final gettext pass (format normalization)

**polib** saves and hand edits often disagree with **Babel**/gettext line-wrapping and reference comments. After **`replay`** or manual §3.4 edits—and **before** treating locale as final—run **`bench generate-pot-file`** and **`bench update-po-files`** once more so catalogs match the toolchain layout.

```bash
cd "<bench-root>"
bench generate-pot-file --app <my_app>
bench update-po-files --app <my_app> --locale <locale>   # repeat per locale
```

Re-run **`bench compile-po-to-mo`** per locale after this pass so **`.mo`** matches the normalized **`.po`**.

### 3.4.3 Verify idempotent gettext (no meaningful churn)

Run **`bench generate-pot-file`** and each **`update-po-files`** **one more time** (identical to §3.4.2, with no edits in between). **Catalog bytes must not change** on that repeat: otherwise gettext output is unstable and you should fix the cause before committing.

Practical check: hash **all** **`main.pot`** and **`*.po`**, run one full **`generate-pot-file`** + every **`update-po-files`**, hash again:

```bash
L="<bench>/apps/<my_app>/<my_app>/locale"
shasum -a 256 "$L/main.pot" "$L"/*.po > /tmp/po-sha-before
cd "<bench-root>"
bench generate-pot-file --app <my_app>
bench update-po-files --app <my_app> --locale de   # every locale with a .po
# …
shasum -a 256 "$L/main.pot" "$L"/*.po > /tmp/po-sha-after
diff /tmp/po-sha-before /tmp/po-sha-after   # must print nothing
```

If **`diff`** reports a change, investigate (environment drift, odd **`.po`** layout, duplicate **`msgid`s**, etc.).

**`git diff`** against **HEAD** is still useful to review the accumulated locale change before commit, but it does **not** prove idempotency; the checksum comparison does.

If the only deltas are benign header timestamps and your team allows it, **AskQuestion**; otherwise treat non‑idempotent repeats as a blocker until resolved.

