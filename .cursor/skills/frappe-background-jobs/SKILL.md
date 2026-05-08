---
name: frappe-background-jobs
description: >-
  Uses frappe.enqueue for DocType-triggered background work, job_name deduplication,
  and test patterns (patch enqueue to run inline). Use when implementing or
  debugging Frappe background jobs, queue workers, on_update hooks that should
  not block the request, or enqueue-related tests.
---

# Frappe background jobs (`frappe.enqueue`)

## When to enqueue

- Heavy or batched work after **`on_update`** / **`on_submit`** (e.g. sync many child rows, external APIs).
- Work that must **not** block the HTTP response or risk **request timeout**.
- Prefer a **single module-level function** as the job target so `frappe.get_attr(path)` is stable.

## Basic pattern

```python
# In DocType controller (e.g. on_update after detecting a real change)
frappe.enqueue(
	"my_app.module.worker.sync_something",
	queue="default",
	job_name=f"sync_something|{self.name}",  # optional dedupe
	doc_name=self.name,
)
```

```python
# worker.py — standalone, whitelisted-safe assumptions
import frappe

def sync_something(doc_name: str) -> None:
	frappe.db.commit()  # only if you opened a transaction intentionally; usually not needed at start
	# ... read DB, frappe.db.set_value / get_doc / bulk updates ...
```

Pass only **JSON-serializable** args (strings, numbers, lists, dicts). Do not pass document objects unless you know the pickle path is acceptable (prefer names/ids).

## Deduplication

Repeated saves (e.g. gate number toggled quickly) can flood the queue. Use a stable **`job_name`** so Frappe can collapse or skip duplicate jobs (behavior depends on version/config; still worth setting for clarity).

## DocType hooks

- Compare **before vs after** in `on_update` using a value captured in **`before_save`** (e.g. `frappe.db.get_value` for existing docs) so you only enqueue when the field **actually** changed.
- Do not enqueue on every save without a guard.

## Tests

Mirror production by **patching** `frappe.enqueue` to call the target immediately:

```python
from unittest.mock import patch

def dequeue(method, **kwargs):
	frappe.get_attr(method)(**kwargs)

with patch("frappe.enqueue", side_effect=dequeue):
	doc.save()
```

Or capture kwargs and assert `job_name` / argument names.

## Permissions

The job runs as the **system** default user context unless you pass `user=` to `frappe.enqueue`. Use **`frappe.db.set_value(..., update_modified=False)`** for system-owned bulk updates when appropriate; use **`ignore_permissions`** on `get_doc` only when necessary and narrow.

## Related

- Realtime notifications after the worker finishes: see skill **frappe-realtime-website**.
