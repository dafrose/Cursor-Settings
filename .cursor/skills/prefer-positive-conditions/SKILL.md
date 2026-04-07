---
name: prefer-positive-conditions
description: >-
  Prefer positive if-conditions over early negation returns when both are equally
  clear. Use when writing control flow in Python, JavaScript, or Frappe client
  scripts.
---

# Prefer positive conditions

Structure control flow so the **main path sits inside a positive check** (`if (ready) { … }`), not an early exit on negation (`if (!ready) return`).

## Default

```javascript
// ✅ GOOD — run when the precondition holds
if (frm.fields_dict.annex_rows) {
	frm.set_query("file", "annex_rows", function () { … });
}
```

```javascript
// ❌ AVOID — early exit on negation (same logic, harder to scan)
if (!frm.fields_dict.annex_rows) {
	return;
}
frm.set_query("file", "annex_rows", function () { … });
```

```python
# ✅ GOOD
if custom_field_installed():
	_set_custom_field_hidden(hidden=not enabled)
else:
	_create_custom_field()
```

## When negation is fine

Use negative / early-exit style only when a positive branch would **complicate** the code:

- **Guard clauses** at the top of a long function where the happy path is most of the body (e.g. `if not doc: return`).
- **Validation failures** that must abort before any side effects.
- **Deep nesting** — a single early `if not x: return` is flatter than wrapping a large block in `if x:`.

If both forms are equally clear, prefer the positive form.
