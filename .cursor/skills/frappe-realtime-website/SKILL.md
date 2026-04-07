---
name: frappe-realtime-website
description: >-
  Publishes per-user realtime events with frappe.publish_realtime, subscribes on
  the website via web_include_js (init order, event names), and extends
  frappe.boot with extend_bootinfo / on_login for one-shot catch-up. Use when
  wiring socket.io alerts for portal users, website JS bundles, or boot payload
  injection after login. Pair with Desk **Notification** when the user must
  receive the information even if they were offline or not logged in at the
  time of the event.
---

# Frappe realtime and website client

## Scope

Use for portal/socket.io alerts via `frappe.publish_realtime`, `web_include_js`, and
`extend_bootinfo` / `on_login`. When the user must get email or audit trail even if offline,
use **Notification** instead.

## Realtime vs Desk **Notification** (persistent, login-independent)

| | **`frappe.publish_realtime`** | Desk **Notification** (email / other channels) |
|---|-------------------------------|-----------------------------------------------|
| **Delivery** | Active socket for that user (or room); website code often skips **Guest** | Runs from document lifecycle hooks; creates **Communication** for email path |
| **If the user was offline** | Event is lost unless you add boot catch-up or another store-and-forward layer | Email / **Communication** still exists; user sees it when they open mail or Desk |
| **Login at event time** | User must be connected (and typically authenticated) to see it live | Recipients are resolved from the document / conditions; delivery does not depend on an open browser tab |

Use **realtime** for immediate in-session UX (toasts, live counters, “your ticket was updated” while they have the portal open).

Use **Notification** (see skill **frappe-notifications**) when the information should **persist and reach the user independent of whether they were logged in or had a socket connected** at the moment of the change—for example gate changes, payment confirmations, or anything that must be **emailed**, **auditable** via **Communication**, or read days later without relying on boot flags.

Combining both is valid: **Notification** for the durable channel, **`publish_realtime`** for instant feedback when they are online.

## Server: `frappe.publish_realtime`

Target a **specific user** (typical for portal alerts):

```python
frappe.publish_realtime(
	event="my_app_ticket_update",  # string channel name; match client
	message={
		"ticket": doc.name,
		"view_ticket_url": get_url("/portal/ticket/" + doc.name),
		# keep payload JSON-serializable
	},
	user=frappe.db.get_value("Customer Profile", {"user": ...}, "user"),
)
```

- **`event`**: one identifier shared by publisher and subscriber.
- **`message`**: dict (or serializable structure) delivered to the client listener.
- **`user=`**: restricts delivery to that user’s socket room (omit for broadcast patterns).

Avoid putting **Desk-only** URLs (`/app/Form/...`) in messages for **Website Users**; use **Web Form routes**, **www** pages, or API-backed portal URLs.

## Website JS: `hooks.py`

```python
web_include_js = ["/assets/my_app/js/alerts.js"]
```

Ship the file under **`my_app/public/js/`** and run **`bench build`** so it appears under **`sites/assets`**.

## Client: subscribe **after** `init`

`frappe.realtime.on` only attaches if the socket exists. Call **`init`** first (website bundle provides `frappe.realtime`):

```javascript
frappe.ready(function () {
  if (!frappe.session || frappe.session.user === "Guest") return;
  if (!frappe.realtime || frappe.boot.disable_async) return;

  frappe.realtime.init(frappe.boot.socketio_port || 9000, false);
  frappe.realtime.on("my_app_ticket_update", function (data) {
    frappe.msgprint({ title: __("Update"), message: "...", indicator: "blue" });
  });
});
```

Respect **`frappe.boot.disable_async`** (or your site’s equivalent) so you do not assume sockets in CI/offline modes.

## Boot catch-up: `extend_bootinfo` + `on_login`

Use when users were **offline** but you still want the **first page load** after login to show pending items (e.g. draft tickets whose `updated_on` or a custom datetime field changed).

1. **`on_login`** (hooks): set a **short-lived cache flag** for that user (e.g. `frappe.cache().set_value(..., expires_in_sec=600)`), only for roles/user-types that should receive catch-up.
2. **`extend_bootinfo`** (hooks): if the flag is set, query pending rows, set **`bootinfo["my_pending_alerts"]` = [...]**, **`frappe.cache().delete_value(...)`** the flag, then persist a **“processed through”** timestamp (e.g. on a profile DocType) so the same alert is not replayed on every navigation.

`extend_bootinfo` receives a **`bootinfo`** dict; mutate it in place. Hooks are usually registered as **lists** in `hooks.py` so they merge with other apps:

```python
extend_bootinfo = ["my_app.boot.extend_bootinfo"]
on_login = ["my_app.boot.on_login"]
```

## Tests

- **`publish_realtime`**: `patch("frappe.publish_realtime", side_effect=capture)` and assert `event`, `user`, and `message` keys.
- **Boot hooks**: `frappe.set_user(...)`, seed data, set cache flag, call `extend_bootinfo({})`, assert keys on the dict.

## Related skills

- [`frappe-notifications`](frappe-notifications/SKILL.md) — persistent Desk **Notification** / email channel
