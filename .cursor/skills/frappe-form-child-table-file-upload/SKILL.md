---
name: frappe-form-child-table-file-upload
description: >-
  Adds an "Attach file" grid button on Frappe child tables that opens
  FileUploader and appends a row (child-table annex pattern). Covers
  grid.add_custom_button, make_attachments_public vs stock Attach, client vs
  server annex validation, and when programmatic row.file skips the file handler.
---

# Frappe child table — grid attach + upload

Use when a **Table** child field needs an upload shortcut beside **Add row** (not only Link-picker or legacy **Attach** fields).

Reference pattern: a parent form script with a **Table** child field (e.g. `annex_rows` on **Sales Invoice**).

## Grid attach button

Frappe grids expose `frm.fields_dict[<table_fieldname>].grid.add_custom_button(label, click)`.

- Buttons use class `btn-custom` and are **prepended** in `.grid-buttons` (typically appears **before** **Add row**).
- `add_custom_button` is idempotent per label across refreshes (re-shows hidden button).
- Register on `refresh`; guard:
  - `table_field?.grid` exists
  - field not `df.hidden` (feature toggle / custom field visibility)
  - `frm.doc.docstatus === 0` (draft only)
  - any business precondition (e.g. a required profile field is set)

```javascript
setup_annex_grid_attach_button(frm) {
	const table_field = frm.fields_dict.annex_rows;
	if (!table_field?.grid || frm.doc.docstatus !== 0 || table_field.df.hidden) {
		return;
	}
	table_field.grid.add_custom_button(__("Attach file"), () => {
		open_annex_file_uploader(frm);
	});
}
```

## FileUploader for child-table rows

Mirror stock **Attach** upload context so files attach to the parent document:

```javascript
new frappe.ui.FileUploader({
	doctype: frm.doctype,
	docname: frm.docname,
	fieldname: "<table_fieldname>", // metadata only; not a real Attach column
	allow_multiple: false,
	make_attachments_public: frm.meta.make_attachments_public ? 1 : 0,
	on_success: (attachment) => {
		const file_doc = attachment.file_doc || attachment;
		const row = frm.add_child("<child_doctype_table_field>");
		row.file = file_doc.name;
		frm.refresh_field("<child_doctype_table_field>");
	},
});
```

### Require save before upload

If `set_query` on child `file` returns empty filters when `frm.is_new()`, block upload the same way — **File** rows need `attached_to_name`.

### `fetch_from` on child rows

Fields like `file_name` with `fetch_from: file.file_name` populate on save via link validation; no extra client code after upload.

## `make_attachments_public`

**What it does:** Passed into `FileUploader`; each queued file gets:

```javascript
private: !make_attachments_public || !frappe.utils.can_upload_public_files()
```

(`FileUploader.vue` — falsy `make_attachments_public` ⇒ **private** upload.)

Stock **Attach** control sets it from field `make_attachment_public` or falls back to `frm.meta.make_attachments_public` (`attach.js` `set_upload_options`).

| Value | Typical result |
| ----- | -------------- |
| Omitted / `null` | **Private** file (default) |
| `0` | **Private** |
| `1` + user may upload public | **Public** if DocType allows |

**Can it be omitted?** Yes. Omitting always uploads **private** files. Include `frm.meta.make_attachments_public ? 1 : 0` only when annex uploads must match the parent DocType’s public-attachment policy (same as vanilla **Attach** on that form).

## Client vs server validation (annex allowlist)

Three layers in a typical annex allowlist setup:

| Layer | When | Severity | API |
| ----- | ---- | -------- | --- |
| Desk child `file` handler | User picks **File** in grid Link | Orange **msgprint** | `is_extension_allowed_for_file_id` |
| Desk after grid upload | Programmatic `row.file = …` after **Attach file** | Orange **msgprint** | same |
| `validate` on save | Every save when multi-attach is on | **`ValidationError`** (blocks save) | `validate_attachment_file` (extension + optional content) |

### Upload path vs `file` row handler

`frappe.ui.form.on("<Child Doctype>", { file(frm, cdt, cdn) { … } })` runs when the user changes the Link in the grid UI. It usually **does not** run when code sets `row.file` and calls `refresh_field` after **FileUploader**.

So the post-upload `is_extension_allowed_for_file_id` call is **not** redundant with the `file` handler — it covers the upload path. Extract one helper (e.g. `warn_if_extension_disallowed(frm, file_id)`) and call it from both places.

### Client check vs server `validate_attachment_file`

Not redundant:

- Client: early, non-blocking warning (extension only via whitelisted API).
- Server: enforcement on save (extension always; content when app **Settings** enable content validation).

Removing client checks still leaves save-time enforcement; UX degrades (user learns only on save).

## Legacy **Attach** field vs grid button

When multi-attach is on, hide the legacy single **Attach** field and show the table (server-side visibility helper). Do **not** repurpose a hidden **Attach** field’s button — use the grid **Attach file** button instead.

## Checklist

- [ ] `grid.add_custom_button` on `refresh` with visibility guards
- [ ] Save-before-upload if `set_query` blocks new docs
- [ ] `make_attachments_public` — omit (private) or match `frm.meta.make_attachments_public`
- [ ] Shared client allowlist helper for Link change + upload paths
- [ ] Server `validate_attachment_file` in parent `validate` (hard gate)
