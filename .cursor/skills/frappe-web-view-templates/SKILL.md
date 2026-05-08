---
name: frappe-web-view-templates
description: >-
  Builds and fixes Jinja templates for Frappe DocTypes with Has Web View (list,
  row, detail). Covers extending templates/web.html, portal list integration,
  get_list_context, and avoiding unstyled or broken website pages. Use when
  editing doctype templates under doctype/*/templates/, WebsiteGenerator
  controllers, /flights-style routes, or when website list/detail pages look
  plain or lack navbar/theme CSS.
---

# Frappe Web View templates (Has Web View)

## Mental model

| Template | Role |
|----------|------|
| **`www/portal.html`** (Frappe) | Renders **DocType list** URLs. Extends `templates/web.html` and **`{% include list_template %}`** in `page_content`. |
| **`*_list.html`** | Your **list body** (included by portal). Must work with **`templates/includes/list/list.html`** (`.website-list` → `.result`). |
| **`*_row.html`** | One **HTML fragment** per row; appended into `.result` (and by “More” AJAX). |
| **`*_detail.html` / `doctype.html`** | **Detail** page for one document; should **extend** `templates/web.html` and fill **`{% block page_content %}`**. |

## When list pages look “plain” (no theme / no real website chrome)

The standard list partial **`{% include "templates/includes/list/list.html" %}`** only outputs the **inner** list (filters, empty state, `.website-list`). Depending on **how** the page is resolved, a list-only fragment may render **without** the normal `web.html` shell (navbar, container, CSS hooks).

**Reliable pattern** (wrap the standard list include in the full website layout):

```jinja
{% extends "templates/web.html" %}
{% block page_content %}
{% include "templates/includes/list/list.html" %}
{% endblock %}
```

Use this in your app’s **`*_list.html`** when the naked include is unstyled. **Do not** edit Frappe’s core `templates/includes/list/list.html`.

**After template changes:** `bench clear-cache` (or hard refresh) so the website picks up Jinja changes.

## List template requirements

1. **Prefer** including Frappe’s list partial so you keep **`.website-list`**, **`.result`**, and the **“More”** button behaviour (`list.js` appends into `.website-list .result`).
2. **Do not** replace `.result` with only a `<table><tbody>` unless you also give the tbody **`class="result"`** (or equivalent) so pagination JS still finds the container.
3. **`get_list_context`** (module-level function in the DocType’s `.py`): Portal expects **`list_template`**; Frappe’s `get_list_context` often sets **`template`** from meta. Set **both** to your `*_list.html` path when you customize, or the include can fail silently / look wrong.

## Row template (`*_row.html`)

- Treat as a **fragment** (no `extends`).
- Use Frappe’s **`web-list-item`** wrapper so rows match portal/website patterns.
- Avoid **nested Bootstrap `.row`** inside the portal main column (negative margins break layout). Prefer **`d-flex`**, **`flex-wrap`**, **`gap-*`**.

## Detail template

- **`{% extends "templates/web.html" %}`** + **`{% block page_content %}`** is the normal pattern for generator detail pages.
- Optional: override **`title`** in **`get_context`** on the DocType class.

## DocType metadata (do not hand-edit JSON in Cursor)

Use Desk or `bench console` to set **Has Web View**, **`is_published`**, **`route`** (e.g. list slug `flights`), **`allow_guest_to_view`**, etc., per project rules.

## Checklist for new web views

- [ ] List: `*_list.html` includes standard list (optionally wrapped in `extends` + `page_content` as above).
- [ ] Row: `*_row.html` uses `web-list-item`; links use **`/ {{ route }}`** (see `frappe.www.portal.set_route`).
- [ ] Detail: extends `web.html`; `get_context` if needed.
- [ ] Python: `get_list_context` sets title, `order_by`, `template` + `list_template`, filters for published docs.
- [ ] Cache cleared after edits.
