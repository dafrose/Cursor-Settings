---
name: frappe-testing
description: >-
  Writes and debugs unit and integration tests for Frappe Framework apps using
  UnitTestCase, IntegrationTestCase, and FrappeTestCase; prefers parameterized
  tests (unittest.subTest) over loops or duplicate test methods; YAML scenario
  fixtures for matrix tests; central helpers with lazy ensure_* + atexit for
  disposable seed rows (default bench run-tests); addCleanup for per-test DB
  teardown; before_tests for scaffolding only; script and query report tests;
  permission tests via frappe.set_user. Use when adding or fixing tests under
  apps/<app>/**/test_*.py, bench run-tests, MandatoryError/.test_log/permission
  issues, keeping dev test sites free of leftover test rows, or asserting Desk
  **Notification** (**Communication**) or **Print Format** PDFs; testing document
  hooks with patched neighbours, batch/background helpers, and **File** rows;
  for notification Jinja use **frappe-notifications**; for print sync use
  **frappe-print-formats**. Do not add test_records.json for app-owned seed data
  — it persists in the site DB with no stock teardown.
---

# Testing Frappe Apps

## Scope

Use when adding or fixing tests under `apps/<app>/**/test_*.py`, running
`bench run-tests`, or keeping dev sites clean with `ensure_*` + `atexit` instead of
`test_records.json`. For **Notification** or **Print Format** PDF assertions, see sibling skills.

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

## UnitTestCase vs IntegrationTestCase

Frappe ships two base classes (`frappe.tests.UnitTestCase`,
`frappe.tests.IntegrationTestCase`; the latter extends the former):

| Base class | Use for |
| ---------- | ------- |
| **`UnitTestCase`** | Pure logic, mocked `frappe.db` / `get_doc`, whitelisted handlers with patches, content sniffing, validation orchestration |
| **`IntegrationTestCase`** | Real DB reads/writes, DocType insert/delete, proving thin glue (e.g. whitelisted API → `frappe.db.get_value` → helper) |

**Split layers:** keep the fast mocked matrix in `UnitTestCase`; add one
`IntegrationTestCase` class for the smallest slice that needs real rows (often
one accept + one reject case). Do not duplicate the full scenario matrix in both
classes.

Put both classes in the same `test_*.py` when they share fixtures; name the
integration class clearly (e.g. `IntegrationTestOrderApi`).

## Prefer parameterized tests over loops or duplicate methods

When many cases share the same arrange/act/assert shape, use **one test method
+ `unittest.subTest`**, not:

- a `for` loop with bare `assert` inside one test (first failure hides later cases), or
- copy-pasted `test_accepts_pdf`, `test_accepts_png`, … methods.

```python
for scenario in load_scenarios():
    with self.subTest(scenario=scenario.filename):
        ...
```

**subTest** reports which case failed, runs all cases, and needs no pytest.

Reserve **separate test methods** for genuinely different behavior (e.g.
settings toggle, drift guard, missing-file edge case) — not for the same pattern
with different inputs.

For allowlist / matrix-style modules, drive cases from **external data** (YAML
below) rather than hard-coded tuples in the test file.

## YAML scenario fixtures (matrix / allowlist tests)

For fixed input→output matrices (MIME allowlists, validation rules, parser
cases), colocate a YAML file next to the test module and a small loader module:

```
<module>/
  <feature>_scenarios.yaml    # ordered list of scenario dicts
  <feature>_test_helpers.py   # optional: loader + shared asserts
  test_<feature>.py
```

**Why YAML over CSV:** readable diffs, multiline/base64 fields, one scenario per
list entry (block style, one key per line).

**Typical scenario keys:**

- Identity: `filename` (descriptive, e.g. `valid.pdf`, `mislabelled.pdf`), `extension`
- Payload: `content_bytes_b64` (optional; decode in loader)
- Expected outcomes: separate booleans per pathway when they diverge (e.g.
  `accept_extension` vs `accept_validation` — mislabelled files accept on
  extension-only but fail content validation)
- Integration subset: optional `test_integration: true` on rows that need real DB
  (extensible; do not hard-code a required count in the loader)
- Unit mocks: optional `file_id`, `expect_error_contains` for validation rejects

**Loader responsibilities:** `yaml.safe_load` (PyYAML is available via Frappe
bench); validate schema; assert `get_extension(filename) == extension`; decode
base64; return typed dataclasses; filter helpers (`scenarios_with_content()`,
`integration_scenarios()`).

**Drift guard test:** one non-parameterized test that every production constant
entry has ≥1 accepting scenario and YAML accept rows match code (allowlist dicts,
enum sets, etc.). Production code stays source of truth; YAML is test data.

**Test methods (example layout):**

| Method | Class | Data |
| ------ | ----- | ---- |
| `test_allowlist_matches_scenarios` | Unit | all scenarios once |
| `test_extension_only` | Unit | all scenarios, subTest |
| `test_content_sniff` | Unit | scenarios with bytes, subTest |
| `test_validation` | Unit | scenarios with bytes, subTest; mock Frappe I/O only |
| `test_<feature>_from_database` | Integration | `integration_scenarios()`, subTest |

Content validation tests should mock **`frappe.db.get_value` and
`frappe.get_doc().get_content()`** only — not the sniffing/validation helper
under test, or the integration and unit layers duplicate coverage without value.

## Integration test cleanup: `addCleanup` vs `try/finally`

Both run teardown when an assertion or exception fails. Choose by **when**
fixtures must disappear relative to the code under test.

| Use **`self.addCleanup(...)`** | Use **`try/finally`** |
| ------------------------------ | --------------------- |
| Single test method creates rows consumed only by that method | Same test method runs **site-wide** work (bulk job, `get_all` scan, report over whole table) |
| One scenario per method (or split matrix into separate methods) | **`subTest` loop** in one method where each iteration runs site-wide work |
| Teardown can wait until after **`tearDown`** | Next iteration (or next test in class) must **not** see leftover rows from the current case |
| Typical: one doc save, hook on one doc | Typical: bulk migration matrix, any job that queries “all rows matching …” |

**Default:** register **`addCleanup`** immediately after insert, before assertions:

```python
doc = ensure_test_document()
self.addCleanup(delete_test_document, doc.name)
child_file = create_test_file(file_name="sample.png")
self.addCleanup(delete_test_file, child_file.name)
```

`addCleanup` callbacks run after **`tearDown`**, in reverse registration order
(LIFO). Register child rows (e.g. **File**) before parent docs if deletes must
run child-first.

**When site-wide scans apply**, delete before the next case — wrap the iteration
in **`try/finally`**:

```python
for docstatus, include_submitted, expect_migrated in (...):
    with self.subTest(docstatus=docstatus, include_submitted=include_submitted):
        doc, child_file = create_record_with_legacy_field(submit=docstatus == 1)
        try:
            result = bulk_migrate_records(include_submitted=include_submitted)
            ...
        finally:
            delete_test_document(doc.name)
            if child_file:
                delete_test_file(child_file.name)
```

Do **not** use **`addCleanup`** inside such a **`subTest`** loop: all registered
callbacks run only after the **entire** test method finishes, so later
iterations would see rows from earlier ones and counts drift.

**`IntegrationTestCase`** rolls back at class teardown; explicit delete still
helps for **File** disk artifacts and clarity. For many disposable rows across
the suite, keep **`ensure_*` + `atexit`** in `helpers.py` as a backstop.

```python
def _delete_test_file(name: str) -> None:
    if frappe.db.exists("File", name):
        frappe.delete_doc("File", name, force=True)
```

## Patch neighbours to isolate the unit under test

Document `validate` / `before_save` hooks often call several downstream steps.
When testing **one** side effect (row migration, dedup, counter increment), patch
the expensive or unrelated neighbours — not the helper you are unit-testing.

| Goal | Typical patch | Then call |
| ---- | ------------- | --------- |
| Test hook side effect without full downstream validation | the heavy validator the hook invokes | `doc.run_method("validate")` or your wrapper |
| Submit a fixture without unrelated gates | `validate` on the same controller | `doc.submit()` |
| Unit-test a setting branch | `frappe.db.get_single_value` or the branch helper | direct function call |
| Unit-test missing linked row | `frappe.db.get_value` returning `None` | resolver helper |

Patch at the **import site used by the module under test** (where the callee is
looked up), not necessarily where you import it in the test file.

```python
with patch("myapp.my_module.my_controller.run_full_validation"):
    my_controller.validate_doc(doc, "validate")
```

## Settings and durable scaffolding restore

When tests toggle a **Single** (settings DocType) or mutate **Custom Field**
metadata, snapshot previous values in `setUp` and restore in `tearDown`:

```python
def setUp(self):
    super().setUp()
    self._previous = frappe.db.get_single_value("My Settings", "feature_enabled")

def tearDown(self):
    frappe.db.set_single_value("My Settings", "feature_enabled", self._previous)
    frappe.clear_messages()
    super().tearDown()
```

Durable prerequisites (company, customer, role) belong in **`tests/scaffold.py`**
or **`before_tests`**; disposable rows created per test belong in **`helpers.py`**
with **`ensure_*` + `atexit`**.

## Desk message and Error Log assertions

**msgprint / alert:** clear stale messages before the act, then assert on
`frappe.get_message_log()` — count, substring, and `indicator` when UX matters.

```python
frappe.clear_messages()
doc.run_method("validate")
matches = [m for m in frappe.get_message_log() if "moved" in m.message.lower()]
self.assertEqual(len(matches), 1)
self.assertEqual(matches[0].indicator, "orange")
```

**Error Log (silent failure path):** when production logs instead of blocking
save, assert a row exists with `reference_doctype` / `reference_name` and message
content; assert document fields unchanged.

## **File** rows

**File** writes disk as well as DB — always register teardown (`addCleanup` or
managed `delete_*` in `atexit`). Factory pattern:

```python
def create_test_file(*, file_name: str, content: bytes) -> frappe.Document:
    file = frappe.get_doc({"doctype": "File", "file_name": file_name, "content": content})
    file.save(ignore_permissions=True)
    return file
```

For submitted parent documents, **cancel before delete** in teardown; patch
unrelated validation on `cancel()` if the test is not about that path.

## Batch jobs and background helpers

Test the **worker function directly** when asserting counts, partial failure,
and per-row outcomes. Reserve `frappe.enqueue` / whitelisted API tests for
permission and queue wiring.

```python
result = bulk_migrate_records(include_submitted=True)
self.assertEqual(result["migrated"], 1)
self.assertEqual(result["failed"], 0)
```

Use **`subTest`** for docstatus × flag matrices when each iteration is
**isolated** (single-doc tests). When the worker scans the site, use
**`try/finally` per iteration** (see Integration test cleanup above) or split
into separate test methods with **`addCleanup`**.

When the same business rule runs on **save** and in a **batch job**, add at
least one test per entry point (e.g. row-level failure on validate vs counter in
the bulk job return dict).

## Multi-layer features: unit matrix + integration spot checks

For features with a pure transformation layer and a DB glue layer:

| Layer | Class | Data | Mocks |
| ----- | ----- | ---- | ----- |
| **Unit** | `UnitTestCase` | YAML or `subTest` matrix | Frappe I/O at boundaries only |
| **Integration** | `IntegrationTestCase` | one test per distinct behaviour | real inserts; explicit asserts on output shape |

Do **not** duplicate the full YAML matrix in integration tests. Integration
asserts should be explicit on the real output (API response shape, child table
rows, returned dict keys) — not shared “expectation object” helpers unless they
also serve unit tests.

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
| Matrix test fails but unclear which case | bare `for` loop in one test | One method + `subTest(scenario=...)` |
| Leftover **File** rows after integration test | no teardown on assertion failure | `addCleanup` right after insert (or `try/finally` in site-wide matrix loops) |
| Bulk job counts wrong on later matrix cases | `addCleanup` in `subTest` loop; rows accumulate | `try/finally` per iteration, or one test method per case |
| Integration test needs masters site lacks | missing scaffold | `tests/scaffold.py` or `ensure_*` in helpers |
| Hook test fails on unrelated validation | full downstream validator runs | patch neighbour validator; call hook wrapper only |
| Cannot delete submitted test document | cancel blocked by validation | patch validation in `delete_*`; cancel before `delete_doc` |
| msgprint assertion flaky | stale message log | `frappe.clear_messages()` before act |
| Batch partial-failure path untested | only happy-path job test | assert return counters (`failed`, `errors`, etc.) per entry point |
| YAML scenarios drift from allowlist code | no drift guard | `test_*_matches_scenarios` sync test |
| `PermissionError` not raised on read | `get_doc` ignores perms | `has_permission` / `check_permission` |
| No **Communication** from **Notification** | Jinja / recipient issues | **frappe-notifications**; **Error Log** |
| **Print Format** missing in Desk | wrong sync path | **frappe-print-formats** |
| `ModuleNotFoundError: frappe._dict` | bad import | use `frappe._dict` |
| `--verbose` rejected | flag removed | `--coverage` / `--profile` |

## Mandatory fields on Desk saves

DocType fields marked `reqd` (including child-table columns) are enforced by Desk before save. In `validate` / `before_save` hooks triggered by normal form saves, **do not** add `if row.<field>:` guards for those columns — use the value directly. Skip-empty checks belong only on optional fields or untrusted entry paths (REST import, `frappe.get_doc` + `insert` in scripts). Workspace rule: `Don-t-verify-if-mandatory-fields-are-filled.mdc`.

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
│   │   ├── scaffold.py                # optional: durable masters for integration tests
│   │   ├── *_scenarios.yaml        # optional: matrix/allowlist test data
│   │   └── test_permissions.py       # test_dependencies only if needed for core/ERPNext seeds
│   └── <module>/
│       ├── doctype/<dt>/
│       │   └── test_<dt>.py          # no test_records.json (app policy)
│       └── report/<rep>/
│           └── test_<rep>.py
└── .github/workflows/tests.yml
```

## Related skills

- [`frappe-notifications`](frappe-notifications/SKILL.md) — assert email via **Communication** / **Error Log**
- [`frappe-print-formats`](frappe-print-formats/SKILL.md) — PDF tests with `frappe.get_print`
- [`frappe-document-field-changes`](frappe-document-field-changes/SKILL.md) — `has_value_changed` and hook tests
- [`frappe-background-jobs`](frappe-background-jobs/SKILL.md) — patch `frappe.enqueue` in tests
- [`frappe-db-permissions`](frappe-db-permissions/SKILL.md) — permission tests and API choice
