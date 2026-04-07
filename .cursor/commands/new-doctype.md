Scaffold a new Frappe DocType.

1. Ask me for:
   - App name (must exist under `apps/`)
   - Module name
   - DocType name
   - Key fields (name, fieldtype, options if Link/Select)
   - Whether it is a Submittable, Child, or Single DocType
2. Create the DocType via `bench console` using the Frappe Python API (`frappe.new_doc`), set all properties, then call `doc.insert()`.
3. Run `bench --site <site> migrate` so the schema is applied.
4. Confirm the generated files under `apps/<app>/<module>/<doctype_snake>/`.
