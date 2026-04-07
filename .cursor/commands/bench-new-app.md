Scaffold a new Frappe app on an existing bench using `bench new-app`.

**Full workflow:** read skill **`frappe-new-app`** (`.cursor/skills/frappe-new-app/SKILL.md`) — AskQuestion phases, license clarification loop, proprietary defaults, and CI nudge.

## Rules

- **Do not** run `bench new-app` yourself — the wizard is interactive; print the exact command for me to run.
- Follow the skill's **AskQuestion** policy: gather bench, app identity, license intent, and scaffold options before printing the command.
- **Clarify until complete** — especially license intent (open source vs proprietary); re-ask when ambiguous.
- After I confirm scaffold (and proprietary license overwrite if applicable), prompt me to consider CI — skill **`alyf-frappe-app-ci`** for ALYF house apps.

## Quick summary (skill has details)

1. Discover bench roots → **AskQuestion** for bench.
2. Collect app name, title, description, publisher, email.
3. **License loop** — open source (pick SPDX) or proprietary (`mit` placeholder at scaffold, overwrite files after — see skill `reference.md`).
4. Git init, stock GitHub workflow, branch name.
5. Print `cd "<bench-root>" && bench new-app <app_name> [--no-git]` plus prompt cheat sheet.
6. After scaffold: proprietary file fixes if needed → nudge CI setup.
