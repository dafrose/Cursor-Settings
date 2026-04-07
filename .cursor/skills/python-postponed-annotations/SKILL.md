---
name: python-postponed-annotations
description: >-
  Unquoted type hints when a module uses from __future__ import annotations
  (Ruff UP037). Use when editing Python files with postponed annotations or
  fixing pre-commit UP037 failures.
---

# Postponed annotations and quoted types

When a module uses `from __future__ import annotations` (PEP 563), annotations are postponed—do **not** wrap return types or parameters in **string** quotes for names that can be written normally.

## Do

```python
from __future__ import annotations

import frappe

def make_doc() -> frappe.model.document.Document:
    ...
```

## Don't

```python
def make_doc() -> "frappe.model.document.Document":
    ...
```

Ruff rule **UP037** flags unnecessary quoted annotations; pre-commit will fail until they are removed.

Reserve quoted annotation strings only when a tool or version constraint truly requires them (unusual with `from __future__ import annotations`).
