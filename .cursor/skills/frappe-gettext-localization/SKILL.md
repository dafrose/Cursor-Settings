---
name: frappe-gettext-localization
description: >-
  Handles Frappe gettext localization for custom apps (`main.pot`, `*.po`,
  `*.mo`), including metadata sources from `hooks.py`, German translation flow,
  and header troubleshooting (`VERSION`, `FIRST AUTHOR`). Use when generating or
  fixing locale files in Frappe v15+ apps.
disable-model-invocation: true
---

# Frappe gettext localization (v15+)

Use this workflow for app translations in Frappe where locale files live at `<app>/<app>/locale/`.

## Command flow

Run from bench root:

```bash
bench generate-pot-file --app <app_name>
bench update-po-files --app <app_name> --locale <locale>
bench compile-po-to-mo --app <app_name> --locale <locale>
```

- `generate-pot-file`: rebuilds `locale/main.pot` from source strings.
- `update-po-files`: syncs `<locale>.po` with new/removed msgids.
- `compile-po-to-mo`: compiles runtime `.mo` files under `sites/assets/locale/...`.

## Where POT/PO header metadata comes from

Frappe builds gettext catalog metadata from app hooks in `hooks.py`:

- `app_title` -> `Project-Id-Version` project name (e.g. `"Frappe S3 Attachment VERSION"`).
- `app_email` -> `Report-Msgid-Bugs-To`, `Last-Translator`, `Language-Team`.
- `app_publisher` -> copyright holder comment.

So if regenerated headers are wrong, update `hooks.py` first (not just `.pot`/`.po` manually).

## Known defaults that surprise people

Two header artifacts are normal unless generator behavior is changed:

1. `# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.`
   - Babel default comment in POT output.
   - Not controlled by app metadata.

2. `Project-Id-Version: <app_title> VERSION`
   - `VERSION` appears because Frappe creates `Catalog(...)` without an explicit version.
   - App metadata controls `<app_title>`, but not the trailing `VERSION`.

## If you need cleaner headers

### Metadata-only fix (no framework patch)

Update app identity in `<app>/<app>/hooks.py`:

- `app_publisher = "ALYF GmbH"`
- `app_email = "hallo@alyf.de"`
- keep/adjust `app_title` as desired

Then regenerate POT/PO files.

### Framework-level fix (removes `VERSION`)

In `frappe/gettext/translate.py` (`new_catalog`), pass a `version=` argument to `Catalog(...)`.

Without this, Babel keeps literal `VERSION` in `Project-Id-Version`.

### `FIRST AUTHOR` removal

Requires post-processing or framework customization around Babel output. App hooks alone will not remove it.

## Translation quality checklist (DE or others)

- Preserve placeholders exactly (`{0}`, `{1}`, etc.).
- Preserve intentional whitespace in msgids/msgstrs (for example trailing space).
- Keep HTML snippets intact when present (`<b>...</b>`).
- Ensure no untranslated `msgstr ""` entries remain in target locale unless intentional.

