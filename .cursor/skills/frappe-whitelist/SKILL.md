---
name: frappe-whitelist
description: >-
  Guides @frappe.whitelist on Python callables: decorator options (allow_guest,
  methods, xss_safe, force_types), API entry points (/api/method, v2 RPC,
  run_doc_method), placement in apps, and security checks inside handlers. Use
  when exposing Desk/portal/webhook endpoints, debugging "Function … is not
  whitelisted", choosing guest vs authenticated APIs, choosing v1 vs v2 API paths,
  or reviewing whitelisted method security.
---

# Whitelisting Frappe methods

## Scope

Use when adding or reviewing **`@frappe.whitelist`** on Python callables — Desk
`frappe.call`, REST RPC, DocType controller methods, portal/webhook endpoints.
For **permission checks inside** handlers and which ORM APIs enforce them, see
**frappe-permissions** and **frappe-db-permissions**. For response shaping
(downloads, status codes, v1 `message` vs v2 `data`), see **frappe-http-response**.

Do **not** use whitelisting for internal-only helpers; keep those as plain
functions and call them from whitelisted entry points or hooks.

## Mental model

1. **`@frappe.whitelist(...)`** registers the function in process-global sets at
   import time (`whitelisted`, `guest_methods`, `allowed_http_methods_for_whitelisted_func`).
2. On each RPC request, Frappe resolves the dotted path → **`is_whitelisted`**
   (login / guest gate) → **`is_valid_http_method`** (verb gate) →
   **`frappe.call(method, **frappe.form_dict)`** (args filtered by signature).
3. **Whitelist ≠ authorized.** It only means the HTTP/RPC layer may invoke the
   callable. **DocPerm, User Permission, and your explicit checks** still apply
   inside the function unless you bypass them deliberately.

```
Client → /api/method/app.module.fn  (or legacy cmd=…)
       → override_whitelisted_method (optional hook redirect)
       → is_whitelisted + is_valid_http_method
       → frappe.call → your function
```

## Decorator options

| Option | Default | Purpose |
| --- | --- | --- |
| *(none)* | — | Callable reachable by **logged-in** users only. |
| `allow_guest=True` | `False` | **Guest** (`session.user == "Guest"`) may call. Still add your own auth/scope checks. |
| `methods=[...]` | `GET, POST, PUT, DELETE` | Restrict HTTP verbs. **Prefer narrowing** — e.g. `methods=["POST"]` for mutations and guest login/logout-style endpoints. |
| `xss_safe=True` | `False` | With `allow_guest`, skip HTML sanitization of string `form_dict` values (only for endpoints that must accept rich HTML). |
| `force_types=True/False` | hook-driven | When enforced, every parameter needs a type annotation or Frappe raises **`FrappeTypeError`**. |

**Type validation (v15+):** Frappe wraps whitelisted functions with
`validate_argument_types`. If the app sets
`require_type_annotated_api_methods = True` in `hooks.py` (Frappe core and new
app boilerplate do), annotations are **required** on all parameters. Always
annotate whitelisted signatures — see **python-postponed-annotations** for
`from __future__ import annotations`.

## Where to put methods

| Location | Typical use |
| --- | --- |
| **DocType controller** (`doctype/foo/foo.py`) | Instance actions invoked via `frm.call` / `run_doc_method`; colocate with document logic. |
| **Feature module** (`app/feature/api.py`, `custom/sales_invoice.py`) | Cross-cutting or client-script endpoints not tied to one DocType method name. |
| **Override via hooks** | `override_whitelisted_methods = {"original.dotted.path": "app.replacement.path"}` — last hook wins; replacement must also be `@frappe.whitelist`. |

**Avoid** central “whitelist registry” files that apply `@frappe.whitelist` at
runtime in `before_request` — hard to trace, easy to miss on code review, and
 fights static import order. Prefer the decorator on the function definition.

## API entry points (same decorator)

| Surface | Example | Notes |
| --- | --- | --- |
| Legacy **`cmd`** | `POST /api/method/...` or `cmd=` form | Return value → `frappe.response["message"]`. v1 path. |
| **API v1 RPC** | `POST /api/v1/method/...` (alias: `/api/method/...`) | Same as legacy **`cmd`**: return → **`message`**. |
| **API v2 RPC** | `POST /api/v2/method/...` | Return value → `frappe.response["data"]`. |
| **`run_doc_method`** | `frappe.call({ method: "submit", args: { dt, dn } })` | Loads doc with **`check_permission=True`**, then whitelists the **controller method**. |
| **API v2 doc method** | `POST /api/v2/document/{doctype}/{name}/method/{method}` | Same whitelist check on controller method + HTTP-method→perm map. |

### Prefer v2 when available

- **Added in Frappe v15** (v15.0.0, Oct 2023) as **beta** ([PR #22300](https://github.com/frappe/frappe/pull/22300)). **Not available on v14** sites.
- For **new external integrations** on v15+ sites, prefer **`/api/v2/...`** over v1 (`/api/method/...`, `/api/resource/...`, legacy `cmd=`):
  - RESTful document routes (`/api/v2/document/{doctype}/{name}/…`)
  - Shorter RPC paths for controller methods (`/api/v2/method/{DocType}/{method}`)
  - Consistent **`data`** response envelope (see **frappe-http-response**)
- **Same `@frappe.whitelist` handler** — only the URL prefix and response wrapper differ; no duplicate Python entry points needed.
- **Keep v1** when the site is v14, an existing client expects **`message`**, or you rely on Desk **`frappe.call`** defaults (v1 unless `api_version: "v2"` is set).
- v2 is still **beta** through v15; upstream targets a stable v2 release in **v16** ([#22762](https://github.com/frappe/frappe/issues/22762)).

**Server Script** rows can shadow `_api` method names — prefer explicit Python
methods in apps unless the site intentionally uses Script Manager.

## Security checklist (apply inside every handler)

1. **Authenticate intent, not only `@frappe.whitelist`.**
   - Default decorator: user must be logged in.
   - **`allow_guest`**: treat as **public internet** — verify webhook secrets,
     signed payloads, or rate limits; never rely on obscurity of the URL.

2. **Check permissions at the trust boundary** (start of handler or before side
   effects):
   - **`doc.check_permission("read"|"write"|…)`** when you loaded or will return a document.
   - **`frappe.has_permission(..., throw=True)`** when you only have doctype + name.
   - **`frappe.only_for("System Manager")`** (or specific roles) for admin-only utilities — still not a substitute for DocPerm on document ops.

3. **Validate parameter shapes.**
   - Use **type annotations** so Frappe coerces/validates (`str`, `int`, `dict`, …).
   - For filter-like args, never pass client JSON straight into ORM filters without
     an allowlist of fields/operators (see [ERPNext Code Security Guidelines](https://github.com/frappe/erpnext/wiki/Code-Security-Guidelines)).

4. **Scope reads and writes to the current user/tenant.**
   - Prefer **`frappe.get_list`** (not **`frappe.get_all`**) for user-facing reads.
   - Never trust client-supplied **`name`** alone — filter by **`owner`**, link
     fields, or User Permission–compatible constraints before **`get_doc`** / writes.
   - **`ignore_permissions=True`** only on narrow, already-scoped paths; document why.

5. **Restrict HTTP methods** for state-changing or guest endpoints:
   `@frappe.whitelist(allow_guest=True, methods=["POST"])`.

6. **Do not expose arbitrary document factories** — if accepting a dict to
   **`frappe.get_doc(values).insert`**, restrict **`doctype`** to an explicit tuple
   and use **`frappe.only_for`** where appropriate (security guidelines precedent).

7. **Guest string input:** default sanitization runs unless `xss_safe=True`; prefer
   normal sanitization and structured JSON fields over `xss_safe` unless required.

8. **Elevation anti-patterns:** avoid **`frappe.set_user("Administrator")`** in
   guest/webhook handlers except for tightly scoped, audited system tasks; prefer
   role-specific users or explicit permission checks on each row.

## DocType controller methods

Whitelisted **instance** methods on Document subclasses:

```python
class Task(Document):
	@frappe.whitelist()
	def add_comment(self, text: str):
		self.check_permission("write")
		# ...
```

Invoked from Desk via **`run_doc_method`** / form **`frm.call`**. The framework
loads the document with permission checks before **`doc.run_method`**. Your
method should still **`check_permission`** for the specific operation when the
HTTP verb→perm mapping is not enough.

## Patterns

```python
@frappe.whitelist()
def download_attachment(name: str):
	"""Logged-in users only; type-validated name."""
	file_doc = frappe.get_doc("File", name)
	file_doc.check_permission("read")
	frappe.local.response.type = "download"
	frappe.local.response.filename = file_doc.file_name
	frappe.local.response.filecontent = file_doc.get_content()
```

```python
@frappe.whitelist(allow_guest=True, methods=["POST"])
def vendor_webhook(payload: dict, token: str):
	expected = frappe.get_single_value("My Settings", "webhook_secret")
	if token != expected:
		frappe.throw(_("Invalid token"), frappe.AuthenticationError)
	# process payload — still validate shape and side effects
```

```python
@frappe.whitelist()
def reindex_search(doctype: str):
	frappe.only_for("System Manager")
	allowed = ("ToDo", "Note")
	if doctype not in allowed:
		frappe.throw(_("Not allowed"))
	# ...
```

```python
# hooks.py — override core endpoint (replacement must be whitelisted)
override_whitelisted_methods = {
	"frappe.core.doctype.user.user.reset_password": "my_app.overrides.custom_reset_password",
}
```

## Pitfalls

| Symptom | Likely cause |
| --- | --- |
| `Function … is not whitelisted` | Missing decorator, typo in dotted path, or module not imported on boot. |
| Works in Desk, 403 for Guest | Missing `allow_guest=True`. |
| 403 despite `allow_guest` | **`PermissionError`** inside handler — whitelist passed, business check failed (expected). |
| GET mutation or CSRF surprises | Default allows GET; use **`methods=["POST"]`** for writes. |
| `FrappeTypeError` on call | Missing annotation with `require_type_annotated_api_methods`; add types or set `force_types=False` only with reason. |
| Override ignored | Target not whitelisted, wrong hook key, or another app's hook listed later. |

**Testing:** call the dotted path with **`frappe.set_user`** / Guest session;
see **frappe-testing** (UnitTestCase for handler logic, IntegrationTestCase for
DB + permissions).

## Related skills

- [`frappe-permissions`](frappe-permissions/SKILL.md) — `check_permission` vs `has_permission`, layers
- [`frappe-db-permissions`](frappe-db-permissions/SKILL.md) — `get_list` vs `get_all`, `save` vs `db.set_value`
- [`frappe-http-response`](frappe-http-response/SKILL.md) — downloads, status codes, v1/v2 response keys
- [`frappe-testing`](frappe-testing/SKILL.md) — API and permission tests
- [`python-postponed-annotations`](python-postponed-annotations/SKILL.md) — annotation style for whitelisted signatures

## Additional resources

- Frappe source: [`frappe/__init__.py` `whitelist` / `is_whitelisted`](https://github.com/frappe/frappe/blob/develop/frappe/__init__.py), [`frappe/handler.py`](https://github.com/frappe/frappe/blob/develop/frappe/handler.py), [`frappe/utils/typing_validations.py`](https://github.com/frappe/frappe/blob/develop/frappe/utils/typing_validations.py)
- [ERPNext Code Security Guidelines](https://github.com/frappe/erpnext/wiki/Code-Security-Guidelines) — parameter types, arbitrary document creation, permission defaults
