---
name: frappe-document-field-changes
description: >-
  Detects and reacts to Frappe Document field changes using has_value_changed,
  get_doc_before_save, is_new/__islocal, and hook placement (before_save vs
  on_update). Use when implementing on_update side effects, avoiding duplicate
  enqueues, seeding fields when another field changes, or debugging “fires on
  every save” / “never fires on insert” behavior.
---

# Frappe Document field changes

## Primary API

- **`doc.has_value_changed(fieldname)`** — compares the current value to **`doc.get_doc_before_save()`** (the row loaded from the DB at save start). Official: [Document API — `has_value_changed`](https://docs.frappe.io/framework/user/en/api/document#dochas_value_changed).
- **`doc.get_doc_before_save()`** — `None` when there is no prior DB snapshot for this save (typical **first insert** path).

## Critical behavior (Frappe Framework)

1. **`has_value_changed` when there is no “before” doc**  
   If `get_doc_before_save()` is `None`, Frappe returns **`True`** for any field (implementation treats missing previous as “changed”). Do **not** interpret that as “the user edited the field” on insert.

2. **`on_update` runs after insert**  
   On `insert()`, Frappe runs **`on_update`** inside the insert lifecycle (before `__islocal` is cleared). So gate-sync / enqueue logic in `on_update` must explicitly handle the **first-persist** case.

3. **`is_new()` vs “insert-time `on_update`”**  
   **`is_new()`** is `bool(self.get("__islocal"))`. During **`on_update` immediately after `insert()`**, `__islocal` is still set, so **`is_new()` is `True`** until the end of `insert()` removes it. For “only skip no-op when no gate on first save”, **`if self.is_new() and not self.get("field"):` return** matches guarding on **`get_doc_before_save() is None`** for normal insert/save flows. Edge case: if `get_doc_before_save()` were `None` on a rare update path, `is_new()` could be `False` while `has_value_changed` still returns `True` — uncommon for standard Desk `get_doc` → `save()`.

## Where to put logic

| Goal | Hook |
|------|------|
| Normalize / derive fields before write (e.g. reset cursor when another field changes) | **`before_save`** — `has_value_changed` works on **updates** once `_doc_before_save` is loaded. |
| Side effects after persist (enqueue, notifications, sync other docs) | **`on_update`** — DB row matches `doc`; safe for `frappe.enqueue` / `db.get_value` of peers. |

## Recommended patterns

**React only when a field actually changed (existing rows):**

```python
def on_update(self):
	if not self.has_value_changed("gate_number"):
		return
	# ...
```

**React on insert only when a value was set (avoid spurious work when `has_value_changed` is always True):**

```python
def on_update(self):
	if self.is_new() and not self.gate_number:
		return
	if not self.has_value_changed("gate_number"):
		return
	# ...
```

Equivalent intent using **`get_doc_before_save()`**:

```python
def on_update(self):
	if self.get_doc_before_save() is None:
		if not self.gate_number:
			return
	elif not self.has_value_changed("gate_number"):
		return
	# ...
```

**Prefer `has_value_changed` over ad hoc snapshots** — avoid storing `self._field_before_save = frappe.db.get_value(...)` in `before_save` unless you need a value that `get_doc_before_save()` does not carry (e.g. computed only in memory).

## Tests

Patch **`frappe.enqueue`** to run the target synchronously or capture kwargs; assert **`has_value_changed`** behavior with a **second `save()`** after changing the field. See skill **frappe-testing** for patterns.

## Related

- **frappe-background-jobs** — enqueue from `on_update` with `job_name` dedupe when reacting to changes.
- **frappe-form-defaults-from-settings** — prefill from a **Single** on Desk **new** forms (`onload` vs `get_single_value`) and **`before_insert`** for mandatory fields.
