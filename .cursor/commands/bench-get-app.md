Fetch a Frappe app into this bench using `bench get-app`.

**Always** determine the correct `--branch` by reading the currently checked-out branch of the `frappe` app:

```bash
git -C /Users/daniel/frappe/bench16/apps/frappe branch --show-current
```

Use that branch value (e.g. `version-16`) for the `--branch` flag.

## Steps

1. Ask me for the app to fetch if I haven't specified it. Accept either:
   - A GitHub URL (e.g. `https://github.com/frappe/erpnext`)
   - A bare app name if it's a known Frappe app (resolve to the canonical GitHub URL)

2. Fetch the app at the correct branch:
   ```bash
   bench get-app <url-or-name> --branch <detected-branch>
   ```

3. Confirm success by listing the apps directory:
   ```bash
   ls /Users/daniel/frappe/bench16/apps/
   ```
