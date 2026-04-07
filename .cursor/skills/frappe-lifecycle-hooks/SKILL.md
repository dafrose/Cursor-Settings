---
name: frappe-lifecycle-hooks
description: >-
  Defines and consumes custom Frappe lifecycle hooks (before/on/after prefixes,
  cross-app hook keys vs handler paths, merge vs last-wins). Use when adding an
  extension point in hooks.py, registering handlers from another app, naming a
  new get_hooks key, or implementing cross-app hook integration without
  importing consumer apps.
---

# Frappe lifecycle hooks (custom extension points)

## Scope

Use when **your app defines** a new `frappe.get_hooks("…")` extension point (not only
`doc_events` / built-in keys from Frappe docs), or when **another app registers** handlers
for such a key.

Official overview: [Hooks](https://docs.frappe.io/framework/user/en/python-api/hooks).
Ecosystem examples: [reference.md](reference.md).

## Lifecycle prefixes

| Prefix | Anchor | Use when |
| --- | --- | --- |
| **`before_*`** | The **next** step is about to run | Handler can change inputs or replace a value before core code continues (`before_write_file`, `before_job`). Name like the upcoming action (`before_attach_pdf`, parallel to `on_print_pdf`). |
| **`after_*`** | The **previous** step just finished | Handler reacts to completed work (`after_migrate`, `after_job`). |
| **`on_*`** | A moment / event in a pipeline | Fired at a point, not strictly “before next line” (`on_print_pdf`). Also used in `doc_events` (`on_submit`). |

Avoid non-Frappe terms (`post_process`, `enhance`) in the **hook key**; they are fine as **handler function** names.

Pick **one** anchor per hook. `before_attach_pdf` and `after_embed_annexes` at the same call site are redundant—choose the name that matches how you document the call site.

**PDF pipeline pair:** Frappe’s `on_print_pdf` runs during print/PDF generation; **`before_attach_pdf`** is the matching extension point immediately before persisting/attaching the final PDF bytes (e.g. a provider app’s `save_and_attach` step).

## Cross-app naming

**Hook keys are global.** All installed apps merge into one namespace via `frappe.get_hooks(key)`.

| Layer | Convention | Example |
| --- | --- | --- |
| **Hook key** | Domain or lifecycle; **usually no app prefix** | `invoice_doctypes`, `before_job`, `on_print_pdf`, `before_attach_pdf` |
| **Handler value** | Full dotted path; **app name in the path** | `"consumer_app.my_module.hooks.enhance_pdf"` |
| **App-specific key** | Rare; short prefix if the key is not a shared ecosystem contract | `pd_standard_format_folder` (Print Designer) |

**Provider app** (calls `get_hooks`): owns the key name, documents signature and semantics, declares the key in its own `hooks.py` (often `[]`).

**Consumer apps**: append handlers in their `hooks.py`; must not import the provider’s orchestration module for side effects—only register paths.

Do **not** rely on `erpnext_*` / `provider_app_*` on every key unless the extension point is truly app-private; handlers are already namespaced by module path.

## Resolution semantics (decide explicitly)

Document how the provider consumes hooks:

| Pattern | Provider code | Examples |
| --- | --- | --- |
| **Merge / run all** | `for method in frappe.get_hooks("key") or []: frappe.call(method, …)` | `before_job`, `invoice_doctypes` (list values), multi-handler PDF transforms |
| **Last wins** | `hooks = frappe.get_hooks("key"); frappe.get_attr(hooks[-1])(…)` | `employee_holiday_list`, `override_whitelisted_methods` |
| **First wins** | `frappe.get_attr(hooks[0])(…)` | Some `get_*` resolvers |

Install order affects merge lists and “last wins” ([hooks resolution](https://docs.frappe.io/framework/user/en/python-api/hooks)). For chained `bytes` transforms, run **all** handlers in order and pass the return value to the next.

## Implementation checklist (provider)

1. **Name** the key (`before_<verb>_<noun>` e.g. `before_attach_pdf`, or `after_<completed_step>`).
2. **Declare** in provider `hooks.py`: `my_hook = []`  # extension point
3. **Call** from one obvious place in provider code; add a one-line comment with the hook key.
4. **Document** in README or docstring: arguments, return type (`None` = unchanged vs required return), merge vs last-wins, DocType guards (consumer responsibility).
5. **Tests**: install consumer app in test site (or patch `frappe.get_hooks`) and assert handler ran.

## Implementation checklist (consumer)

1. Register in consumer `hooks.py` only—no provider imports.
2. Handler signature matches provider docs; return `None` when not applicable (e.g. wrong DocType).
3. Keep handler idempotent where possible; do not assume you are the only handler unless documented as last-wins.

## Chaining binary payloads (PDF)

```python
def run_before_attach_pdf_hooks(doc, pdf_bytes: bytes) -> bytes:
    for method in frappe.get_hooks("before_attach_pdf") or []:
        result = frappe.call(method, doc=doc, pdf_bytes=pdf_bytes)
        if result is not None:
            pdf_bytes = result
    return pdf_bytes
```

Consumer:

```python
# consumer_app/hooks.py
before_attach_pdf = [
    "consumer_app.my_module.hooks.enhance_pdf",
]
```

Provider must **not** call `consumer_app` directly; consumer registers only when both apps are installed.

## vs `doc_events`

| | Custom `get_hooks` key | `doc_events` |
| --- | --- | --- |
| **When** | Extension inside your app’s pipeline (e.g. before attaching a generated PDF) | Standard document lifecycle on a DocType |
| **Coupling** | Optional apps register; provider stays generic | Tied to DocType + event name |

Use `doc_events` for “on **Sales Invoice** submit”; use a custom hook for “after my PDF is built, before I save the **File**”.

## Anti-patterns

- Provider imports consumer app to call `get_einvoice()` / `attach_xml_to_pdf`.
- Generic hook keys (`before_save`, `process_pdf`) that collide globally.
- Undocumented last-wins vs run-all behavior.
- `post_*` / `pre_*` keys instead of `before_*` / `after_*`.

## Additional resources

- [reference.md](reference.md) — Frappe / ERPNext / Print Designer examples
