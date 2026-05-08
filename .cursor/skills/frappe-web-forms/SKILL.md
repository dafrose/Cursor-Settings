---
name: frappe-web-forms
description: >-
  Creates and extends Frappe Web Forms (Desk UI, routes, get_context in companion
  .py, reference_doc defaults from query params, linking from website generators).
  Discourages hand-editing exported web_form JSON. Use when adding or changing
  Web Forms, prefill from URLs, or integrating Book / portal flows.
---

# Frappe Web Forms

## Prefer Desk over editing JSON

- **Do not** hand-edit `**/web_form/**/*.json` in the IDE for normal metadata: fields, labels, read-only, route, title, published, **Is Standard**, module, login rules, and intro text belong in **Desk → Web Form**.
- Reasons: validations run on save, timestamps and exports stay consistent, and the assignment/course workflow expects **you** to own schema in the UI.
- **When the agent would change a Web Form:** stop and **tell the user exactly what to click/enter in Desk** (or use `bench console` if they insist on programmatic DocType-style edits). Reserve repo edits for **controller code** (`.py`) and optional **client script** (`.js`), not the exported `.json` unless the user already edited in Desk and needs a line fix you agree on.

## What each file does

| File | Purpose |
|------|---------|
| `**/*.json` | Exported Web Form definition (Desk is source of truth). |
| `**/*.py` | `get_context(context)` for server-side context: defaults, `reference_doc`, `no_cache`, permission-sensitive logic. |
| `**/*.js` | Client script (Desk **Client Script** field or colocated file); use for DOM, conditional read-only, post-load tweaks. |

## URL shape

- Public route: **`/{route}`** — Desk **Route** on the Web Form (e.g. `book-flight-ticket-web-form`).
- New document: **`/{route}/new`**. Append query args for prefill, e.g. **`?flight=AIRPLANE_FLIGHT_NAME`**. Link from **WebsiteGenerator** detail pages using `frappe.utils.data.quoted` for names in the query string.

## Prefill and `reference_doc`

- **`get_context`** in the Web Form’s Python module runs after core `load_form_data`. It may **return** a dict merged into context (e.g. `reference_doc`).
- For **new** forms only, guard with **`not frappe.form_dict.get("name")`** so existing responses are not overwritten.
- Read query params from **`frappe.form_dict`** (e.g. `flight`).
- Set **`reference_doc`** to a dict including **`doctype`**, link keys, and field values (e.g. **`flight_price`**) so the website bundle hydrates the form.
- If defaults must change every load (random prices, etc.), set **`context.no_cache = 1`** so responses are not cached with stale values.

## Linking from DocType web views

- Define the Web Form **route** once (Desk). In code that builds booking URLs, use the **same** route string (constant or single source) so `/{route}/new?...` never drifts from the exported Web Form.

## Anti-patterns

- Duplicating field lists in markdown instead of “configure these fields in Desk …”.
- Editing **`is_standard`**, **`module`**, or **`web_form_fields`** in JSON without a Desk save in the loop.
- Putting business rules only in JSON; validation belongs in DocType controllers and/or Web Form accept pipeline as appropriate.

## `frappe.has_permission(doctype, doc=…)` vs `Document.has_permission`

`frappe.has_permission` resolves document checks via **`has_permission` hooks** and role/user permission rules — it does **not** call your DocType class’s overridden `has_permission` method. A `Document.has_permission` override only affects `doc.check_permission` / `doc.has_permission` call sites. For API, Desk, and `frappe.has_permission`, implement **`hooks.py` → `has_permission`** (return `False` to deny, `None` to leave evaluation to the rest of the stack). Returning `None` from a **subclass** `has_permission` is also unsafe: `check_permission` treats it like a falsy denial.

## Minimal Desk checklist (for the user)

When scoping a new Web Form, prompt them to confirm in Desk:

1. **Title** (and naming rules such as “ends with Web Form” if the course requires it).
2. **DocType** linked, **Published**, **Route**, **Login required** / **Anonymous** as needed.
3. **Fields** on the form: order, **Read Only**, **Mandatory**.
4. **Client Script** / **Introduction** if needed.
5. **Save**, then **export** or migrate so the app stays in sync—after that, **avoid raw JSON drift** by changing future fields in Desk again.
