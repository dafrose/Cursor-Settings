# frappe-new-app — reference

## Proprietary license defaults

Apply **immediately after** `bench new-app` when license intent is proprietary, **before
the first commit or push**. Adapt copyright holder and year; confirm text with legal if
needed.

### `license.txt`

Replace scaffold MIT text entirely:

```text
Copyright (c) <year> <Publisher>. All Rights Reserved.

This software and associated documentation files (the "Software") are the
proprietary property of <Publisher>.

Unauthorized copying, modification, distribution, or use of this Software,
in whole or in part, is strictly prohibited without prior written permission
from <Publisher>.
```

Example (proprietary app):

```text
Copyright (c) 2026 Example Corp GmbH. All Rights Reserved.

This software and associated documentation files (the "Software") are the
proprietary property of Example Corp GmbH.

Unauthorized copying, modification, distribution, or use of this Software,
in whole or in part, is strictly prohibited without prior written permission
from Example Corp GmbH.
```

### `hooks.py`

```python
app_license = "Proprietary"
```

### `pyproject.toml`

Under `[project]`, add (or replace any MIT / SPDX license line):

```toml
license = { file = "license.txt" }
```

### `README.md`

Replace the scaffold `### License` section (often literally `mit`):

```markdown
### License

Proprietary. See [license.txt](license.txt). All rights reserved by <Publisher>.
```

## Post-scaffold checklist

| Step | Action |
| --- | --- |
| 1 | Verify `apps/<app_name>/` on bench |
| 2 | Proprietary: apply four files above |
| 3 | Open source: confirm `license.txt` matches chosen SPDX id |
| 4 | Review `.gitignore`, remote origin, repo visibility (private if proprietary) |
| 5 | Consider CI — [`alyf-frappe-app-ci`](../alyf-frappe-app-ci/SKILL.md) |
| 6 | First commit only after license reflects intent |

## Open-source license quick reference

| SPDX (scaffold) | Use when |
| --- | --- |
| `mit` | Default Frappe / ALYF permissive OSS |
| `apache-2.0` | Permissive + explicit patent grant |
| `gpl-3.0` | Strong copyleft |
| `agpl-3.0` | Copyleft + network use (SaaS) |
| `bsd-3-clause` | Permissive, attribution clause |

**Not suitable for closed source:** any row above, plus `bsl-1.0` (source-available, not
proprietary), `cc0-1.0`, `unlicense` (public domain).

## Example end-to-end summary (agent output)

**Collected values**

| Setting | Value |
| --- | --- |
| Bench | `…/version-16` |
| App name | `my_custom_app` |
| Title | My Custom App |
| Publisher | Example Corp GmbH |
| License intent | Proprietary (scaffold placeholder: `mit`) |

**Command (user runs)**

```bash
cd "/path/to/version-16" && bench new-app my_custom_app
```

**At prompts:** enter collected title, description, publisher, email; choose `mit` at
license; No for stock GitHub workflow unless decided otherwise; branch `version-16`.

**After scaffold:** apply proprietary defaults → consider **alyf-frappe-app-ci** or org CI.
