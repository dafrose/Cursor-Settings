# Set up a new bench for a specific **frappe** branch

Use this when creating a **new** bench directory (not this repo). The bench CLI clones **frappe** at the branch you pass to `--frappe-branch`.

## 0. Gather information (ask first)

Before proposing commands, collect answers as follows:

1. **Use the AskQuestion tool** (required) for every choice that fits clear options:
   - **Frappe branch** — e.g. `version-15`, `version-16`, `develop`, or **Other** (then confirm the exact branch name in chat if needed).
   - **Dev mode** — **Yes** (`--dev`) or **No** (omit).
   - **Backups / cron** — **Yes** (default, omit flag) or **No** (`--no-backups`).
   Optionally use **AskQuestion** for bench location style (e.g. “under `~/frappe/<name>`” vs “custom path”) when you can offer a short list of options.
2. **Bench name / full path** — If not fully determined by AskQuestion (free-text path or folder name), ask once in **normal chat** and confirm spelling.

Do not skip **AskQuestion** for the branch / dev / backups items when the user has not already stated them explicitly in the same message.

Map answers to `bench init` flags:

| Choice | Flag |
|--------|------|
| Dev mode: yes | `--dev` |
| Dev mode: no | *(omit)* |
| Backups: yes (cron) | *(omit)* |
| Backups: no | `--no-backups` |

## 1. Pick the branch and toolchain

Requirements come from **frappe**’s `pyproject.toml` (`requires-python`) and `package.json` (`engines.node`) on that branch. Typical mappings:

| Branch | Python (`requires-python`) | Node (`engines.node`) |
|--------|----------------------------|------------------------|
| `version-15` | `>=3.10,<3.15` (e.g. Homebrew `python@3.12`) | `>=18` (e.g. nvm: `18`) |
| `version-16`, `develop` | `>=3.14,<3.15` (Homebrew `python@3.14`) | `>=24` (e.g. nvm: `24`) |

If a branch differs (e.g. hotfix), confirm on GitHub:  
`https://github.com/frappe/frappe/blob/<branch>/pyproject.toml` and `.../package.json`.

## 2. Install Python with Homebrew

Install the formula that matches the branch (examples):

```bash
brew install python@3.12    # typical for version-15
brew install python@3.14    # version-16 / develop
```

Use the interpreter under the formula prefix so **bench** gets a stable path (Homebrew typically installs `python3.12` / `python3.14`, not `python3`, under this `bin`):

```bash
"$(brew --prefix python@3.14)/bin/python3.14"   # adjust python@X.Y and python3.XY to match what you installed
```

Add that `bin` to your `PATH` in shell config if you want `python3` to resolve to the same build outside of `bench init`; the `--python` flag should still use the explicit `python3.XY` path for clarity.

## 3. Install Node with nvm

Install and select the major version that satisfies the table (examples):

```bash
nvm install 18    # version-15
nvm install 24    # version-16 / develop
```

Do **not** rely on a system-wide Node from Homebrew for this workflow; keep Node on **nvm** only so versions stay explicit and swappable.

## 4. Upgrade bench CLI (recommended)

Use the Homebrew Python you will pass to `bench init` (or a dedicated venv) so `bench` itself is consistent:

```bash
pip install -U frappe-bench
```

## 5. Select Node, then run `bench init`

In the **same terminal session** where you will run `bench init`, load **nvm** and activate the correct Node **first**. That way the initial asset build uses the right Node, and generated paths / your usual `bench start` environment can keep using plain `node` on `PATH` without hand-editing **Procfile** later (as long as you start the bench from a shell where **nvm** is loaded and `nvm use` has been run, or you set a default with `nvm alias default`).

```bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm use 24    # or 18 for version-15; use the major you installed

node -v   # confirm before continuing
```

Replace `<bench-path>` with the new directory, and `<branch>` with e.g. `version-15`, `version-16`, or `develop`.

**version-15** (example: Homebrew `python@3.12`, nvm Node 18):

```bash
bench init <bench-path> --frappe-branch version-15 --python "$(brew --prefix python@3.12)/bin/python3.12"
```

Append **`--dev`** and/or **`--no-backups`** per §0.

**version-16** or **develop** (Homebrew `python@3.14`, nvm Node 24):

```bash
bench init <bench-path> --frappe-branch version-16 --python "$(brew --prefix python@3.14)/bin/python3.14"
```

Append **`--dev`** and/or **`--no-backups`** to the command above according to §0.

Other useful flags (only if the user asks):

- `--dev` — developer mode and dev dependencies (see §0).
- `--no-backups` — skip automatic periodic backups / crontab registration (see §0).
- `--skip-assets` — skip the initial asset build (run `bench build` later with the same `nvm use` active).
- `--no-procfile` — omit `Procfile` if you manage processes differently.

**Example** (`version-15`, dev on, backups on):

```bash
bench init <bench-path> --frappe-branch version-15 --python "$(brew --prefix python@3.12)/bin/python3.12" --dev
```

**Example** (`version-15`, dev off, backups off):

```bash
bench init <bench-path> --frappe-branch version-15 --python "$(brew --prefix python@3.12)/bin/python3.12" --no-backups
```

## 6. After init — verify Python and Node

Sanity-check that the bench matches what you intended:

```bash
cd <bench-path>
./env/bin/python -V
node -v
```

Run `node -v` with **nvm** loaded and the same `nvm use` as during init (or your default). If anything is off, fix Homebrew / nvm selection before building assets or starting processes.

Then add apps with `bench get-app … --branch <branch>` aligned with the **frappe** branch.

## Agent checklist

When helping with this flow:

1. **Gather inputs** (see §0): use the **AskQuestion** tool for **Frappe branch**, **dev mode**, and **backups** unless the user already gave all three in the same message. Collect **bench name / full path** via AskQuestion only when options are clear; otherwise ask in chat.
2. From the toolchain table in §1, state the **Homebrew Python** formula (e.g. `python@3.14`) and **nvm** Node major (e.g. `24`); for unknown branches, suggest checking **frappe** `pyproject.toml` / `package.json` on GitHub.
3. Print a short sequence: `brew install …`, `nvm install` / `nvm use`, then a single `bench init` line that includes `--frappe-branch <branch>`, `--python "$(brew --prefix python@X.Y)/bin/python3.XY"` (use the actual `python3.XY` name from `ls "$(brew --prefix python@X.Y)/bin/"`), and the chosen **`--dev`** / **`--no-backups`** flags. Emphasize **`nvm use` before `bench init`** so Node matches for the first build and avoids **Procfile** edits later, assuming the user runs **bench** from an **nvm**-aware shell.
4. Remind them to **verify** `./env/bin/python -V` and `node -v` after init.
5. Do **not** run `bench init` without confirmation (it creates directories and may need network); prefer giving the exact commands for them to run locally.
