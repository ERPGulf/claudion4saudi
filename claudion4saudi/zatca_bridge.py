import frappe


def zatca_background_on_submit(doc, method=None):
	"""Forward to zatca_erpgulf only when that app is actually installed.

	The hook used to point straight at
	`zatca_erpgulf.zatca_erpgulf.advance_payment.zatca_background_on_submit`,
	which makes submitting an Advance Sales Invoice fail on any site that does
	not have the (separate, optional) zatca_erpgulf app.
	"""
	if "zatca_erpgulf" not in frappe.get_installed_apps():
		return

	from zatca_erpgulf.zatca_erpgulf.advance_payment import (
		zatca_background_on_submit as _fn,
	)

	return _fn(doc, method)
