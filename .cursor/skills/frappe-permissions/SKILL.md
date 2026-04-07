---
name: frappe-permissions
description: >-
  Explains Frappe Framework permission layers (Role / DocPerm, User Permission,
  controller has_permission, hooks), how they combine, and common pitfalls
  (User API, test users, hook ordering, permlevel, Role Profile blocking role
  changes). Use when designing Desk or portal access, debugging "Not permitted",
  User Permission sync, or choosing between has_permission hooks and
  document-driven role grants.
---

# Frappe permission system (practical)

## Scope

Use when designing Desk or portal access, debugging "Not permitted", User Permission
sync, or choosing between `has_permission` hooks and document-driven grants. For which DB APIs
skip checks by default, see **frappe-db-permissions**.

Frappe resolves **read / write / submit / …** in layers. Know which layer you are changing; mixing them without a clear model causes "works on my machine" bugs.

## Layers (evaluation order matters conceptually)

1. **Administrator** — `frappe.session.user == "Administrator"` bypasses checks (use sparingly in app code).
2. **DocType controller `has_permission`** — if defined on the DocType class, can allow or deny before generic rules; return `True` / `False` / `None` (`None` = defer to default).
3. **Role permissions (DocPerm)** — rows on **Role** linked to **DocType** (read, write, create, delete, submit, cancel, amend, report, import, export, print, email, share). Optional **If Owner** restricts to documents where `doc.owner == session.user`.
4. **User Permissions** — named rows: user, allow (DocType), for_value (document name), optional **Applicable for** (child DocType), **Is Default**, deny rules, **Apply to All Document Types**. They **restrict** which linked values the user may use or see on many DocTypes (not a full RBAC tree by themselves).
5. **Share** — per-document share rows; augments access for specific users.
6. **Hooks `permission_query_conditions` / `has_permission`** — global overrides; powerful and easy to get wrong (performance, predictability, test isolation).

**Website / portal:** same user is still a **User** document; **Website User** flag and roles like **Guest** / custom portal roles control what `frappe.session.user` can do. Do not assume Desk-only Role profiles apply to portal unless that user has those roles.

## `check_permission` vs `has_permission` (predicate vs enforcement)

Frappe exposes two parallel APIs for the same permission stack — one returns a boolean, the other raises. Pick based on whether you want to **branch** or **stop**.

| API | Returns | Raises | Use for |
| --- | --- | --- | --- |
| `frappe.has_permission(doctype, ptype, doc=None, user=None)` | `bool` | no (unless `throw=True`) | Predicate — gate UI, conditionally enqueue, fall back to alternate flow |
| `doc.has_permission(permtype="read", user=None)` | `bool` | no | Predicate on an existing **Document**; honors `doc.flags.ignore_permissions` |
| `doc.check_permission(permtype="read", permlevel=None)` | `None` | `frappe.PermissionError` (localized message) | Enforcement at trust boundaries — entry of whitelisted methods, before destructive side effects |
| `frappe.has_permission(..., throw=True)` | `bool`/raises | `frappe.PermissionError` | Same enforcement but when you only have a `doctype` + `name`, not a loaded **Document** |

**Prefer `check_permission` (or `throw=True`)** at the **entry point** of any code path that bypasses Frappe's built-in `insert` / `save` / `submit` checks: custom `@frappe.whitelist` methods, scheduler jobs that act on user input, portal endpoints, bulk actions. The raised `frappe.PermissionError` carries a localized "You need the '{perm}' permission on {DocType} {name}" message that Desk and the request handler render correctly.

**Prefer `has_permission`** when access is just one input to a decision: hiding a button, choosing between read and write paths, deciding whether to enqueue a notification, returning a redacted vs full payload.

```python
@frappe.whitelist()
def cancel_booking(name: str):
    doc = frappe.get_doc("Ride Booking", name)
    doc.check_permission("write")
    ...

def get_dashboard_actions(name: str):
    doc = frappe.get_doc("Ride Booking", name)
    return {
        "can_cancel": doc.has_permission("write"),
        "can_invoice": frappe.has_permission("Sales Invoice", "create"),
    }
```

Notes:
- `doc.check_permission` internally calls `doc.has_permission`, which short-circuits on `doc.flags.ignore_permissions`. That flag is the deliberate escape hatch for trusted server paths — see `ignore_permissions=True` below.
- Do **not** wrap `check_permission` in `try/except frappe.PermissionError` to convert it back into a bool. Use `has_permission` directly; catching the exception just to flip it loses the localized message and confuses error logs.
- Frappe's own `insert` / `save` / `submit` / `cancel` already call `check_permission` for you. Adding another `check_permission("write")` inside `before_save` is redundant and only useful at custom entry points.

## Typical pitfalls

### `User` has no `has_role` in server-side code paths

Core **User** is a standard DocType. Roles hang off **`user.roles`** (child table **Has Role**), not a `user.has_role("Role Name")` method on the ORM object. Prefer:

```python
role_names = {r.role for r in (frappe.get_doc("User", email).roles or [])}
if "Some Role" in role_names:
    ...
```

Or query **`tabHas Role`** / `frappe.get_roles(email)` depending on context. Client-side desk may expose different helpers; do not copy those APIs into controllers blindly.

### Confusing **User Permission** with **Role** DocPerms

- **Role + DocPerm** answers: "Can this role read/write **Shop** in general?"
- **User Permission** answers: "For this user, which **Shop** (or **Company**, **Territory**, …) values are in scope?"

If the user has read on **Shop** but a User Permission row limits `for_value` to one shop, other shops disappear from list views and link queries — by design.

### `has_permission` hooks vs document hooks for "grant on link"

Two patterns:

| Approach                                                                                            | Pros                                                                               | Cons                                                                                      |
| --------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| **`hooks.py` `has_permission`** for a DocType                                                       | Central, works even when Frappe's default rule would deny                          | Harder to reason about; must not fight Role Manager expectations; easy to forget in tests |
| **Sync on document events** (e.g. assign **User Permission** + role when `Shop Tenant.user` is set) | Matches business language ("link user → access"); Desk Role Manager stays truthful | Must handle insert/update/trash/clear user; keep idempotent                               |

Pick one primary story per DocType. If you use **both**, document the order of evaluation and avoid contradictory rules.

### Permlevel and "field hidden but still readable"

**Permlevel** hides fields in the form UI for users without matching role permlevel; it is **not** a substitute for **read permission on the DocType** or row-level security. API and list views can still expose data if role permissions allow reading the document.

### Tests: stale roles and User Permissions

`before_tests` / install scripts that seed users often need to **strip** old **Has Role** and **User Permission** rows when permission model changes. Otherwise tests pass/fail based on leftover DB state. After mutating permissions in tests, prefer `frappe.db.commit()` when the runner expects persisted state, and use `frappe.set_user` to assert as the portal user.

### **Role Profile** on **User** blocks role changes (including `add_roles`)

If a **User** has a **Role Profile** whose linked **Role** has **no DocType permissions** (or the profile is otherwise empty / misconfigured), Frappe can **refuse to apply changes to the Has Role child table**—from Desk **and** from server code such as `frappe.get_doc("User", ...).add_roles(...)`. **User Permission** rows created in the same request may still appear, while the **Shop Tenant** (or similar) role never sticks, which looks like “sync is half broken.”

**Debug / fix:** Clear or replace the **Role Profile** on that **User**; give the profile’s **Role** real **Role Permissions Manager** rows if the profile must stay; or assign roles without a locking empty profile.

### `if_owner` alone for multi-tenant-ish data

**If Owner** only ties access to **document owner**, not to arbitrary business keys (tenant, company). For "user A only sees tenant T documents", you usually need **User Permission** (or custom query conditions), not only if_owner.

### `ignore_permissions=True`

Use only in trusted server paths (migration, confirmed system user). Overuse leaks data across tenants.

## Practical checklist when "Not permitted"

1. Confirm **`frappe.get_roles()`** for the session user includes the role you think they have. If hooks add **User Permission** but not roles, check **Role Profile** on **User** (empty profile / role with zero DocPerms can block **Has Role** updates).
2. Open **Role Permissions Manager** for that **Role** + **DocType** — check **If Owner**, export, import, etc.
3. List **User Permission** rows for that user (**User Permission** list filtered by user).
4. Check DocType **`has_permission`** on the class and **`hooks.py`** `has_permission` / `permission_query_conditions`.
5. For API: confirm method is `@frappe.whitelist` and role **Desk Access** / website auth as needed.

## DocType JSON and workspace rules

If project rules forbid hand-editing exported **`*.json`** for core DocTypes, add fields and **Permission Rules** via **Desk** or **`bench console`** (`get_doc("DocType", ...)`, mutate, `save()`) so timestamps and generated hints stay consistent.

## Related skills

- [`frappe-whitelist`](frappe-whitelist/SKILL.md) — `@frappe.whitelist` decorator, guest APIs, handler placement
- [`frappe-db-permissions`](frappe-db-permissions/SKILL.md) — ORM/db API default permission behavior
- [`frappe-testing`](frappe-testing/SKILL.md) — permission tests with `frappe.set_user`
