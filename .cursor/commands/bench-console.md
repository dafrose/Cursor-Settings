Run a one-off Python snippet against a Frappe site via `bench execute`.

1. Ask me which site to target if not clear from context.
2. Ask me what Python expression or function I want to run.
3. Execute it with:
   ```
   bench --site <site> execute <dotted.path.to.function> [--args '[]'] [--kwargs '{}']
   ```
   For inline snippets that are not importable functions, use `bench console` interactively or write a temporary script.
4. Print the return value and any relevant output.
