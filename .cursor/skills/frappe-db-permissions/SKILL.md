---
name: frappe-db-permissions
description: >-
  Aligns database reads/writes in Frappe apps with the permission stack (DocPerm,
  permission query conditions, User Permissions, whitelisted APIs). Includes a
  reference table of ORM/db APIs and whether they enforce permissions by default.
  Covers when to use get_list/get_doc/save vs db.set_value, and how to scope
  updates safely. Use when writing whitelisted methods, portal APIs, hooks that
  touch other users’ rows, or debugging PermissionError / silent list filtering.
---

# Frappe: database access and permissions

## Reference: database APIs vs default permission checks

Grounded in **Frappe Framework v15** (`frappe.model.db_query.DatabaseQuery.execute`, `frappe/__init__.py` `get_list` / `get_all`, `frappe.model.document`, `frappe.database.database`, `frappe.client`). Behavior is stable across recent v14/v15 lines; re-verify if you rely on edge cases after upgrades.

**What “permissions enforced” means for list-style queries (`DatabaseQuery`)**

When `ignore_permissions` is **false** (default for **`frappe.get_list`** / **`frappe.db.get_list`**):

1. **`has_permission(..., throw=True)`** for **read** or **select** on the main (and joined) DocTypes — blocks the call if the role has no read/select.
2. **`build_match_conditions()`** — appends **User Permission** / **`permission_query_conditions`** SQL so the result set is row-scoped.

When `ignore_permissions` is **true** (**`frappe.get_all`** / **`frappe.db.get_all`** always force this; you can also pass it to **`get_list`**): **both** (1) and (2) are skipped. You still need SQL-level access as the DB user; there is no second ORM safety net.

| API | Default: enforces DocPerm read/select? | Default: User Perm + PQC row filters? | Notes |
| --- | --- | --- | --- |
| **`frappe.get_list`** / **`frappe.db.get_list`** | Yes | Yes | Pass `ignore_permissions=True` to bypass (same effect as `get_all`). |
| **`frappe.get_all`** / **`frappe.db.get_all`** | **No** (forced bypass) | **No** | Implementation sets `ignore_permissions=True` unconditionally. |
| **`frappe.get_last_doc`** | **No** | **No** | Uses `get_all` then `get_doc`; easy to over-fetch across tenants if `filters` are loose. |
| **`frappe.get_value`** (alias **`frappe.db.get_value`**) | **No** | **No** | Thin read; no `has_permission`, no match conditions. |
| **`frappe.db.get_values`** / **`get`** | **No** | **No** | Same as `get_value`. |
| **`frappe.db.exists`** | **No** | **No** | Implemented via `get_value(..., ignore=True, ...)`. |
| **`frappe.db.count`** | **No** | **No** | Query builder count only. |
| **`frappe.db.sql`** / **`sql_list`** | **No** | **No** | No DocPerm or row filters; trusted-server use only. |
| **`frappe.qb` … `.run()`** (queries from **`get_query`**, etc.) | **No** | **No** | Docs note permissions are not inherent to the builder path. |
| **`frappe.db.set_value`** / **`bulk_update`** | **No** (no `check_permission` on write) | **No** | Bypasses document workflow; does not validate DocPerm write by itself. |
| **`frappe.db.set_single_value`** / **`get_single_value`** | **No** | **No** | Singles table / cache; Desk REST wraps reads with checks (see below). |
| **`frappe.db.delete`** | **No** | **No** | Raw DELETE for matching filters. |
| **`frappe.db.bulk_insert`** | **No** | **No** | Low-level insert. |
| **`frappe.new_doc`** | N/A (in-memory) | N/A | No DB hit until **`insert`**. |
| **`frappe.get_doc`** (load existing) | **No** on load | **No** | `load_from_db` uses **`db.get_value`** only. **Read** is **not** checked at load time in the ORM. |
| **`frappe.get_cached_doc`** / **`get_cached_value`** | Same as **`get_doc`** / field read | Same | Cache keyed by doctype+name; same load path. |
| **`frappe.get_single`** / **`get_single_value`** (module-level) | **No** on load | **No** | Singles via **`get_doc(doctype, doctype)`**. |
| **`doc.insert`** | **Yes** (`check_permission("create")`) | N/A | Unless `ignore_permissions=True` / `doc.flags.ignore_permissions`. |
| **`doc.save`** / **`_save`** | N/A | N/A | **`check_permission("write")`** unless ignored. |
| **`doc.submit` / `cancel`** | **Yes** | N/A | Respective perm types unless ignored. |
| **`doc.delete`** | **Yes** (delete) | N/A | Delegates to **`frappe.delete_doc`** with `ignore_permissions` flag. |
| **`frappe.delete_doc`** | **Yes** (delete) | N/A | Default `ignore_permissions=False`; uses `doc.has_permission("delete")` (unless Administrator / ignored). |
| **`frappe.set_value`** (module) | **Yes** (via **`get_doc` → `save`**) | N/A | Same stack as normal save. |
| **`frappe.rename_doc`** | **Yes** (write + rules) | N/A | Supports `ignore_permissions` internally for trusted paths. |

**REST / Desk client (`frappe.client`)** — these add checks **on top of** the underlying DB call:

| API | Extra permission behavior |
| --- | --- |
| **`frappe.client.get`** | **`doc.check_permission()`** (read) + **`apply_fieldlevel_read_permissions`** after **`get_doc`**. |
| **`frappe.client.get_list`** | **`frappe.get_list`** (full list stack). |
| **`frappe.client.get_value`** | **`frappe.has_permission(doctype, …)`** then **`get_list`** for non-Single (so row filters apply); Singles use **`db.get_values_from_single`**. |
| **`frappe.client.get_single_value`** | **`frappe.has_permission(doctype)`** then **`db.get_single_value`**. |
| **`frappe.client.set_value`** | **`get_doc` → `update` → `doc.save()`** (write path). |

**Practical rule:** anything **`frappe.db.*`** or raw SQL / query builder is **“DB only”** — assume **no** Frappe permission story unless **you** or **`frappe.client`** / **`get_list`** add it.

## Permission stack (short)

1. **Role permissions (**DocPerm**)** — per DocType: read / write / create / delete / submit, **permlevel**, **if_owner** (where used).
2. **`permission_query_conditions` hooks** — append SQL/WHERE so **list** queries only return allowed rows (e.g. **Notification Log**: `for_user = session.user`).
3. **User Permission** — narrows rows by **Link** field values (often combined with DocPerm read).
4. **`has_permission` hooks / controller** — extra checks for **get_doc** / **save** / **delete** on a document instance.

List views and **`frappe.get_list`** (default) apply **(1)+(2)+(3)**. **`frappe.get_all`** always skips **(1)+(2)+(3)**. **Single-doc** writes (**`save`**, **`insert`**, **`delete`**) use **`check_permission`** / **`has_permission`**; loading **`get_doc`** from the DB does **not** run read checks unless you (or **`frappe.client.get`**) add them.

## Reads: respect the ORM layer

| Need                                                       | Prefer                                                                                                                                        |
| ---------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| User-facing or whitelisted code, “what may this user see?” | **`frappe.get_list`** (default `ignore_permissions=False`) so **read/select** and **match conditions** apply. Do **not** use **`frappe.get_all`** for user-scoped data — it **always** bypasses those checks. |
| Internal job / migration / confirmed admin path            | **`frappe.get_all`** / **`get_list(..., ignore_permissions=True)`** only with a **narrow, documented filter**, or **`frappe.db.sql`** with the same care. You cannot turn permission checks *on* for **`get_all`**. |

**Avoid** **`frappe.db.get_value` / `sql`** for end-user–scoped data unless you **replicate** the same constraints (easy to get wrong). If you use **`db.get_value`**, pair it with an explicit **`for_user` / owner** check that matches your product rules.

## Writes: `save` vs `db.set_value`

| Path                                               | Permission behaviour                                                                       | When to use                                                                                                                                                                        |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`frappe.get_doc` → mutate → `doc.save()`**       | **`check_permission("write")`** on save. Needs **Write** on DocType (and permlevel rules). | Normal business documents; preferred default.                                                                                                                                      |
| **`frappe.set_value` / `frappe.client.set_value`** | Same as **save** (uses **`get_doc` + `update` + `save`**).                                 | Same as save; not a permission bypass.                                                                                                                                             |
| **`frappe.db.set_value`**                          | **Does not** run document permission checks by itself.                                     | Only after you have **already** restricted to the correct row(s)—e.g. name came from **`get_list`** with the same user, or **`db.exists({"name": x, "for_user": session.user})`**. |

**Core precedent:** some framework DocTypes (e.g. **Notification Log** **`mark_as_read`**) use **`frappe.db.set_value`** because **`save()`** is a poor fit (**`in_create`**, log-style rows, tiny flag updates). When you mirror that pattern in an app, **document in a comment** why **`save`** is not used, and **tighten scope** with **`get_list` / `exists`** so you never update another user’s row.

## Whitelisted methods (portal / guest / website user)

1. **Never trust** client **`name`** / **`docname`** alone. Resolve the row with a filter that includes **`frappe.session.user`** (or equivalent tenant key) **before** any write.
2. Prefer **`frappe.get_list(..., pluck="name", filters={...})`** then **`db.set_value`** per id, or **`get_doc`** + **`save`** if Write exists and the DocType supports it.
3. **`Guest`**: return empty lists or **`frappe.throw(..., PermissionError)`** early; do not hit the DB with relaxed filters.
4. **UI**: wire **`frappe.call`** **`error`** handlers so **PermissionError** / validation failures are visible (not silent).

## Custom fields on core DocTypes

- **`read_only: 1`** on a **Custom Field** can block or complicate updates via **`save`** / **`set_value`** depending on context. If the field is only updated from server code, prefer **`read_only: 0`** and hide from Desk with UX if needed—or use **`db.set_value`** after explicit scoping (see above).
- Adding fields: use **`create_custom_fields`** / **`bench console`**, not hand-edited core DocType JSON (project rules).

## Tests

- **`frappe.set_user("normal@example.com")`** then call the API or **`get_list`** / **`save`** and assert allowed vs denied counts or **`PermissionError`**.
- Patch **`frappe.enqueue`** / **`publish_realtime`** when testing side effects, not permission boundaries.

## Quick checklist

- [ ] List path uses **`get_list`** with default permissions (not **`get_all`**) for user-scoped reads, unless **`ignore_permissions`** is deliberate and documented.
- [ ] Writes either go through **`save`** with correct **DocPerm**, or **`db.set_value`** only after **explicit row scope** (same user as **`session.user`**).
- [ ] Whitelisted handler validates **ownership / tenant** before update.
- [ ] No broad **`UPDATE … WHERE for_user = %s`** without the same invariants documented in code.
