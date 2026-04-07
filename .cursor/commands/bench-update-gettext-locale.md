Update gettext localization files for a Frappe app using an interactive workflow.

Goal:
- Ask the user which bench, app, and locale to target (using `AskQuestion`).
- Regenerate POT/PO files with Frappe commands.
- Re-apply and adapt translations by comparing PO changes from git diff against the committed file.
- Compile MO files.

Execution context:
- Anchor every shell command to app root using an absolute path prefix:
  - `cd <absolute_app_path> && <command>`
- `<absolute_app_path>` must contain `<bench>/apps/<app>`.
- Do not run commands from an implicit current directory.
- Preflight example before running gettext or git commands:
  - `cd <absolute_app_path> && pwd`
  - confirm the output path is exactly `<absolute_app_path>`.

Follow this workflow exactly:

1. Discover options, then ask with `AskQuestion`
   - Discover bench candidates (directories that look like bench roots, typically containing `apps` and `sites`).
   - For the selected bench, list installed app folders from `<bench>/apps/` (exclude hidden/system folders).
   - For locale options, inspect `<bench>/apps/<app>/<app>/locale/` using shell listing from app root (do not rely on glob-only discovery).
   - Derive locale names from existing `*.po` filenames.
   - Ask in one or more `AskQuestion` prompts:
     - bench target
     - app target
     - locale target (offer only `de` and any other existing locales)
   - If the needed option is not present, include an `other` option and then ask a normal chat follow-up for the exact value.
   - If the user wants a locale that does not yet exist, ask a separate yes/no style question whether to add another locale, then request the locale code in normal chat.

2. Validate paths (before running commands)
   - Bench root: `<bench>`
   - App locale directory: `<bench>/apps/<app>/<app>/locale`
   - Target files:
     - POT: `<locale_dir>/main.pot`
     - PO: `<locale_dir>/<locale>.po`

3. Confirm git baseline for PO comparison
   - Run git checks in the app repository:
     - verify `<locale_dir>/<locale>.po` is tracked at `HEAD`
     - if tracked, the committed file is the baseline for diff analysis
     - if not tracked (new file), mark baseline as unavailable and treat every msgid as new
   - Do not create a backup copy of the PO file.

4. Run gettext update commands from app root
   - Use absolute app-path anchoring:
     - `cd <absolute_app_path> && bench generate-pot-file --app <app>`
     - `cd <absolute_app_path> && bench update-po-files --app <app> --locale <locale>`

5. Detect added and altered msgids (using git diff when available)
   - If git baseline is available:
     - Read old entries from committed PO content at `HEAD`.
     - Compare with current working tree PO and inspect `git diff -- <locale_dir>/<locale>.po`.
     - Build a mapping:
       - `old_msgid -> old_msgstr` from committed content.
     - Classify entries in current PO:
       - Added msgid: new `msgid` not present in old mapping.
       - Altered msgid: entry is marked `fuzzy` and has previous msgid metadata (`#| msgid "..."`) OR git diff context links replacement of one msgid with another.
     - For altered entries, recover previous translation from old mapping using previous msgid.
   - If git baseline is unavailable (new file):
     - Treat every msgid in the current PO as added.
     - No altered-msgid adaptation is possible.

6. Update translations in PO
   - For added msgids:
     - Fill `msgstr` with a proper translation in the selected locale.
   - For altered msgids:
     - Do not rewrite from scratch.
     - Start from previous translation and adapt wording to the new msgid content.
     - Preserve placeholders and formatting exactly (`{0}`, `%s`, HTML tags, whitespace).
   - Remove `fuzzy` flag only when translation is fully adapted and correct.

7. Compile runtime MO files
   - Use absolute app-path anchoring:
     - `cd <absolute_app_path> && bench compile-po-to-mo --app <app> --locale <locale>`

8. Final checks and report
   - Confirm PO and POT were updated.
   - Report:
     - Count of added msgids translated.
     - Count of altered msgids adapted from previous translations.
     - Any unresolved entries left intentionally empty.

Quality requirements:
- Preserve placeholders and token order exactly.
- Keep intentional spacing and markup.
- Avoid broad defensive normalization; use direct msgid/msgstr handling.
- If translation intent is ambiguous, ask a focused follow-up question before finalizing that entry.
