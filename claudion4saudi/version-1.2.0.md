# Version 1.2.0

Frappe/ERPNext **v16 compatibility**, without dropping v15. One branch runs on
both; every version difference is handled at runtime, never by forking the repo.

### v16 compatibility changes

- **Packaging.** Declared the runtime dependencies `pdf_file.py` actually imports
  (`pdfplumber`, `pdf2image`, `pytesseract`) — previously only `geoip2` was listed,
  so a clean install produced an app that raised `ImportError` the moment anything
  touched PDF handling. Added `[tool.bench.frappe-dependencies]` pinning the
  supported framework range to `>=15.0.0,<17.0.0`.
- **Hooks.** Removed the deprecated `from . import __version__ as app_version`
  (v16 reads the version from `__init__.py` directly).
- **Optional ZATCA integration.** `doc_events` pointed Advance Sales Invoice
  `on_submit` straight at `zatca_erpgulf`, so submitting failed on any site
  without that separate app. Now routed through `claudion4saudi.zatca_bridge`,
  which checks `frappe.get_installed_apps()` and no-ops when it is absent.
- **Dead config module.** Deleted `config/desktop.py` and `config/docs.py` —
  v12-era app config discovery, unread since v14.
- **Removed ERPNext symbol.** `get_party_tax_withholding_details` no longer
  exists anywhere in erpnext v16 (v15: `tax_withholding_category.py:101`). The
  import aborted `install-app` outright with
  `ImportError: Module import failed for Advance Sales Invoice`. It was dead code
  — its only call site was already commented out — so it is removed.
- **Wrong module, both versions.** `get_party_bank_account` was imported from
  `erpnext.accounts.party`, where it does not exist in v15 *or* v16. Re-pointed at
  `erpnext.accounts.doctype.bank_account.bank_account` (v16:102, v15:110).
- **Tests.** The three test stubs subclassed `frappe.tests.utils.FrappeTestCase`,
  a deprecation shim on v16 (`frappe/tests/utils/__init__.py:75`). They now try
  `frappe.tests.IntegrationTestCase` and fall back to `FrappeTestCase`. The
  fallback is mandatory, not defensive: `IntegrationTestCase` does not exist in
  frappe v15 at all, including at 15.119.0, the current branch head.
- **Fixtures.** Removed the frozen 215-entry `field_order` Property Setter for
  Sales Invoice, which describes a DocType that has 233 fields on v16 — it drops
  32 standard fields (the entire tax-withholding and UTM blocks, `apply_tds`,
  `coupon_code`, `item_wise_tax_details`, `sales_team_section` and more) and names
  14 fields that no longer exist. Widened `User.desk_theme` options to a superset
  of core, and re-anchored two custom fields whose `insert_after` pointed at a
  `zatca_erpgulf` field and at a colliding tab break.
- **Desk themes now persist.** Core `switch_theme` hard-codes
  `if theme in ["Dark", "Light", "Automatic"]` and silently discards anything else
  (identical at v16 `user.py:1448` and v15 `user.py:1347`), so the app's themes
  applied to the DOM and vanished on reload. `override_whitelisted_methods` now
  routes the endpoint to `claudion4saudi.override.switch_theme`, the theme names
  match what core actually sends (`toTitle(name)`, so `claudionday` →
  `Claudionday`), and an unknown theme raises instead of failing silently.
- **ZATCA badges.** `badge.js` requested `/assets/zatca_erpgulf/js/badges/*.png`,
  but those five PNGs ship in *this* app. All five URLs returned 404 against a
  running site; they now point at `/assets/claudion4saudi/js/badges/`.
- **Dead code.** Stripped a 2,631-line commented-out copy of ERPNext's
  PaymentEntry controller from `advance_sales_invoice.py` (3,650 → 525 lines,
  live code unchanged at 410), deleted the unwired `advance_in_sales_invoice.py`
  and a dead `check_if_advance_entry_modified` monkey patch, and removed 44
  unused imports.

### Pre-existing bugs fixed

These are not v16 regressions — each reproduces identically on v15, and each was
verified against the upstream tree before being touched.

- **`UnboundLocalError` in `get_payment_entry`.** `advance_sales_invoice_.py`
  referenced `tax` and `new_tax` *after* the `for tax in doc.get("taxes")` loop
  closed, so any source document with no taxes crashed — taking out the app's main
  entry point, the Sales Order → Advance Sales Invoice button, for a large share
  of ordinary documents. The same misplacement meant that when taxes *did* exist
  only the last row ever received `item_wise_tax_detail`.
- **Unsupported `charge_type` copied verbatim.** `get_payment_entry` copied each
  source tax row into the ASI with `charge_type` unchanged. The source is Sales
  Taxes and Charges (`On Net Total`, `On Item Quantity`); the destination is
  Advance Taxes and Charges, whose options are `("", Actual, On Paid Amount,
  On Previous Row Amount, On Previous Row Total)` — identical on v15 and v16. An
  ordinary KSA 15% VAT order therefore could not be converted at all, failing with
  `Type cannot be "On Net Total"`. Charge types the destination rejects are now
  collapsed to `Actual`, carrying the already-computed amount so the agreed VAT is
  preserved exactly.

  Note for reviewers: there is **no core behaviour to mirror here**. ERPNext v16's
  own `payment_entry.get_payment_entry` (`payment_entry.py:2885-3050`) never
  copies `doc.taxes` at all — there is no `append("taxes")`, `set("taxes")` or
  `.taxes =` anywhere in `payment_entry.py`, and the only tax reference inside the
  function is the `book_tax_discount_loss` check at `payment_entry.py:3037`, which
  concerns early-payment discount loss. Advance Taxes and Charges is normally
  populated by the user or recomputed by `apply_taxes()` (`payment_entry.py:961`).
  Copying source taxes is this app's own extension, so the conversion had to be
  chosen rather than copied.
- **Three undefined names.** `AdvanceSalesInvoice.allocate_amount_to_references()`
  called `allocate_open_payment_requests_to_references`,
  `get_payment_request_outstanding_set_in_references` and
  `get_references_outstanding_amount`, none of which were imported — the method
  raised `NameError` on every call. They came across from PaymentEntry only inside
  the commented-out block. All three still exist in erpnext v16 at
  `payment_entry.py:3101`, `:2241` and `:2168` with matching signatures, and are
  now imported from there rather than re-copied.

### Behaviour notes

- **Guest endpoints kept as-is.** `api.py:create_invoices` and
  `pdf_file.py:pdf_to_json` remain `allow_guest=True`. They are the integration
  contract for ERPGulf's GPOS product, and a compatibility release is the wrong
  place to change authentication semantics. They are now POST-only via the
  decorator rather than a hand-rolled `frappe.request.method` check.
  **Recommendation for maintainers:** these two endpoints accept unauthenticated
  requests and write invoices and files. Dropping `allow_guest` in favour of a
  token or API-key flow would be worth doing as its own change.
- **PDF generation.** `wkhtmltopdf` has been removed from Homebrew (the upstream
  project is archived), so it is no longer installable on macOS. v16 ships a
  native headless-Chrome backend; set Print Settings → PDF Generator to `chrome`.
  Print Settings still defaults to `wkhtmltopdf`.
- **Orphaned CSS themes.** Ten themes are still styled in the CSS bundles
  (`blue`, `red`, `peachgrey`, `claudiondark`, `claudionlight`, `claudionsimple`,
  `claudiontheme`, `claudiontheme2/3/4`) but are not offered by the switcher —
  they were already unreachable behind commented-out entries. Left in place;
  pruning them is a separate cosmetic change worth roughly 40 KB.
- **Fixture export must happen on a fresh site.** ERPNext's setup wizard creates
  Property Setters with the *same names* as nine of this app's and does not set a
  module, wiping `module: "Claudion4Saudi"` from them. Reproduced identically on
  v15 and v16. Because `hooks.fixtures` filters on that module, running
  `bench export-fixtures` on a site that has been through the setup wizard exports
  **3 of 12** property setters and silently drops the rest. The nine affected:

      Sales Invoice Item-barcode-hidden
      Sales Invoice Item-discount_account-hidden
      Sales Invoice Item-discount_account-mandatory_depends_on
      Packed Item-rate-read_only
      Sales Invoice-rounded_total-hidden
      Sales Invoice-rounded_total-print_hide
      Sales Invoice-scan_barcode-hidden
      Sales Invoice-tax_id-hidden
      Sales Invoice-tax_id-print_hide

  Deliberately **not** fixed here: resolving it means deciding whether ERPNext's
  KSA defaults or this app's setters should win, which is a product decision for
  ERPGulf rather than a compatibility one.
- **Advance Sales Invoice posts no GL entries.** The controller implements no
  `on_submit` and no `on_cancel` despite `is_submittable: 1`; the only submit hook
  is the optional ZATCA bridge. Submitting an ASI produces zero GL Entries, and
  cancelling has nothing to reverse. Stated here because it is easy to assume
  otherwise from the DocType name.
- **Test stubs.** The three `test_*.py` classes previously had no test methods, so
  `bench run-tests --app claudion4saudi` passed by collecting nothing. Each now has
  one real assertion covering DocType existence, meta load and custom-field
  presence.

### Supported versions

| | frappe | requires-python | DB driver | node |
|---|---|---|---|---|
| v15 | 15.x (tested 15.119.0) | `>=3.10,<3.15` | PyMySQL | `>=18` |
| v16 | 16.x (tested 16.32.0) | `>=3.14,<3.15` | PyMySQL + `mysqlclient` | `>=24` |

ERPNext tested at 15.120.0 and 16.33.0. The app's own `requires-python` stays
`>=3.10`; the narrower v16 floor comes from Frappe, not from this app. Python 3.14
happens to satisfy both ranges at these versions, which is convenient for running
the two branches on one machine, but v15 on 3.11 remains fully supported.

Because v16 adds `mysqlclient` (a C extension) while v15 uses only PyMySQL, a v16
bench additionally needs `pkg-config` and, on macOS, the `mariadb-connector-c`
formula. A v15-only bench needs neither.

### Contributors

- v16 compatibility work contributed via pull request.
