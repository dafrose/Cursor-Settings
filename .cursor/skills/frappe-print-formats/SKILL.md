---
name: frappe-print-formats
description: >-
  Covers standard **Print Format** layout (`<module>/print_format/…/….json`),
  **fixtures**, **`bench migrate`** sync, optional Print Designer
  **default_templates**, **Jinja** body (`doc`, **Bootstrap**, **Custom CSS**
  hooks), **`doc.get_formatted`**, **frappe.get_print** PDF tests. Use when
  authoring or shipping receipts/invoices as PDF, styling print output, or when
  formats on disk never appear in the DB.
---

# Frappe **Print Format** and PDF in apps

**Default (no Print Designer app):** ship formats as **`…/<module>/print_format/<scrub(name)>/<scrub(name).json>`** plus optional **`fixtures`** (`"Print Format"` in `hooks.py`). Do **not** expect **`default_templates/*.json`** to load by itself.

## Two on-disk conventions

| Convention                 | Typical path                                                   | When it appears                                                                                                                                                                                                                                                                                                                                                       |
| -------------------------- | -------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Standard (core Frappe)** | `<app>/<module>/print_format/<scrub(name)>/<scrub(name).json>` | **Desk** saves a **standard** format in developer mode; `export_module_json` (`frappe/modules/utils.py`) writes here. Synced with normal **module import / `bench migrate`**. **Use this when Print Designer is not installed.**                                                                                                                                      |
| **Print Designer export**  | `<app>/<pd_folder>/<scrub(doctype_app)>/*.json>`               | Only when **Print Designer** is installed: override on **Print Format** (`print_designer/.../overrides/print_format.py`) writes under `print_designer_template_app` + **`pd_standard_format_folder`** (default **`default_templates`**). Auto-import on app install uses **`install_default_formats`** — **irrelevant if Print Designer was removed from the bench.** |

`default_templates/...` is **not** core Frappe magic; without Print Designer + hook-driven import, treat leftover files as **legacy** and move the source of truth to **`print_format/`** or **fixtures**.

## How JSON gets into the database

1. **`bench migrate` / install** — Imports standard module JSON (including **`print_format`** tree when present).
2. **`fixtures`** in `hooks.py` — List **`"Print Format"`** and run **`bench export-fixtures`**. Prefer this for reproducible CI and clones even when **`print_format/`** exists.
3. **Print Designer `install_default_formats`** — **Only if** the **print_designer** app is installed: **`after_app_install`** (`print_designer/install.py` → `default_formats.py`) imports from **`print_designer/default_templates/<app>/`** and, when your app sets **`pd_standard_format_folder`**, from **`<your_app>/<pd_folder>/<installed_app_name>/`**. Skip this entire bullet when Print Designer is not on the site.
4. **Patches / one-off `import_file_by_path`** — Idempotent upserts on long-lived sites.

If JSON never appears in Desk: confirm **`print_format/`** path and module, run **migrate**, add **fixtures**, and verify you did not rely on **`default_templates`** alone after removing Print Designer.

## Authoring tips

- **`print_designer`: 1** with empty designer JSON but **`html`** set can route rendering through designer hooks; for **plain Jinja + `html`**, prefer **`print_designer`: 0**, **`custom_format`: 1**, **`print_format_type`**: **Jinja** (unless you intentionally use Print Designer).
- Strip **`__unsaved`**, **`__onload`**, and other non-field keys before programmatic **`insert`** / **`import_file_by_path`**.
- **Letter head**, margins, and **Print Settings** (“allow print for draft”) affect Desk PDF and `get_print`.

## Jinja **HTML** body (matches Desk “Print Format Help”)

- **Server-side Jinja** in the **Print Format** **`html`** (and subject where templated). The template receives **`doc`**: the document being printed (full `Document` API where applicable).
- **`frappe`** is available for common utilities (e.g. **`frappe.db.get_value("Doctype", name, "fieldname")`** for lookups). This is **printview** context — broader than **Notification** email safe-Jinja; still avoid fragile patterns in production.
- **Bootstrap** CSS is included for the print page: use grid/helpers (`row`, `col-md-*`, `table`, `table-bordered`, `text-right`, etc.).
- **Formatted values:** **`{{ doc.get_formatted("fieldname") }}`** renders dates, currency, etc., with correct options. On **child table** rows, pass the parent for currency-style fields: **`{{ row.get_formatted("amount", doc) }}`** (Desk example pattern for **Sales Invoice**-style `items`).
- **Child tables:** `{% for row in doc.items %}` (replace `items` with your table fieldname); use **`row.idx`**, **`row.fieldname`**, conditionals as in normal Jinja.
- **Optional heading field:** some DocTypes use a select for print title, e.g. **`{{ doc.select_print_heading or "Invoice" }}`** — use only if the field exists on your DocType.

Official references (Frappe / upstream): [Jinja](https://jinja.palletsprojects.com/), [Bootstrap 3 docs](https://getbootstrap.com/docs/3.3/) (version shipped with Desk may vary slightly).

## **Custom CSS** (Desk “Custom CSS Help”)

Frappe wraps auto-generated field markup so you can target groups without hand-writing every label:

| Hook                     | Meaning                                                      |
| ------------------------ | ------------------------------------------------------------ |
| Each label + value group | **`data-fieldtype`** and **`data-fieldname`** on the wrapper |
| Value cells              | Class **`value`**                                            |
| **Section Break**        | Class **`section-break`**                                    |
| **Column Break**         | Class **`column-break`**                                     |

Examples (from Desk help):

```css
/* Left-align integer fields */
[data-fieldtype="Int"] .value {
  text-align: left;
}

/* Separator styling between sections */
.section-break {
  padding: 30px 0;
  border-bottom: 1px solid #eee;
}
.section-break:last-child {
  padding-bottom: 0;
  border-bottom: none;
}
```

Put these in the **Print Format** **CSS** field (`css` in JSON). Combine with custom **`html`** when **`custom_format`** is set for full control, or use CSS alone to tweak the standard layout.

## PDF in code and tests

- **`frappe.get_print(doctype, name, print_format, as_pdf=True)`** (`frappe/utils/print_utils.py`) builds HTML via **printview**, then **`get_pdf`** (wkhtmltopdf by default unless **`pdf_generator`** / hooks say otherwise).
- Smoke assertion: **`result[:4] == b"%PDF"`** when `as_pdf=True`. Use **`as_pdf=False`** to assert substrings in HTML.
- CI / dev must have a working **PDF stack** (e.g. **wkhtmltopdf**); otherwise PDF steps fail while HTML still works.

## Attach / portal

- **`frappe.attach_print`** returns an in-memory file payload (`fname`, `fcontent`) for mail pipelines and custom handling.
- **Important:** attaching print in a Desk **Notification** (`attach_print: 1`) includes a PDF in outbound email, but does **not** create a **File** row on the source document timeline by itself.
- To persist on timeline/attachments, call **`save_file`** with the bytes from `attach_print` and `attached_to_doctype` / `attached_to_name` (or equivalent arguments), and skip duplicate **File** names if you need idempotency.
- Portal: reuse **printview** URL or a whitelisted method that returns **`get_print`** PDF bytes with permission checks.

## `in_print` flag and post-print writes

- During print rendering, Frappe sets **`doc.flags.in_print = True`** in `printview`.
- `Document.insert` / `Document._save` short-circuit when this flag is set, so writes can silently no-op on that same in-memory `Document`.
- If you pass a live doc to `attach_print` / `get_print` and then need to `save()` / `cancel()` it in the same flow, clear the flag first (`doc.flags.in_print = False`) or reload a fresh document instance.
- Practical symptom: submit path that prints first, then cancel/save later on the same object appears to "not persist" (docstatus/status unchanged in DB).
- In tests around submit/cancel plus printing, a robust fallback sequence is: `cancel()` → `reload()` → if still not cancelled, `save()` + `frappe.db.commit()` + `reload()` (usually unnecessary once `in_print` is cleared correctly).

## Jinja vs **Notification** email templates

- **Print** HTML is rendered in the **printview** Jinja context (full **`doc`**, helpers for print). It is **not** the same restricted **`get_safe_globals()`** environment as **Notification** email bodies—do not assume the two behave identically.

## Related

- **frappe-testing** — `FrappeTestCase`, `bench run-tests`, fixtures.
- **frappe-notifications** — Safe Jinja for **Notification** emails only.
