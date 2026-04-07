---
name: frappe-background-jobs
description: >-
  Uses frappe.enqueue for long-running or batched work (job_id, deduplicate,
  long/default queues), Desk messages with RQ Job links, enqueue_after_commit,
  and test patterns. Use when implementing or debugging Frappe background jobs,
  RQ workers, whitelisted actions that must not block the request, on_update
  side effects, or enqueue-related tests.
---

# Frappe background jobs (`frappe.enqueue`)

## Scope

Use when implementing or debugging `frappe.enqueue`, RQ workers, queue choice,
deduplication, Desk **RQ Job** links, or `enqueue_after_commit`. Not for deciding *whether*
a hook should fire on every save (see **frappe-document-field-changes**) or general test layout
(see **frappe-testing**).

Reference: `frappe.utils.background_jobs` (RQ + Redis). Jobs appear in Desk as **RQ Job**.

## When to enqueue

- Work that risks **HTTP timeout** or blocks the UI (bulk migration, many API calls, large loops).
- **DocType hooks** (`on_update`, `on_submit`) where the save response must return quickly.
- Prefer a **module-level function** (dotted path string) as the job target so `frappe.get_attr` is stable in workers.

Do **not** enqueue without a guard on every save — detect real changes first (see skill **frappe-document-field-changes**).

## Split entry point and worker

| Layer | Role |
| ----- | ---- |
| **Whitelisted API** / button handler | `enqueue` with `deduplicate=True`, handle return value, `msgprint`, return `{job_id, queued}` |
| **Worker function** | Heavy logic; no `frappe.whitelist` |

For user-triggered jobs with a stable `job_id`, rely on **`deduplicate=True`** only — do **not** also call `is_job_enqueued` before `enqueue`; that duplicates the same check and still misses races unless you handle a falsy return from `enqueue`.

```python
from frappe import _
from frappe.utils import get_link_to_form
from frappe.utils.background_jobs import create_job_id, enqueue

MY_JOB_ID = "my_app.module.expensive_task"

def run_expensive_task(arg: str) -> None:
	# ... long work ...

@frappe.whitelist()
def expensive_task(arg: str):
	namespaced = create_job_id(MY_JOB_ID)
	job = enqueue(
		"my_app.module.run_expensive_task",
		queue="long",
		timeout=1500,
		job_id=MY_JOB_ID,
		deduplicate=True,
		arg=arg,
	)
	if job:
		frappe.msgprint(
			_("Task queued. Track progress in {0}.").format(get_link_to_form("RQ Job", job.id)),
			indicator="blue",
		)
		job_id = job.id
		is_queued = True
	else:
		frappe.msgprint(
			_("Task already queued. Track progress in {0}.").format(get_link_to_form("RQ Job", namespaced)),
			indicator="orange",
		)
		job_id = namespaced
		is_queued = False
	return {"job_id": job_id, "queued": is_queued}
```

**Desk link:** `job.id` is the namespaced RQ id (`{site}::{job_id}`). **RQ Job** `name` matches `job.id`. Use `get_link_to_form("RQ Job", job.id)` on success; on duplicate (`enqueue` returned `None`), use `create_job_id(MY_JOB_ID)` for the link.

**Client script:** do not `location.reload()` waiting for completion. Optional short `freeze` only while enqueueing:

```javascript
frappe.call({
	method: "my_app.module.expensive_task",
	freeze: true,
	freeze_message: __("Queuing..."),
});
```

## `enqueue` parameters (v15)

| Parameter | Notes |
| --------- | ----- |
| `method` | Dotted path **string** (preferred) or callable |
| `queue` | `short`, `default`, `long` — default timeouts 300s; **long** 1500s unless `workers` in site config overrides |
| `timeout` | Seconds; set above expected runtime for `long` jobs |
| `job_id` | Logical id; stored as `{site}::{job_id}` via `create_job_id` |
| `deduplicate=True` | Requires `job_id`; skips if **queued** or **started**; returns **`None`** (no new job) |
| `enqueue_after_commit=True` | Schedules enqueue on `frappe.db.after_commit` — use when job must not run if transaction rolls back |
| `now=True` | Runs via `frappe.call` immediately (sync), not via worker |
| `**kwargs` | Passed to worker; must be **JSON-serializable** (ids, flags, dicts) — not `Document` instances |
| `user` | Set in `execute_job` with `frappe.set_user`; default is enqueueing user |

**Deprecated:** `job_name` for dedupe — use **`job_id`** + **`deduplicate`**.

**Helpers:**

```python
from frappe.utils.background_jobs import create_job_id, is_job_enqueued, get_job_status

create_job_id("my_app.job")  # link when enqueue returned None (duplicate)
is_job_enqueued("my_app.job")  # optional read-only check in UI/list — not for pre-enqueue guard when using deduplicate
```

**Document method:**

```python
frappe.enqueue_doc("Sales Invoice", "SINV-0001", "submit", queue="default", timeout=300)
```

## Queue choice

| Queue | Typical use |
| ----- | ------------- |
| `default` | Moderate post-save sync, emails, single-doc processing |
| `long` | Migrations, bulk rebuilds, large file/API batches |
| `short` | Quick async tasks |

Ensure workers run: `bench worker --queue long` (and `default` / `short` as needed). Without a **long** worker, `long` jobs sit queued.

## Deduplication

- With `deduplicate=True`, **`enqueue` returns `None`** when the job is already **queued** or **started** (also covers concurrent double-clicks).
- Completed/failed jobs with the same `job_id` are deleted and re-queued on the next enqueue (RQ arg reuse).
- Queue full / Redis errors are separate — `_check_queue_size` may throw; do not assume every falsy return is a duplicate.

## Permissions and DB in workers

- Worker runs **`execute_job`** → `frappe.init(site)` → optional `frappe.set_user(user)`.
- Bulk system updates: `frappe.db.set_value(..., update_modified=False)`; `ignore_permissions` only when narrow and justified.
- Mid-job **`frappe.db.commit()`** in the worker commits outside the test transaction — tests that upload/delete must clean up explicitly.

## DocType hooks

```python
def on_update(self):
	if not self.has_value_changed("status"):
		return
	frappe.enqueue(
		"my_app.workers.on_status_change",
		queue="default",
		job_id=f"on_status_change::{self.name}",
		deduplicate=True,
		name=self.name,
	)
```

Capture “before” state in **`before_save`** if the hook needs the previous value. Hooks often skip `msgprint`; dedupe alone is enough.

## Tests

**1. Test worker logic directly** (no Redis):

```python
controller.run_migrate_existing_files()
```

**2. Test whitelist enqueue** — patch `enqueue` on the **module under test**:

```python
job = MagicMock(id="testsite::my_app.job")
with patch("my_app.module.enqueue", return_value=job) as enqueue_fn:
	result = my_app.module.expensive_task("x")
enqueue_fn.assert_called_once_with(..., job_id="my_app.job", deduplicate=True)

with patch("my_app.module.enqueue", return_value=None):
	result = my_app.module.expensive_task("x")
assert result["queued"] is False
```

**3. Integration-style** — inline dequeue:

```python
def dequeue(method, **kwargs):
	frappe.get_attr(method)(**kwargs)

with patch("frappe.enqueue", side_effect=dequeue):
	doc.save()
```

**4. `now=True` in tests** (optional, runs sync without worker):

```python
enqueue(..., now=frappe.flags.in_test)
```

Do not rely on workers during `bench run-tests` unless the test site runs them.

## Redis unavailable

During **`bench migrate`**, if Redis is down, `enqueue` may **fall back to synchronous** `frappe.call` (logged). Otherwise `ConnectionError` propagates.

## Related skills

- [`frappe-document-field-changes`](frappe-document-field-changes/SKILL.md) — guard enqueues with `has_value_changed` / insert vs update
- [`frappe-testing`](frappe-testing/SKILL.md) — patch `frappe.enqueue` in tests
