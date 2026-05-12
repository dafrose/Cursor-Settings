---
name: frappe-docstrings
description: >-
  Summarizes Frappe Framework Python docstring conventions: Google-style Args/Returns
  (common in frappe.utils and newer modules) vs reST :param/:returns (still widespread
  in core). Use when writing or editing docstrings in Frappe apps, documenting hooks,
  whitelisted APIs, or matching upstream Frappe style.
---

# Frappe docstring formatting

## What the upstream codebase does

Frappe Framework is **mixed**. A quick survey of `apps/frappe/frappe` shows both:

1. **Google-style** (`Args:` / `Returns:` / `Raises:`) with `name (type, optional): description` lines — common in `frappe/utils` (e.g. `frappe/utils/logger.py` `get_logger`, `frappe/utils/data.py` `get_timedelta`), `frappe/types`, `frappe/query_builder`, `frappe/auth.py`, and several `frappe/desk` modules.
2. **reST / Sphinx-style** (`:param name:`, `:returns:`) — still very common in large core areas such as `frappe/model/document.py`, `frappe/database/database.py`, `frappe/__init__.py`, `frappe/client.py`, and many email / integration modules.

There is **no single enforced standard** across the framework. Newer utility APIs tend toward **Google-style**; older or very large modules often keep **reST**.

## Practical guidance for Frappe apps

- Prefer **one style per module**; do not mix `:param` and `Args:` in the same docstring.
- For **new, documented functions** in apps (controllers, `utils.py`, integrations), **Google-style** is a good default: it matches much of modern `frappe.utils`, reads well in IDEs, and does not require `:param` alignment maintenance.
- When **extending or mirroring** a specific Frappe module that already uses reST, stay consistent with **that** module’s style.
- Many hooks and controller methods stay **one-line** summaries; expand to `Args:` / `Returns:` only when parameters or behaviour are non-obvious.

## Google-style template (recommended default for apps)

Use a short summary line, then sections with a blank line after the summary.

```text
"""One-line imperative summary.

Optional longer context (side effects, when this runs, DocType names in bold per team rules).

Args:
	name (type): What it is. Use ``inline code`` for field names and literals.
	other (type, optional): Defaults and behaviour.

Returns:
	type: What the caller gets.

Raises:
	ExceptionType: When.
"""
```

Indentation: match the enclosing function’s indent for continuation lines (Frappe upstream often uses deep indent under `Args:`; consistency within the file matters more than matching every upstream file).

## reST-style template (when matching core modules)

```text
"""One-line summary.

:param name: Description.
:param other: Description.
:returns: Description.
"""
```

## Document events and other hooks

Frappe’s `Document.hook` composer calls string handlers as `handler(doc, method, *args, **kwargs)` where `doc` is the document instance and `method` is the **event name string** (e.g. ``"after_insert"``, ``"on_trash"``). Document the second parameter when it exists, even if unused, so future readers know why the signature cannot be collapsed to `(doc)`.

## DocType and field naming in prose

When docstrings mention Frappe concepts, follow project rules: **DocType** names in bold, _field labels_ in italics, field names in ``inline code``.

## See also

- Examples of **Google-style**: `frappe/utils/logger.py` (`get_logger`), `frappe/utils/data.py` (`get_timedelta`).
- Examples of **reST**: `frappe/model/document.py`, `frappe/database/database.py`.
