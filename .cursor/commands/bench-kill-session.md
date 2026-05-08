Kill leftover processes from a previous Frappe **bench** development session (e.g. after `bench start` / honcho exited badly). **Scope to one bench directory** so other benches on the machine are not touched.

### Why things “stick around” (honcho / dev server)

- **Honcho** (used by `bench start`) stops **all** Procfile processes when **any one** of them exits. If you see `schedule.1 stopped (rc=0)` (or another worker exiting) followed by `sending SIGTERM to …`, that cascade is **honcho**, not a random bug—fixing it usually means making `bench schedule` stay running or adjusting the Procfile, not only killing orphans.
- **`bench serve`** often uses the **Werkzeug/Flask development server** with a **watchdog reloader** (“Restarting with watchdog”). The **child** process may **not** include `bench serve` in its command line, so matchers that only look for `bench serve` / `gunicorn` miss it.
- **`bench watch`** may run **`node esbuild`** (or similar) under **yarn**; children may show as `node …/esbuild` and must still match the bench.

---

1. **Resolve the bench root** (directory that contains `Procfile`). If the user did not give a path, infer from context (e.g. workspace `version-15` or wherever `Procfile` lives). Ask once if still ambiguous.

2. **Collect candidate PIDs** for that bench only, then deduplicate. Use the shell.

   **A. `ps` (macOS: `ps -ax -o pid=,args=`; Linux: `ps -eo pid=,args=` if needed)**  
   Include a PID if the full command line contains the **absolute bench root** and matches **any** of:
   - `honcho`
   - `redis-server`
   - `bench serve`, `bench watch`, `bench schedule`, `bench worker`
   - `gunicorn`
   - `socketio.js` or `frappe/socketio`
   - **`python` / `python3` / `Python`** and also (`frappe` or `werkzeug` or `sites/` or `bench` in a way that clearly indicates the dev app server or reloader—not unrelated scripts in the repo)
   - **`node`** and also (`esbuild` or `vite` or `rollup` or `socketio` or `yarn` with paths under the bench)

   **B. Redis pidfiles** (if present): read PIDs from `<bench>/config/pids/redis_cache.pid` and `redis_queue.pid` and verify each PID is still running (`kill -0`).

   **C. Redis listen ports**: from `<bench>/config/redis_cache.conf` and `redis_queue.conf`, read the `port` lines. For each port, use `lsof -ti tcp:<port> -sTCP:LISTEN` (or equivalent) and keep a PID only if `ps` shows it is `redis-server`.

   **D. Bench “well-known” TCP ports (orphan dev server / socketio / watch)**  
   These catch processes whose argv no longer mentions `bench serve`:
   - Parse **`--port`** from the `web:` line in `Procfile` (if absent, default **8003** or read **`webserver_port`** from `<bench>/sites/common_site_config.json` if present).
   - Read **`socketio_port`** from `<bench>/sites/common_site_config.json` if present (typical **9003**).
   - Optionally read **`file_watcher_port`** from the same file (often used for live reload / esbuild; only kill if `ps` shows `node` or a clear bench-related command).

   For each such port, take PIDs from `lsof -ti tcp:<port> -sTCP:LISTEN`. **Keep** a PID only if `ps` shows it is plausibly this bench (e.g. `python`/`node` with the bench path in the command line, or a path under `<bench>/apps/` / `<bench>/env/`). **Do not** kill unrelated servers on the same port without that check.

3. **If there are no PIDs**, say so and stop.

4. **Otherwise** print the bench root and the list of PIDs. If the user asked for a dry run / preview only, stop after printing.

5. **Terminate**: send **SIGTERM** to each PID, wait about one second, then **SIGKILL** any that are still alive. Report what was killed.

6. **Do not** kill processes whose command line does not tie them to that bench path (except redis matched via pidfile/port as above, and port **D** only after the plausibility check). **Never** kill the current session’s shell or unrelated system services.
