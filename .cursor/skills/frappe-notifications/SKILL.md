---
name: frappe-notifications
description: >-
  Explains how Desk **Notification** documents hook into document lifecycle, how
  email channel renders Jinja in a sandboxed environment, common silent-failure
  modes, and how to assert behavior in tests (Communication / Error Log). Use
  when authoring or debugging **Notification** rows, email templates for alerts,
  recipient conditions, or tests that expect notifications to fire on **New** /
  **Save** / submit events.
---

# Frappe Desk **Notification** (email) and testing

## When notifications run

- `Document.run_method` calls `run_notifications(method)` after the user hook (`after_insert`, `on_update`, etc.).
- `run_notifications` maps method names to **Notification** `event` values, e.g. `after_insert` → `"New"`, `on_update` → `"Save"`, `on_submit` → `"Submit"` (`frappe/model/document.py`).
- Enabled rows are loaded with `frappe.get_all("Notification", filters={"enabled": 1, "document_type": self.doctype})` and cached under `frappe.cache.hget("notifications", self.doctype)`. After changing a **Notification** in code or DB, clear that cache or restart workers if behavior looks stale.

## Email channel and **Communication**

- For `channel == "Email"`, `Notification.send_an_email` renders subject and message, resolves recipients, then creates a **Communication** via `frappe.core.doctype.communication.email._make` with `communication_type="Automated Message"` and `send_email=False`, then passes the communication name into `frappe.sendmail` (`frappe/email/doctype/notification/notification.py`).
- A practical integration assertion: after the triggering `insert()` / `save()`, query **Communication** with `reference_doctype` / `reference_name` matching the source document and `communication_type="Automated Message"`.

## Recipients

- `get_list_of_recipients` evaluates each child row’s **condition** with `frappe.safe_eval(..., context)` where `context` includes the live `doc` and `alert` (**Notification**).
- `receiver_by_document_field` reads `doc.get(field)`; values are split on commas for multiple addresses; each segment is validated with `validate_email_address`. If the condition is false or the field is not a valid email, **no email path runs** and no **Communication** is created for that attempt.

## Jinja: sandboxed globals (common pitfall)

- Message and subject are rendered with `frappe.utils.jinja.render_template`, which uses the same Jinja environment as other safe templates: globals come from `get_safe_globals()` (`frappe/utils/safe_exec.py`), not the full Python **`frappe`** module.
- **Works** in templates: e.g. `frappe.db.get_value`, `frappe.db.get_default`, `frappe.utils.fmt_money`, `frappe.utils.format_date`, and other utilities exposed on the limited `frappe` / `frappe.utils` namespaces.
- **Often breaks at runtime** (Jinja error → no mail, no **Communication**): `frappe.defaults.get_user_default`, `frappe.utils.get_defaults()`, or anything not on the safe namespace. Prefer **`frappe.db.get_default("currency")`**, **`frappe.db.get_default("company")`**, or explicit fallbacks instead of full **defaults** APIs.

## Silent failures

- `send_notification_by_channel` wraps the channel send in `try/except Exception` and calls `log_error("Failed to send Notification")` without re-raising. Template errors therefore produce **Error Log** entries and **no** **Communication**.
- When a test expects a **Communication** but gets none, check **Error Log** for that title/message and fix the template or recipient configuration.

## Testing patterns

1. Ensure the **Notification** document exists on the site (fixtures / `test_dependencies` including `"Notification"`, or `skipTest` if missing).
2. Enable the notification for the test if needed (`frappe.db.set_value(..., "enabled", 1)`), restore in `finally`.
3. Perform the action under test (e.g. `get_doc(...).insert()`).
4. Assert **Communication** rows as above (or patch `Notification.send` / `send_an_email` if you only need a unit-level signal).
5. In `tearDown`, delete those **Communication** documents before deleting the primary document to avoid orphans.

## Manual debugging

- `frappe.get_doc("Notification", name).send(frappe.get_doc(doctype, docname))` reproduces the email path; pair with a reloaded `doc` so fetched fields match DB.
- After editing exported notification JSON or `.md` message files, sync the database record (migrate, import, or `db.set_value` on **Notification**.`message`) so the site under test matches the repo.

## Related

- General Frappe tests: skill **frappe-testing**.
