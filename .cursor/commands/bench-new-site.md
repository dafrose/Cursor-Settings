Create a new Frappe site in this bench and install apps into it.

## Steps

### 1. Gather information

Ask me for:
- **Site name** (e.g. `mysite.localhost`)
- **Apps to install** (comma-separated list; `frappe` is always installed implicitly by `bench new-site`)

### 2. Detect the bench branch

```bash
git -C <bench-root>/apps/frappe branch --show-current
```

Use the result (e.g. `version-16`) as `<branch>` in any `bench get-app` calls below.

### 3. Check which apps are already fetched

```bash
ls <bench-root>/apps/
```

For each app I requested (excluding `frappe`):
- If it is **already in the list** → skip `get-app`.
- If it is **missing** → fetch it first:
  ```bash
  bench get-app <url-or-name> --branch <branch>
  ```
  Accept either a GitHub URL or a bare app name (resolve known Frappe apps to their canonical GitHub URL automatically).

### 4. Hand off to me

Do **not** run `bench new-site` yourself. Instead, print the exact command for me to run in my own terminal:

```
cd <bench-root> && bench new-site <site-name> --install-app <app1> --install-app <app2> ...
```

Include every requested app (except `frappe`, which is installed automatically) via repeated `--install-app` flags. Tell me the command requires my MySQL root password and an Administrator password for the new site.
