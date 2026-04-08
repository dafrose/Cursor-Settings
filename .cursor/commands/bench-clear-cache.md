Clear the Frappe cache for a site and restart workers if needed.

1. Identify the target site (ask if ambiguous).
2. Run:
   ```
   bench --site <site> clear-cache
   ```
3. If I also need doctypes to be reloaded (e.g. after a schema change without migrate), also run:
   ```
   bench --site <site> clear-website-cache
   ```
4. Optionally restart the bench:
   ```
   bench restart
   ```
   Ask me before doing the restart.
