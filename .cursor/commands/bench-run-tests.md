Run the Frappe test suite for the module or DocType I am currently working on.

1. Identify the app and module from the file I have open or from the context I provide.
2. Construct the correct `bench run-tests` command, e.g.:
   ```
   bench run-tests --app frappe --module frappe.tests.test_foo
   ```
   Prefer the most specific test module available. If I specify a DocType name, resolve it to the test file automatically.
3. Execute the command from the bench root (`<bench-root>`, for example `~/frappe/develop`).
4. Report failing assertions clearly and suggest fixes.
