---
name: command-working-directory-selection
description: >-
  Picks the correct bench or app directory before shell commands. Use before
  running bench, git, or app-specific tooling; when cwd is ambiguous, ask the
  user which target to use.
---

# Command working directory selection

Before running any shell command, always pick the correct execution context and prepend an explicit `cd "<target-dir>" && ...` unless you are already in that exact directory.

## Directory selection rules

- **Bench operations** (for example `bench --site ...`, migrations, installs, test runs): run from the relevant bench root (for example `<workspace>/version-15` or another intended bench).
- **App git/dependency operations** (for example `git status`, `git commit`, app-specific tooling): run from the relevant app repository root (for example `<workspace>/version-15/apps/<app-name>`).
- **Cross-check commands** (for example checking both bench and app): run each command in its own explicit target directory.

## Ambiguity handling

If the correct bench or app is ambiguous, do not guess. Use the `AskQuestion` tool to ask the user to choose the target directory before running commands.

## Verification

When command results are suspicious or unexpectedly empty, verify context with `pwd` and `git rev-parse --show-toplevel` in the same command chain and correct the target directory before continuing.
