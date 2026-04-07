---
name: frappe-form-defaults-from-settings
description: >-
  Prefills DocType fields from a Single (e.g. **App Settings**) on the
  Desk **new** form and on insert: `before_insert` for mandatory fields, client
  `frappe.db.get_single_value` with safe async handling, optional Python `onload`
  only if something reads `__onload`, optional `extend_bootinfo`. Use when wiring
  site-wide defaults into forms, APIs, or imports.
---

# Frappe form defaults from **Single** settings

## Scope

Use when prefilling **DocType** fields from a **Single** (settings) on Desk **new**
forms and on insert—`before_insert`, client `get_single_value`, optional `onload` / `extend_bootinfo`.

## Problem

You store a default in a **Single** DocType (e.g. *Default Amount* on **App Settings**) and want:

- Desk **new** document: user sees the default immediately but can edit.
- **Insert** without the field (API / import / Quick Entry): row still validates (*Rent* can stay **Required**).

## What does **not** work for brand-new Desk forms

**`Document.onload` + `set_onload`** runs when the server loads a document via **`getdoc`** (existing name) or when **`savedocs`** runs **`run_onload`** after save. A **new** row is created in the browser (`__islocal`); the first **`refresh`** usually has **no** `doc.__onload` from that hook. Do **not** rely on `frm.doc.__onload` alone to prefill **new** forms.

## Server: apply default before mandatory validation

On **`insert()`**, Frappe runs **`before_insert`** then **`_validate()`** (including mandatory checks). Use **`before_insert`** to set the field when it is still empty / zero so **Required** fields stay required on the schema.

```python
from frappe.utils import flt

def before_insert(self):
	if flt(self.rent) > 0:
		return
	default = frappe.db.get_single_value("App Settings", "default_amount")
	if default is not None:
		self.rent = default
```

**If nothing reads `doc.__onload`**, omit **`onload`** on the controller entirely — **`before_insert`** plus the form script (or boot) is enough. Add **`onload` + `set_onload`** only when another consumer needs that payload after **`getdoc`** / post-save load (custom print, another script, etc.); it is **not** required for Desk **new**-form prefill.

## Desk client: **new** form prefill

Use **`frappe.db.get_single_value(doctype, field)`** in the form script (e.g. **`refresh`** when **`frm.is_new()`**). It returns a **Promise**; the form can change before it resolves.

**Pattern:**

1. Skip if not new, field already set, or a **pending** fetch is already in flight (avoids duplicate requests on repeated `refresh`).
2. Set **pending** = true, then call **`get_single_value`**.
3. In **`.then`**: one guard — **`!frm.doc || !frm.is_new() || flt(frm.doc.rent) > 0`** — then **`frm.set_value`** (user may have typed *Rent* or closed the form).
4. **`.finally`**: clear **pending** (including on error).

Do not duplicate the same “is new / rent empty” checks inside `.then` beyond what’s needed for **async races**; the **pending** flag replaces a separate “already applied” flag for deduping in-flight work.

## Optional: no extra HTTP call

**`hooks.py` → `extend_bootinfo`** (or `update_website_context`) can inject `frappe.boot.app_default_amount` so the form script reads from boot instead of **`get_single_value`**. Tradeoff: boot payload size and freshness vs one small `get_single_value` per new form.

## Tests

- **`before_insert`**: `insert` a doc **without** the field; assert it matches **`frappe.db.set_single_value`** / known value; restore single in **`finally`**.
- **Explicit value**: insert **with** the field set; assert settings default did **not** overwrite.
- **`onload`** (if kept): **`from frappe.desk.form.load import run_onload`**, **`run_onload(doc)`** on a **saved** doc, assert **`doc.get_onload("your_key")`**.

## When to use this skill

- Wiring **Single** (or other global) defaults into a **Link** / standard DocType form.
- Debugging “default never appears on **New**” or double-fetch / overwrite issues in **`refresh`**.

## Related skills

- [`frappe-document-field-changes`](frappe-document-field-changes/SKILL.md) — reacting when a user changes a field after load
