---
name: frappe-testing
description: >-
  Writes and debugs unit tests for Frappe Framework apps using FrappeTestCase,
  central helpers with lazy ensure_* + atexit for all disposable seed rows
  (default bench run-tests), before_tests for scaffolding only, script and
  query report tests, and permission tests via frappe.set_user. Use when
  adding or fixing tests under apps/<app>/**/test_*.py, bench run-tests,
  MandatoryError/.test_log/permission issues, keeping dev test sites free of
  leftover test rows, or asserting Desk **Notification** (**Communication**) or
  **Print Format** PDFs; for notification Jinja use **frappe-notifications**; for
  print sync use **frappe-print-formats**. Do not add test_records.json for
  app-owned seed data — it persists in the site DB with no stock teardown.
---

# Testing Frappe Apps

Patterns for reliable unit tests under a standard `bench` layout
(`apps/<app>/<app>/...`) and Frappe v15-ish runtime.

**Policy:** avoid **`test_records.json`** in the app for seed data — Frappe’s
`make_test_records` **commits** those rows; the stock runner does not remove
them. Use **`tests/helpers.py`** with lazy **`ensure_*()`** and a single
**`atexit`** (or equivalent) cleanup so the site stays clean after
`bench run-tests`.

## Run the suite

```bash
bench --site <site> run-tests --app <app>
bench --site <site> run-tests --module <app>.<dotted.path>.test_module
bench --site <site> run-tests --app <app> --coverage   # writes sites/.coverage
```

There is **no `--verbose`** flag; use `--coverage`, `--profile`, `--failfast`,
`--junit-xml-output`, etc.

## Where tests live

| Location | Use for |
| -------- | ------- |
| `apps/<app>/<app>/<module>/doctype/<dt>/test_<dt>.py` | DocType controller tests (auto-discovered). Frappe still walks **DocType** link dependencies and calls `make_test_records` for them — without `test_records.json` that path inserts nothing but may add the DocType to **`sites/<site>/.test_log`**. |
| `apps/<app>/<app>/<module>/report/<rep>/test_<rep>.py` | Report tests. No automatic record loading for the report module itself. |
| `apps/<app>/<app>/tests/test_*.py` | Cross-cutting tests. |

Use **`test_dependencies = ["DocType A", ...]`** only when you need Frappe to
run **`make_test_records`** for **other** DocTypes (e.g. core / ERPNext fixtures
that still ship with `test_records.json`). Do not use it as a substitute for
your own **`ensure_*`** when this app owns the rows and they must not persist.

## Shared disposable test data: lazy `ensure_*` + `atexit` (standard)

Use with the **stock** `bench run-tests` path.

1. **Central module** — e.g. `<app>/<app>/tests/helpers.py` for factories and
   shared seeds.
2. **Lazy `ensure_*()`** — `frappe.db.exists` / `get_value`; insert only what is
   missing. Safe from `setUp`, `setUpClass`, or inside factories (e.g.
   `create_test_flight()` calls `ensure_test_airports()` first).
3. **Register cleanup once** — first `ensure_*` that touches disposable rows
   calls `register_*_cleanup()`: `if _flag: return` then
   `atexit.register(remove_all_managed_test_data)`.
4. **`remove_*` order** — dependents first (e.g. tickets → flights → airports),
   then users, then masters. Use `frappe.set_user("Administrator")`,
   `force=True` / `ignore_permissions=True` where needed; `commit` on success,
   `rollback` on failure.
5. **Guard teardown** — if `getattr(frappe.local, "db", None)` is missing at
   interpreter shutdown, return early from removers.

**`before_tests` (hooks):** only **durable scaffolding** — custom fields,
**Role** rows, company/currency if required. **Do not** insert disposable **User**
rows, **Airport**s, or other throwaway masters there if the site must stay clean.

**`atexit` tradeoffs:** runs when the test **process** exits normally (not
`kill -9`). Register **one** composite cleanup to control order. Frappe’s runner
has **no `after_tests` hook** — `atexit` is the practical default.

## Helpers: factories and seeds

Per-test or per-class data: factories in `tests/helpers.py`; choose `setUp` vs
`setUpClass` per isolation needs below.

```python
def create_test_flight(*, airplane=None, ...):
    return frappe.get_doc({"doctype": "Airplane Flight", ...}).insert()
```

All **app-owned** seed rows that tests rely on should be created through these
helpers (directly or via **`ensure_*`**) so teardown can delete them.

## Per-test isolation, especially with capacity-like constraints

Frappe wraps each test class in a transaction rolled back at class end, but
**inside one class, state accumulates**. Quotas (e.g. seat capacity): use
`setUp` per test, not `setUpClass`, or later tests fail with opaque
`ValidationError`s.

## The `.test_log` file

`bench` writes `sites/<site>/.test_log` so `make_test_records_for_doctype` can
skip re-processing a DocType. After removing **`test_records.json`** or changing
fixture strategy, **`rm sites/<site>/.test_log`** once if you see odd
`MandatoryError` / skipped inserts while migrating old sites. New policy: do
not rely on this file for app seed data — prefer **`ensure_*`**.

## `before_tests` hook

Wire in `hooks.py`:

```python
before_tests = "<app>.install.before_tests"
```

**Scaffolding only** (roles, custom fields, defaults that should persist). For
disposable seed rows, use **helpers + `ensure_*` + `atexit`**. Idempotent writes;
`frappe.db.commit()` when the hook mutates the DB.

## Permission tests with `frappe.set_user`

```python
import contextlib, frappe

@contextlib.contextmanager
def as_user(user):
    previous = frappe.session.user
    frappe.set_user(user)
    try:
        yield
    finally:
        frappe.set_user(previous)
```

**Gotcha**: `frappe.get_doc(doctype, name)` does **not** raise `PermissionError`
by itself. Assert if-owner / role rules with:

```python
self.assertFalse(frappe.has_permission(doctype, doc=doc, user=u, ptype="read"))
with self.assertRaises(frappe.PermissionError):
    doc.check_permission("read")
```

`frappe.get_list(...)` filters by permissions — good for "can / cannot see row".

## Script reports

Call `execute(filters)` directly. Return `(columns, data, message, chart, report_summary)`.

```python
from <app>.<app>.report.<rep>.<rep> import execute

cols, data, _, chart, summary = execute({})
```

## Query reports

Call the saved **Report** doc:

```python
report = frappe.get_doc("Report", "Add-on Popularity")
columns, data = report.execute_query_report({})
```

Returns `[columns, list_of_row_lists]`. SQL changes: **Desk → Report → Edit**,
then `bench export-fixtures` — do not hand-edit JSON in repo as the only source.

## Common assertion patterns

```python
self.assertRaisesRegex(frappe.ValidationError, "fully booked")
self.assertRaises(frappe.MandatoryError)
self.assertRegex(value, r"^[1-9][0-9]?[A-E]$")
self.assertEqual(doc.docstatus, 1)
```

## Coverage

```bash
bench --site <site> run-tests --app <app> --coverage
```

Output: `sites/.coverage`. Example:
`coverage report --include="*/<app>/*" --omit="*/test_*,*/__pycache__/*"`.
Aim high on controllers and reports.

## Quick troubleshooting

| Symptom | Likely cause | Fix |
| ------- | ------------ | --- |
| `MandatoryError: <link>` | Missing **`ensure_*`** for that link | Add lazy ensure + register cleanup |
| `MandatoryError` on own field (e.g. `airplane`) | Helper did not seed prerequisite | **`ensure_*`** in factory path |
| `ValidationError: fully booked` on later tests | `setUpClass` shares quota | Move creation to `setUp` |
| `PermissionError` not raised on read | `get_doc` ignores perms | `has_permission` / `check_permission` |
| No **Communication** from **Notification** | Jinja / recipient issues | **frappe-notifications**; **Error Log** |
| **Print Format** missing in Desk | wrong sync path | **frappe-print-formats** |
| `ModuleNotFoundError: frappe._dict` | bad import | use `frappe._dict` |
| `--verbose` rejected | flag removed | `--coverage` / `--profile` |

## What goes in code vs. Desk

| Concern | Where |
| ------- | ----- |
| `test_*.py`, `helpers.py`, `install.py`, `hooks.py` | Code |
| Roles for permission tests | **Desk → Role** (not hand-edited JSON) |
| `if_owner` / DocPerm matrix | **Role Permissions Manager** → export fixtures |
| Query report SQL | Desk → export fixtures |

## Reference layout

```
apps/<app>/
├── <app>/
│   ├── hooks.py                       # before_tests = "<app>.install.before_tests"
│   ├── install.py                     # before_tests: roles, custom fields (not disposable seeds)
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── helpers.py                 # factories; ensure_* + atexit for all disposable rows
│   │   └── test_permissions.py       # test_dependencies only if needed for core/ERPNext seeds
│   └── <module>/
│       ├── doctype/<dt>/
│       │   └── test_<dt>.py          # no test_records.json (app policy)
│       └── report/<rep>/
│           └── test_<rep>.py
└── .github/workflows/tests.yml
```
