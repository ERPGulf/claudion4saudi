app_name = "claudion4saudi"
app_title = "Claudion4Saudi"
app_publisher = "Claudion"
app_description = "Claudion4Saudi"
app_email = "support@ERPGulf.com"
app_license = "mit"


from frappe import _


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


doc_events = {
    "Advance Sales Invoice": {
        "on_submit": "claudion4saudi.zatca_bridge.zatca_background_on_submit",
    },
}


override_whitelisted_methods = {
    # "frappe.core.doctype.user.user.switch_theme": "claudion4saudi.override.switch_theme",
    # "erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry":
    # "claudion4saudi.custom_payment_entry.custom_get_payment_entry"
}

fixtures = [
    {"dt": "Custom Field", "filters": {"module": "Claudion4Saudi"}},
    {"dt": "Property Setter", "filters": {"module": "Claudion4Saudi"}},
]
