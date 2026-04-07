# Lifecycle hooks — ecosystem reference

## Built-in lifecycle keys (Frappe)

| Key | Prefix | Consumption |
| --- | --- | --- |
| `before_request` / `after_request` | before / after | Request pipeline |
| `before_job` / `after_job` | before / after | RQ worker (`frappe/utils/background_jobs.py`) |
| `before_migrate` / `after_migrate` | before / after | Migrate |
| `before_write_file` | before | `File` save (`frappe/utils/file_manager.py`) |
| `on_print_pdf` | on | After PDF generated (`frappe/utils/print_utils.py`) |

## Cross-app extension (ERPNext ecosystem)

Keys are **shared nouns**; each app adds list entries. Provider merges lists.

| Key | Provider calls | ERPNext | HRMS (example) |
| --- | --- | --- | --- |
| `invoice_doctypes` | `frappe.get_hooks("invoice_doctypes")` | Sales/Purchase Invoice | Expense Claim |
| `accounting_dimension_doctypes` | same pattern | long default list | extra doctypes |
| `company_data_to_be_ignored` | transaction deletion | defaults | extra doctypes |

## Override-style (last handler wins)

```python
# erpnext/setup/doctype/employee/employee.py
hrms_override = frappe.get_hooks("employee_holiday_list")
if hrms_override:
    return frappe.get_attr(hrms_override[-1])(employee, raise_exception, as_on)
```

Hook key has **no** `hrms_` prefix; HRMS supplies the winning handler path.

## Print / attach PDF pipeline

| Key | When | Owner |
| --- | --- | --- |
| `on_print_pdf` | During PDF generation (`print_utils`) | Frappe |
| `before_attach_pdf` | After bytes ready, before `save_and_attach` | Provider app (custom) |

Print Designer handlers (Frappe-owned keys):

| Key | Handler app path |
| --- | --- |
| `pdf_body_html` | `print_designer.pdf.pdf_body_html` |
| `pdf_generator` | `print_designer.pdf_generator.pdf.get_pdf` |
| `get_print_format_template` | `print_designer.pdf.get_print_format_template` |

App-specific config hook: `pd_standard_format_folder` (abbreviated prefix, not `print_designer_`).

## Cross-app PDF hook pattern (provider + consumer)

| Piece | Owner |
| --- | --- |
| `before_attach_pdf` | **Provider app** defines key + calls hooks (pairs with Frappe `on_print_pdf`) |
| Shared PDF helpers | **Provider app** library |
| `enhance_pdf` handler | **Consumer app** — transform `pdf_bytes` before attach |

## `frappe.get_hooks` helpers

```python
# All apps, merged list
frappe.get_hooks("invoice_doctypes")

# Single app only
frappe.get_hooks("fixtures", app_name="my_app")

# Iterate (merge pattern)
for method in frappe.get_hooks("before_job") or []:
    frappe.call(method, ...)
```

## Docs

- [Hooks (Python API)](https://docs.frappe.io/framework/user/en/python-api/hooks)
- [Hooks reference](https://frappeframework.com/docs/user/en/python-api/hooks) — list of built-in keys
