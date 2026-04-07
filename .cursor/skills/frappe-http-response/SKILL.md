---
name: frappe-http-response
description: >-
  Shapes HTTP responses in Frappe via frappe.local.response / frappe.response:
  JSON body, http_status_code, type (download, redirect, pdf, …), headers, and
  returning werkzeug.Response. Covers /api/v1 vs v2 vs legacy cmd, when status
  codes are applied automatically vs set explicitly. Prefer /api/v2 when the site
  runs Frappe v15+. Use when building whitelisted APIs, custom JSON envelopes, file downloads, redirects, REST
  status codes, or debugging API response bodies.
---

# Frappe HTTP response object

## Scope

Use when shaping HTTP responses via `frappe.local.response` / `frappe.response`:
JSON envelopes, `http_status_code`, `type` (download, redirect, pdf), headers, or Werkzeug
`Response` returns. Covers `/api/v1` vs v2 vs legacy `cmd` behavior.

## API version preference (v1 vs v2)

- **v2 availability:** **Frappe v15+** only — shipped as **beta** in v15.0.0 (Oct 2023, [PR #22300](https://github.com/frappe/frappe/pull/22300)). v14 sites have v1 only.
- **Prefer v2** for new REST/RPC clients when the target site runs v15+: prefix **`/api/v2/`** (`/api/v2/method/…`, `/api/v2/document/…`, `/api/v2/doctype/…`). Upstream targets stable v2 in **v16** ([#22762](https://github.com/frappe/frappe/issues/22762)).
- **Response envelope:** v2 RPC and REST assign return values to **`data`**; v1 / legacy **`cmd`** use **`message`** (table below). Plan client parsers accordingly.
- **Keep v1** for v14 compatibility, legacy `/api/resource/…` clients, or Desk **`frappe.call`** without `api_version: "v2"`.

## Mental model

- **`frappe.local.response`** is a request-scoped `_dict` initialized with `{"docs": []}` when the site request starts (`frappe/__init__.py`).
- **`frappe.response`** is a **LocalProxy** to the same object. Prefer one style consistently in a file; both are equivalent.

## How the body is built

1. Your code (whitelisted method, API route, hook, etc.) mutates `frappe.local.response` and/or returns a value from some entry points.
2. **`frappe.utils.response.build_response()`** picks a builder from `frappe.response.get("type")` (default **`json`**): `csv`, `txt`, `download`, `json`, `pdf`, `page`, `redirect`, `binary` (`frappe/utils/response.py`).
3. **`frappe.app.process_response`** merges **`frappe.local.response_headers`** onto the final Werkzeug `Response` (CORS, cookies, rate limit, etc.).

## Where return values go (API surface)

| Entry | Return value handling |
|-------|------------------------|
| Legacy **`cmd`** RPC (`frappe.handler.handle`) | If the method returns a non-`None` value that is not a Werkzeug `Response`, it is stored as **`frappe.response["message"]`**. |
| **`/api/v1/...`** RPC (`handle_rpc_call` → `handler.handle`) | Same as above: payload typically ends up under **`message`** (handler side effect). |
| **`/api/...`** unified handler (`frappe.api.handle`) | If the matched endpoint **returns** a non-`None` value and it is not a `Response`, it is assigned to **`frappe.response["data"]`**. |
| **`/api/v2/method/...`** (`handle_rpc_call` returns `frappe.call(...)`) | Return value is assigned to **`data`** by `frappe.api.handle`. |

So: **v1-style RPC** leans on **`message`**; **v2 method calls** leans on **`data`**. If you need a flat or custom JSON document, populate **`frappe.local.response`** directly and avoid relying on the automatic wrapper key.

## JSON status code and body

In **`as_json()`** (`frappe/utils/response.py`):

- If **`http_status_code`** is truthy, it becomes the **Werkzeug response status** and is **removed** from the dict before serialization (it must not appear in the JSON body).
- If **`http_status_code`** is missing or falsy (`None`, `0`), the default Werkzeug status applies (**200** unless something else set the `Response`).

`docs` is dropped from the serialized payload when it is an empty list.

## Non-JSON responses

Set **`frappe.local.response["type"]`** (or attribute) and the fields each builder expects, for example:

- **`download`** / **`binary`**: `filename`, `filecontent`; optional `content_type`, `display_content_as` (`attachment` vs `inline`) for downloads (`as_raw`).
- **`pdf`**: `filename`, `filecontent`.
- **`redirect`**: `location` (Werkzeug `redirect`).
- **`page`**: `route` and optional `http_status_code` passed into website rendering (`as_page`).

Download handlers do **not** reuse the `as_json` `http_status_code` logic; rely on thrown **`HTTPException`** subclasses or return a raw **`Response`** if you need precise status on those paths.

## Bypassing Frappe’s JSON envelope entirely

From **`frappe.handler.handle`**:

- If a whitelisted function returns a **`werkzeug.wrappers.Response`**, that object is returned **as-is** up the stack (no automatic `message` assignment).

Use this for fully custom status, headers, and body outside `build_response("json")`.

## When HTTP status is set **automatically**

- **Uncaught exceptions**: `frappe.app.handle_exception` uses **`getattr(exc, "http_status_code", 500)`**. Frappe’s built-in exceptions in `frappe/exceptions.py` define `http_status_code` (401, 403, 404, 417, 429, …). JSON clients get **`frappe.utils.response.report_error`**, which builds JSON then sets **`response.status_code`** on the Werkzeug object.
- **`werkzeug.exceptions.HTTPException`**: handled via **`e.get_response(...)`** — status comes from the exception.
- **Successful JSON** with no `http_status_code` set: typically **200**.

## When to set **`http_status_code` explicitly**

- **Success codes other than 200** (e.g. **201 Created**, **202 Accepted**): framework helpers sometimes set **`frappe.response.http_status_code = 202`** after an action (see resource delete patterns in `frappe/api/v1.py`); mirror that pattern for similar APIs.
- **Validation or business-rule failures** where you **do not** want to raise (return a JSON error payload with 4xx).
- **Custom JSON shapes** while still using `build_response("json")` — set keys on `frappe.local.response`, set **`http_status_code`**, and **`pop("message", None)`** / **`pop("data", None)`** if a prior layer added a wrapper you do not want in the body.

Prefer **`frappe.throw(...)`** with the right exception class when the situation matches an existing **`http_status_code`** — less duplication and consistent error JSON.

## Headers and cookies

- **`frappe.local.response_headers`**: merged onto the outgoing response in **`process_response`** — use for per-request headers without building a raw `Response`.
- Cookie flushes use the cookie manager; do not fight cache semantics without checking **`process_response`** behavior.

## Further reading

- Official: [REST API](https://docs.frappe.io/framework/user/en/guides/integration/rest_api) (v2 routes, v15+), [Responses](https://docs.frappe.io/framework/user/en/python-api/response) (maps `build_response`, download example, `display_content_as`).
- Source of truth: [`frappe/utils/response.py`](https://github.com/frappe/frappe/blob/develop/frappe/utils/response.py), [`frappe/handler.py`](https://github.com/frappe/frappe/blob/develop/frappe/handler.py) (`message` + `Response` bypass), [`frappe/api/__init__.py`](https://github.com/frappe/frappe/blob/develop/frappe/api/__init__.py) (`data` assignment).
- Community article (same themes as official docs): [Frappe Forum — `frappe.local.response` vs `frappe.response`](https://discuss.frappe.io/t/how-to-control-your-api-response-body-in-frappe-frappe-local-response-vs-frappe-response/152487).
- LinkedIn (Mohammed Amir, 2025): [How to Control Your API Response Body in Frappe](https://www.linkedin.com/pulse/how-control-your-api-response-body-frappe-vs-mohammed-amir-rcxhf/) — Werkzeug/thread-local overview, `http_status_code`, `type`, popping `message` for custom envelopes.

## Quick patterns

```python
# Custom JSON body (no automatic "message" / stray keys)
frappe.local.response["http_status_code"] = 200
frappe.local.response["items"] = items
frappe.local.response.pop("message", None)
frappe.local.response.pop("data", None)
```

```python
# File download
frappe.local.response.type = "download"
frappe.local.response.filename = "export.csv"
frappe.local.response.filecontent = content
frappe.local.response.display_content_as = "attachment"
```

```python
# Full control
from werkzeug.wrappers import Response

@frappe.whitelist()
def raw():
	return Response("ok", status=204, mimetype="text/plain")
```

## Related skills

- [`frappe-whitelist`](frappe-whitelist/SKILL.md) — exposing handlers via `@frappe.whitelist`
- [`frappe-testing`](frappe-testing/SKILL.md) — assert API responses in tests
