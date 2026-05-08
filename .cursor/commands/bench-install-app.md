Install a Frappe app into this bench using `bench get-app` and `bench install-app`.

**Always** determine the correct `--branch` by reading the currently checked-out branch of the `frappe` app:

```bash
git -C <bench-root>/apps/frappe branch --show-current
```

Use that branch value (e.g. `version-16`) for every `get-app` call.

## Dependency installation

- **Do not** use `uv pip install` to install Python dependencies for apps.
- **Do** either:
  - pass **`--resolve-deps`** on `bench get-app` so Bench installs dependencies (preferred when fetching), or
  - run **`bench pip install`** (e.g. editable install of the app under `apps/`) if you need to install or retry dependencies after the app is on disk.

## Steps

1. Ask me for the app to install if I haven't specified it. Accept either:
   - A GitHub URL (e.g. `https://github.com/frappe/erpnext`)
   - A bare app name if it's a known Frappe app (resolve to the canonical GitHub URL)

2. Fetch the app at the correct branch (include `--resolve-deps` unless there is a documented reason not to):
   ```bash
   bench get-app <url-or-name> --branch <detected-branch> --resolve-deps
   ```

3. Install the app on the target site (ask me which site if ambiguous):
   ```bash
   bench --site <site> install-app <app-name>
   ```

4. Confirm success by listing installed apps:
   ```bash
   bench --site <site> list-apps
   ```
