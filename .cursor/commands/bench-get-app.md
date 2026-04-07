Fetch a Frappe app into a bench using `bench get-app`.

## 0. Gather information (AskQuestion first)

Before running any shell command, collect inputs as follows.

**Skip AskQuestion** only when the user’s message already states that value unambiguously (same turn as invoking this command).

1. **Discover bench candidates** — directories that look like bench roots (contain `apps/frappe`). Typical layout: `<workspace>/version-15`, `<workspace>/version-16`.
2. **Use the AskQuestion tool** (required when not already given):
   - **Bench** — one option per discovered bench (label: folder name or short path; id: absolute bench root).
   - **App** — see §0.1 below.
   - **Branch for `get-app`** — default option: *Use frappe app branch* (detected in step 1); include **Other** if the user may need a different branch (then ask for the exact branch name in normal chat).
   - **Install Python dependencies** — **Yes** (`--resolve-deps`, preferred) or **No** (omit flag; use `bench pip install` only if a later step needs it).
3. **Free-text follow-up in normal chat** when the user picks **Other**:
   - **App**: GitHub URL (e.g. `https://github.com/frappe/erpnext`) or bare app name for a known Frappe app (resolve to the canonical GitHub URL).
   - **Branch**: exact branch name (e.g. `version-15-hotfix`).

Do not run `bench get-app` until bench, app, and branch are confirmed.

### 0.1 App AskQuestion options

Build the app prompt from context:

- If the user already named an app or URL in their message, do **not** ask again; resolve the URL if needed.
- Otherwise, offer a short list of common apps (resolve ids to canonical GitHub URLs when executing), for example:
  - `erpnext` → `https://github.com/frappe/erpnext`
  - `hrms` → `https://github.com/frappe/hrms`
  - `payments` → `https://github.com/frappe/payments`
  - `webshop` → `https://github.com/frappe/webshop`
- Always include **Other** — then ask in chat for the GitHub URL or bare app name.

After the bench is known, list `<bench-root>/apps/`. If the chosen app folder already exists, use **AskQuestion**: **Skip** (app already on disk) vs **Fetch anyway** (re-run `get-app` to update).

## Dependency installation

- **Do not** use `uv pip install` to install Python dependencies for apps.
- **Do** pass **`--resolve-deps`** on `bench get-app` when the user chose **Yes** above (preferred when fetching).
- If they chose **No**, omit `--resolve-deps`; run **`bench pip install`** from the bench root only if a later step requires dependency install or retry.

## Execution context

- Run all `bench` commands from the selected **bench root** (`cd "<bench-root>" && …`).
- If more than one bench is plausible and the user did not pick one, do not guess — use **AskQuestion**.

## Steps

### 1. Detect branch (when using frappe app branch)

When the user chose *Use frappe app branch*:

```bash
git -C <bench-root>/apps/frappe branch --show-current
```

Use that value (e.g. `version-16`) for `--branch`.

### 2. Fetch the app

```bash
cd "<bench-root>" && bench get-app <url-or-name> --branch <branch> [--resolve-deps]
```

Include `--resolve-deps` only when the user chose **Yes** in §0.

### 3. Confirm success

```bash
ls "<bench-root>/apps/"
```

Report whether the new app directory appears and note any bench CLI warnings.
