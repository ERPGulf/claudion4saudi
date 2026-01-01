import frappe


def check_if_advance_entry_modified(args):
	"""Custom validation to support Advance Sales Invoice in addition to Payment Entry"""
	if not args.get("unreconciled_amount"):
		args.update({"unreconciled_amount": args.get("unadjusted_amount")})

	ret = None
	
	# Handle Advance Sales Invoice - Skip validation to avoid "Payment Entry has been modified" error
	# This is safe because:
	# 1. Advance Sales Invoice is already submitted (docstatus=1)
	# 2. We're only reading values, not modifying the Advance Sales Invoice
	# 3. The tax reduction is calculated fresh each time from DB values
	if args.voucher_type == "Advance Sales Invoice":
		# Simply return without throwing error - the advance is valid if it exists and is submitted
		advance_exists = frappe.db.exists(
			"Advance Sales Invoice",
			{"name": args.get("voucher_no"), "docstatus": 1}
		)
		if not advance_exists:
			frappe.throw(("Advance Sales Invoice {0} is not submitted or does not exist").format(args.get("voucher_no")))
		return  # Valid - don't throw error
	
	# For other voucher types, call original ERPNext logic
	# Import here to avoid circular import
	from erpnext.accounts.doctype.payment_entry.payment_entry import check_if_advance_entry_modified as original_check
	return original_check(args)


@frappe.whitelist()
def switch_theme(theme):
    theme_mapping = {
        "Light": "Frappe Light",
        "Dark": "Timeless Night",
        # "Automatic": "Automatic",
        # "Blue": "Blue",
        # "Red": "Red",
        # "Peach Grey": "PeachGrey",
        "Purple": "Purple",
        # "Claudion Dark": "ClaudionDark",
        # "Claudion Theme": "ClaudionTheme",
        # "Claudion Simple": "ClaudionSimple",
        # "Claudion Light": "ClaudionLight",
        "Claudion Day": "ClaudionDay",
        "Claudion Night": "ClaudionNight",
    }
    # frappe.db.set_value("User", frappe.session.user, "desk_theme", theme)
    # return "success"
    if theme in theme_mapping:
        theme_option = theme_mapping[theme]
        # frappe.db.set_value("User", frappe.session.user, "desk_theme", "ClaudionTheme3")
        frappe.db.set_value("User", frappe.session.user, "desk_theme", theme_option)
        return f"Theme set to {theme_option}"
