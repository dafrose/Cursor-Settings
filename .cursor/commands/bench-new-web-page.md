# New Frappe web page (Jinja)

Scaffold a **blank** public web page under an app’s `www/` folder with Frappe Jinja enabled.

## Template (reference)

Match the pattern used in `apps/rentals/rentals/www/hello.html`:

- Extend the standard web layout: `{% extends "templates/web.html" %}`
- Put markup inside `{% block page_content %}…{% endblock %}`

Blank starter:

```jinja
{% extends "templates/web.html" %}
{% block page_content %}

{% endblock %}
```

## Steps

1. Ask me for:
   - **App name** (must exist under `apps/`, e.g. `rentals`)
   - **Filename** under that app’s `www/` (e.g. `about.html` — URL path will be `/about` without `.html` in the default route)
   - Optional: a one-line comment at the top describing the page

2. Resolve the full path: `apps/<app>/<package>/www/<filename>.html`  
   - The **package** is usually the same as the app name (e.g. `rentals/rentals/www/`). If the app layout differs, infer from existing `www/` files in that app.

3. Create the file with the blank template above (add optional HTML comments or a minimal placeholder only if I asked for it).

4. Remind me to reload or clear cache if the page does not appear: `bench --site <site> clear-cache` (or restart `bench start` if needed).

## Notes

- No Python controller is required for a static Jinja-only page served from `www/`.
- For dynamic context (passing variables from Python), add a matching `.py` file next to the template and use Frappe’s web page controller pattern — only if I ask for server-side data.
