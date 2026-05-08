Run a Frappe migration for the current site.

1. Ask me which site to migrate if it is not clear from context (list available sites from `bench/sites/`).
2. Run:
   ```
   bench --site <site> migrate
   ```
   from `<bench-root>` (for example `~/frappe/bench16`).
3. Watch the output for errors. If any patch or schema change fails, show the relevant traceback and suggest a fix.
