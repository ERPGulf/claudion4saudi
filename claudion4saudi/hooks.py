app_name = "claudion4saudi"
app_title = "Claudion4Saudi"
app_publisher = "Claudion"
app_description = "Claudion4Saudi"
app_email = "support@ERPGulf.com"
app_license = "mit"


from frappe import _
from . import __version__ as app_version


app_include_css = "claudion4saudi.bundle.css"
app_include_js = ["claudion4saudi.bundle.js"]


doctype_js = {
    "Quotation": "claudion4saudi/custom/js/quotation.js",
    "Sales Order": [
        "public/js/custom_sales_order.js",
        "public/js/adv_sales_invoice.js",
    ],
    "Sales Invoice": ["public/js/custom_sales_invoice.js", "public/js/new_fetch.js"],
    "Advance Sales Invoice": [
        "public/js/zatca_button.js",
        "public/js/badge.js",
    ],
}


after_migrate = "claudion4saudi.migrate.after_migrate"


override_doctype_class = {
    "Sales Invoice": "claudion4saudi.advance_in_sales_invoice.CustomSalesInvoice",
}


doc_events = {
    "Advance Sales Invoice": {
        "on_submit": "zatca_erpgulf.zatca_erpgulf.advance_payment.zatca_background_on_submit",
    },
}


# NOTE: override_whitelisted_methods not used
# check_if_advance_entry_modified is handled via monkey patch in __init__.py
# override_whitelisted_methods only works for @frappe.whitelist() methods, not internal functions

fixtures = [
    {"dt": "Custom Field", "filters": {"module": "Claudion4Saudi"}},
    {"dt": "Property Setter", "filters": {"module": "Claudion4Saudi"}},
]
