---
name: frappe-db-permissions
description: >-
  Aligns database reads/writes in Frappe apps with the permission stack (DocPerm,
  permission query conditions, User Permissions, whitelisted APIs). Covers when to
  use get_list/get_doc/save vs db.set_value, and how to scope updates safely. Use
  when writing whitelisted methods, portal APIs, hooks that touch other users’
  rows, or debugging PermissionError / silent list filtering.
---

# Frappe: database access and permissions

## Permission stack (short)

1. **Role permissions (**DocPerm**)** — per DocType: read / write / create / delete / submit, **permlevel**, **if_owner** (where used).
2. **`permission_query_conditions` hooks** — append SQL/WHERE so **list** queries only return allowed rows (e.g. **Notification Log**: `for_user = session.user`).
3. **User Permission** — narrows rows by **Link** field values (often combined with DocPerm read).
4. **`has_permission` hooks / controller** — extra checks for **get_doc** / **save** / **delete** on a document instance.

List views and **`frappe.get_list`** / **`frappe.get_all`** (without **`ignore_permissions=True`**) apply **(1)+(2)+(3)**. **Single-doc** paths (**`get_doc`**, **`save`**) use **`has_permission`** and role rules; do not assume they mirror list filters unless you verify.

## Reads: respect the ORM layer

| Need                                                       | Prefer                                                                                                                                        |
| ---------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| User-facing or whitelisted code, “what may this user see?” | **`frappe.get_list`** or **`frappe.get_all`** without **`ignore_permissions=True`** so **PQC** and role rules apply.                          |
| Internal job / migration / confirmed admin path            | **`frappe.get_all(..., ignore_permissions=True)`** only with a **narrow, documented filter** (or use **`frappe.db.sql`** with the same care). |

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

- [ ] List path uses **`get_list`/`get_all`** without **`ignore_permissions`** unless justified.
- [ ] Writes either go through **`save`** with correct **DocPerm**, or **`db.set_value`** only after **explicit row scope** (same user as **`session.user`**).
- [ ] Whitelisted handler validates **ownership / tenant** before update.
- [ ] No broad **`UPDATE … WHERE for_user = %s`** without the same invariants documented in code.
