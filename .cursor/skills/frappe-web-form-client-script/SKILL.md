---
name: frappe-web-form-client-script
description: >-
  Authors Frappe Web Form client scripts: init timing, frappe.init_client_script
  vs after_load, field handlers, success-page hooks, and Desk Client Script field
  vs colocated .js. Use when wiring web_form/**/*.js, post-submit UX, or
  debugging scripts that never run on the public form.
---

# Frappe Web Form client script

## Scope

Use when adding or fixing **JavaScript on public Web Forms** (`web_form/**/*.js`, Desk
**Client Script** on **Web Form**, success-page behaviour, field sync). For routes,
`get_context`, and `reference_doc` prefill, use [`frappe-web-forms`](../frappe-web-forms/SKILL.md).

## Mental model — load order

On `/{route}/new`, Frappe renders `web_form.html` roughly as:

1. Inline boot (`frappe.web_form_doc`, `frappe.reference_doc`)
2. `web_form.bundle.js` — registers `frappe.ready(…)` which later runs `new WebForm(…)` → `make()`
3. Inline script block:
   - If **Web Form.client_script** (Desk field) is set → assigns `frappe.init_client_script`
   - If **standard** form has colocated `{scrub(name)}.js` → appends that file as raw inline `context.script` (Jinja-rendered)

Inside `WebForm.make()` (after fields exist, before listeners):

```javascript
frappe.init_client_script && frappe.init_client_script();
frappe.web_form.events.trigger("after_load");
this.after_load && this.after_load();
```

**Critical:** `WebForm`’s constructor does `frappe.web_form = this`. Anything assigned to
`frappe.web_form` *before* `new WebForm()` (e.g. `frappe.web_form.after_load = …` at file
parse time) is **lost** when the instance is created. Scripts that “never run” are often
using the wrong hook or the wrong timing.

## Preferred entry point

**Assign `frappe.init_client_script`** (in colocated `.js` or Desk **Client Script**).
It runs inside `make()` when `frappe.web_form` is the live instance and `fields_dict` exists.

```javascript
frappe.init_client_script = () => {
	const web_form = frappe.web_form;

	web_form.on("some_field", () => {
		// field change
	});

	sync_on_load(web_form);
};
```

### Hooks that work from `init_client_script`

| API | Use for |
|-----|---------|
| `frappe.web_form.on(fieldname, handler)` | Field change handlers (sets `df.change`) |
| `web_form.fields_dict[name].set_value(…)` | Programmatic values |
| `web_form.refresh_dependency()` | Re-evaluate depends-on / read-only |
| Patch instance methods (e.g. `render_success_page`) | Post-submit UI — bind original first |
| `frappe.web_form.events.on("after_load", …)` | Same timing as stock `after_load` event |

### Avoid at file top level

- `frappe.web_form.after_load = …` before `new WebForm()` — **wiped** by constructor
- Assuming `frappe.web_form` at parse time is the form instance — it is not yet

## Success page / submit response

`WebForm` calls `render_success_page(data)` after a successful `accept`. Patch it from
`init_client_script`:

```javascript
function patch_success_page(web_form) {
	const render_success_page = web_form.render_success_page.bind(web_form);

	web_form.render_success_page = (data) => {
		render_success_page(data);
		$(".success-footer .new-btn").hide(); // "Submit another response"

		const name = data?.name || web_form.doc?.name;
		if (name) {
			append_reference_to_success_message(name);
		}
	};
}
```

### Hiding “Submit another response” (Desk)

There is **no** dedicated Desk checkbox. Stock template shows the `.new-btn` link when
`not login_required or allow_multiple` and no `success_url` is set.

| Workaround | Effect |
|------------|--------|
| Set **Success URL** | Footer becomes redirect message; button gone — but user is redirected |
| **Login required** + **Allow multiple** off | Hides button — but breaks anonymous intake |
| Client script | Hide `.success-footer .new-btn` in `render_success_page` — preferred for one-shot public forms |

Mirror user-facing copy in Python when you need server-side tests, e.g.
`get_enquiry_reference_message(name)` next to the Web Form module.

## Desk Client Script field vs colocated `.js`

For **standard** Web Forms, Frappe supports **both**. Consider which to use; neither is mandatory.

| | Desk **Client Script** (Web Form) | Colocated `web_form/…/{name}.js` |
|---|-----------------------------------|----------------------------------|
| **Version control** | Only if exported/synced with the form | Always in the app repo |
| **Lint / review** | No JS toolchain by default | Pre-commit, CI, PR review |
| **Deploy** | DB change or export + migrate | App release / bench pull |
| **Who edits** | Desk admin, functional owner | Developers |
| **Jinja in script** | No | Yes — file is `frappe.render_template(…, context)` |
| **`get_context` pairing** | Separate from Python module | Same folder as `get_context` |
| **Testability** | Harder to assert structure | `get_html_for_route("/{route}/new")` can grep for symbols |
| **Size / structure** | Fine for small snippets | Better for helpers, patches, multiple concerns |

**Load interaction:** template wraps Desk **Client Script** in `frappe.init_client_script` first;
colocated `.js` is injected **after**. If **both** assign `frappe.init_client_script`, the
**file wins** (last assignment). Do not split logic across both without merging into one
function.

**When to prefer Desk:** quick one-off tweak, admin-owned copy, prototype before commit.

**When to prefer file:** non-trivial logic, patches, shared helpers, tests, Jinja from
`get_context`, team review.

**Hybrid (optional):** keep structure in `.js`; leave Desk field empty. Or expose small
helpers on `window` from the file and call them from a short Desk snippet (only if you accept
the overwrite risk above).

Do **not** hand-edit exported `web_form/**/*.json` for normal workflow — configure **Client
Script** in Desk or edit the colocated `.js`; see [`frappe-web-forms`](../frappe-web-forms/SKILL.md).

## Testing client script behaviour

1. **Rendered script (smoke):** integration test with `get_html_for_route(f"{route}/new")` —
   assert `frappe.init_client_script` and key function names appear (confirms file shipped).
2. **Submit outcome (integration):** `accept(web_form=…, data=json.dumps(payload))` under
   `as_guest()` when anonymous; assert returned `doc.name` and server-side message helpers.
3. **Do not** rely on a headless browser for stock Frappe tests unless the project already
   runs UI tests — grep + `accept()` usually suffice.

## Pitfalls

- **`after_load` on global `frappe.web_form`** at parse time — silent no-op after constructor.
- **Two `init_client_script` assignments** — Desk + file; only the last runs.
- **Non-standard Web Forms** — colocated `.js` is loaded only when `is_standard` and module path
  resolve; custom/one-off forms may need Desk **Client Script** only.
- **Success reference missing** — submit response uses `data.name`; fall back to
  `web_form.doc.name` if needed after patch.

## Related skills

- [`frappe-web-forms`](../frappe-web-forms/SKILL.md) — routes, `get_context`, Desk vs JSON
- [`frappe-form-custom-events`](../frappe-form-custom-events/SKILL.md) — Desk Form custom events
  (different runtime; Web Form uses `web_form.on`, not `frappe.ui.form.on`)
