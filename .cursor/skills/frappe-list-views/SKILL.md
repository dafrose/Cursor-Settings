---
name: frappe-list-views
description: Edits Frappe DocType list views, including colocated `*_list.js` files, `frappe.listview_settings`, custom `get_indicator`, and draft status indicators. Use when changing list badges, list actions, columns, filters, or list behavior for a DocType.
---

# Frappe List Views

## Quick Rules

- For colocated list views, you do not need to set a hook. Also, it is enough to set "has_indicator_for_draft = true" to enable the status indicators.
- Prefer colocated list scripts at `<app>/<module>/doctype/<doctype>/<doctype>_list.js`.
- Only use `doctype_list_js` in `hooks.py` when the list script is not colocated.

## Workflow

1. Locate the DocType folder and check whether `<doctype>_list.js` already exists.
2. Add or edit `frappe.listview_settings["<DocType>"]`.
3. For status badges on draft docs, set:

```javascript
frappe.listview_settings["<DocType>"] = {
  has_indicator_for_draft: true,
};
```

4. If custom badge text/color is needed, implement `get_indicator(doc)`.
5. Keep filters aligned with badge logic (for example, `status,=,Paid`).
6. Reload Desk and verify badges in list view.

## Minimal Patterns

```javascript
frappe.listview_settings["Shop Rent Payment"] = {
  has_indicator_for_draft: true,
};
```

```javascript
frappe.listview_settings["Shop Rent Payment"] = {
  has_indicator_for_draft: true,
  get_indicator(doc) {
    if (doc.status === "Paid") {
      return [__("Paid"), "green", "status,=,Paid"];
    }
    return [__("Due"), "red", "status,=,Due"];
  },
};
```
