---
name: frappe-system-settings-shipping
description: >-
  Ships changes to Frappe Single DocTypes (System Settings, Website Settings)
  via set_single_value in setup/install.py helpers and thin patches, not full
  Single fixtures. Use when enabling site-wide toggles for Web Forms, guest
  uploads, or other System Settings fields from a Frappe app.
---

# Frappe — shipping System Settings from an app

## Scope

Use when an app needs to set one or a few fields on a **Single** DocType (**System Settings**, **Website Settings**, …) on install or migrate.

Do **not** use for DocType schema (use patches + Desk export / migrate). Do **not** export the full Single as a fixture unless you accept overwriting the entire site config (almost never).

For form defaults from a Single at **new document** time, see [`frappe-form-defaults-from-settings`](frappe-form-defaults-from-settings/SKILL.md).

## Install script location

Put install hooks and shared helpers under a **`setup/`** or **`utils/`** package — not loose at the app root unless the app is tiny and unlikely to grow.

| Path | Use when | Examples |
| --- | --- | --- |
| **`<app>/setup/install.py`** | **Default for apps** — install orchestration, Single defaults, seed data | ERPNext `erpnext.setup.install`; `my_app.setup.install` |
| **`<app>/utils/…`** | Reusable non-install utilities; avoid overloading with install unless the app mirrors framework layout | ERPNext `erpnext.setup.utils` (helpers imported by install) |
| **`frappe/utils/install.py`** | Frappe **framework** only — not a pattern for third-party apps | `add_standard_navbar_items` |
| **`<app>/install.py`** | Very small apps with one hook and no setup surface | `tiny_app.install` — prefer `setup/install.py` when adding patches or more helpers |

Hook registration:

```python
after_install = "my_app.setup.install.after_install"
```

Patch imports:

```python
from my_app.setup.install import enable_guest_file_uploads
```

## Quick rules

1. **One field (or small set)** → `frappe.db.set_single_value("System Settings", "fieldname", value)`.
2. **Put helpers in `setup/install.py`** (or `utils/install.py` only if that matches an established app layout).
3. **Patch `execute()` imports from install** — thin wrapper only (`patch → setup.install`).
4. Register the patch in `patches.txt` under `[post_model_sync]` unless it must run before migrate.
5. Wire `after_install = "<app>.setup.install.after_install"` in `hooks.py`.
6. **Do not** ship `fixtures/system_settings.json` — export is the full Single snapshot; import replaces site-specific config.

## Where helpers live (ecosystem convention)

| Pattern | When | Examples on bench |
| --- | --- | --- |
| **Helper in `setup/install.py`, patch imports install** | Fresh install + existing sites need the change | ERPNext `from erpnext.setup.install import make_default_operations`; Frappe patches import `frappe.utils.install` |
| **Logic inline in patch only** | Migrate-only one-off; fresh install gets same result elsewhere | Many ERPNext `v15_0/*` patches |
| **Patch re-runs full `after_install`** | Small idempotent `after_install` | `execute:from my_app.setup.install import after_install; after_install()` in `patches.txt` |

**Import direction:** `patches/<name>.py` → `setup/install.py`. Do **not** put shared helpers in patch modules and import them from `after_install`.

## Workflow

1. Add helper(s) to `setup/install.py`:

   ```python
   import frappe

   def enable_guest_file_uploads() -> None:
       frappe.db.set_single_value("System Settings", "allow_guests_to_upload_files", 1)

   def after_install() -> None:
       enable_guest_file_uploads()
   ```

2. Add thin patch `patches/enable_guest_file_uploads.py`:

   ```python
   from my_app.setup.install import enable_guest_file_uploads

   def execute() -> None:
       enable_guest_file_uploads()
   ```

3. Register in `patches.txt`:

   ```text
   [post_model_sync]
   my_app.patches.enable_guest_file_uploads
   ```

4. Register in `hooks.py`:

   ```python
   after_install = "my_app.setup.install.after_install"
   ```

5. Document in deploy runbook if ops must **opt out** on shared benches (rare).

## Reference — mechanisms

| Mechanism | Fresh install | Existing site | Scope |
| --- | --- | --- | --- |
| `after_install` | Yes | No (unless re-install) | Runs once on `bench install-app` |
| Patch `execute()` | Yes (on next migrate) | Yes | Runs once per patch version |
| Full Single fixture | Migrate sync | Migrate sync | **Entire** Single — avoid |
| Manual Desk | Anytime | Anytime | Runbook only |

Use **both** `after_install` and a patch when the app may already be installed on staging/production before the setting lands (typical for feature PRs).

## Idempotency

`set_single_value` to a fixed target (e.g. `1`) is idempotent. Optional guard:

```python
if not frappe.db.get_single_value("System Settings", "allow_guests_to_upload_files"):
    frappe.db.set_single_value("System Settings", "allow_guests_to_upload_files", 1)
```

Usually unnecessary when enabling a required product default.

## Pitfalls

- **Fixture export** — `bench export-fixtures` with `{"dt": "System Settings"}` dumps all fields from the export site; re-import on migrate can clobber timezone, language, backup limits, etc.
- **Patch-only on new apps** — sites that installed the app before the patch existed need the patch line in `patches.txt`; `after_install` alone does not run on `bench migrate`.
- **Root-level `install.py`** — works for tiny apps but diverges from ERPNext; move to `setup/install.py` before adding patch imports.
- **Helper in patch module** — inverts Frappe / ERPNext convention.
- **Guest upload toggle** — `allow_guests_to_upload_files` is site-wide; document security review for production (anonymous Web Form attach fields depend on it — see Frappe `handler.upload_file`).

## Example

`my_app`:

- `setup/install.py` — `enable_guest_file_uploads()` + `after_install()`
- `patches/enable_guest_file_uploads.py` — imports helper from `setup.install`, calls it in `execute()`
- Enables **System Settings** → *Allow guests to upload files* for a Web Form that accepts guest file uploads

## Related skills

- [`frappe-form-defaults-from-settings`](frappe-form-defaults-from-settings/SKILL.md) — read Single values into new forms, not site-wide toggles
- [`frappe-web-forms`](frappe-web-forms/SKILL.md) — anonymous Web Forms and guest attach behaviour
- [`command-working-directory-selection`](command-working-directory-selection/SKILL.md) — bench root before `bench migrate` / `install-app`
