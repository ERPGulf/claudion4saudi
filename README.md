## Claudion4Saudi

Features for Saudi Arabian ERPNext users — Arabic name fields, Advance Sales
Invoices against Sales Orders, quotation rate history, and custom desk themes.

### Supported versions

| | frappe | erpnext | requires-python | node |
|---|---|---|---|---|
| **v15** | 15.x (tested 15.119.0) | 15.x (tested 15.120.0) | `>=3.10,<3.15` | `>=18` |
| **v16** | 16.x (tested 16.32.0) | 16.x (tested 16.33.0) | `>=3.14,<3.15` | `>=24` |

One branch supports both; version differences are handled at runtime.

The Python ranges come from Frappe, not from this app — `claudion4saudi` itself
declares `requires-python = ">=3.10"`. Frappe v16 pins `>=3.14,<3.15`, so a v16
bench must run Python 3.14 exactly, while a v15 bench is happy anywhere from 3.10
to 3.14. If you want one machine to run both branches, 3.14 currently satisfies
each range.

### Installation

Common to both:

```bash
bench get-app https://github.com/ERPGulf/claudion4saudi
bench --site <site> install-app claudion4saudi
bench --site <site> migrate
bench build --app claudion4saudi
```

#### v16 prerequisites

v16 needs a little more than v15, because Frappe v16 adds `mysqlclient` (a C
extension) on top of PyMySQL, and `bench` builds it from source:

- **Python 3.14** — exactly; 3.13 and 3.15 both fail Frappe's own pin.
- **Node 24+** — `frappe/package.json` declares `engines.node >= 24`.
- **`pkg-config`** — `bench` refuses to install an app without it.
- **`mariadb-connector-c`** — on macOS, `bench` runs
  `brew --prefix mariadb-connector-c` and feeds the result to `PKG_CONFIG_PATH`
  when building `mysqlclient`. Install the formula even though it is keg-only.
- **`uv`** — bench 5.x uses it for every virtualenv and install operation.

On macOS:

```bash
brew install python@3.14 node@24 pkg-config mariadb-connector-c uv
```

A **v15-only** bench needs none of `pkg-config`, `mariadb-connector-c` or Python
3.14 — v15 talks to MariaDB through PyMySQL, which is pure Python.

### Optional dependency: `zatca_erpgulf`

ZATCA e-invoicing is provided by the separate
[`zatca_erpgulf`](https://github.com/ERPGulf/zatca_erpgulf) app. It is **optional**:

- Advance Sales Invoice `on_submit` is routed through
  `claudion4saudi.zatca_bridge`, which no-ops when `zatca_erpgulf` is not
  installed, so submitting works on a site without it.
- The ZATCA status badges on Advance Sales Invoice are served from this app's own
  assets and render regardless.
- The "Send to ZATCA" button calls into `zatca_erpgulf` and will fail without it.

### PDF generation

Print Settings still defaults to `wkhtmltopdf`, which is no longer packaged on
macOS (the upstream project is archived and the Homebrew formula was removed).
Frappe v16 ships a native headless-Chrome backend — set **Print Settings → PDF
Generator** to `chrome`.

### Maintainer note: exporting fixtures

**Only run `bench export-fixtures --app claudion4saudi` against a site that has
NOT been through the ERPNext setup wizard.**

The setup wizard creates Property Setters with the same names as nine of this
app's and leaves `module` empty, overwriting the app's `module: "Claudion4Saudi"`
tag. Since `hooks.fixtures` filters on that module, exporting from such a site
writes **3 of 12** property setters and silently drops the other nine. This
reproduces identically on v15 and v16.

Use a freshly installed site for fixture work, and check `git diff` afterwards —
the entry count should not fall.

### Development

```bash
bench --site <site> run-tests --app claudion4saudi
ruff check . --select E9,F63,F7,F82,F401
```

After changing `hooks.py`, run `bench --site <site> clear-cache`. App hooks are
cached per site, so a new `override_whitelisted_methods` entry is not served until
you do — the endpoint silently keeps resolving to core.

#### License

mit
