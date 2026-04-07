---
name: frappe-reqd-fields
description: >-
  Skip empty-value guards on mandatory (reqd) Frappe fields in Desk save hooks.
  Use when writing validate/before_save hooks, child-table row handlers, or
  server code that reads reqd columns on normal form saves.
---

# Mandatory reqd fields — no empty checks on Desk save

## Scope

If you load data from a mandatory (`reqd`) field, do not verify whether it has a value. Assume that it does and use it.

Desk blocks save when a mandatory field is empty (parent fields and child-table rows). Server hooks that run on normal Desk save (`validate`, `before_save`, …) can therefore skip `if row.file:`-style guards on `reqd` child columns.

Reserve explicit empty checks for API/import paths or optional fields only.
