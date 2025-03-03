import erpnext
from erpnext.accounts.doctype.journal_entry.journal_entry import get_exchange_rate
from erpnext.accounts.party import get_party_account
import frappe
from frappe.utils import flt

# @frappe.whitelist()
# def get_reference_details_(
# 	reference_doctype, reference_name, party_account_currency, party_type=None, party=None
# ):
# 	# Ensure the function only works for Sales Orders
# 	if reference_doctype != "Sales Order":
# 		frappe.throw(_("This function only supports Sales Orders."))

# 	frappe.logger().info(f"Fetching reference details for {reference_doctype} - {reference_name}")

# 	# Fetch the Sales Order document
# 	ref_doc = frappe.get_doc(reference_doctype, reference_name)

# 	# Get Company Currency
# 	company_currency = ref_doc.get("company_currency") or erpnext.get_company_currency(ref_doc.company)

# 	# Initialize variables
# 	total_amount = outstanding_amount = exchange_rate = None

# 	# Ensure that outstanding amount is correctly calculated
# 	total_amount = ref_doc.get("base_rounded_total") or ref_doc.get("rounded_total") or ref_doc.get("base_grand_total") or ref_doc.get("grand_total")
# 	outstanding_amount = flt(total_amount) - flt(ref_doc.get("advance_paid"))

# 	# Get exchange rate
# 	if party_account_currency == company_currency:
# 		exchange_rate = 1
# 	else:
# 		exchange_rate = ref_doc.get("conversion_rate") or get_exchange_rate(party_account_currency, company_currency, ref_doc.transaction_date)

# 	# Get Customer and Account Details
# 	party = ref_doc.get("customer")
# 	account = get_party_account("Customer", party, ref_doc.company)

# 	# Construct response dictionary
# 	res = frappe._dict({
# 		"due_date": ref_doc.get("delivery_date"),  # Using delivery date as due date for SO
# 		"total_amount": flt(total_amount),
# 		"outstanding_amount": flt(outstanding_amount),
# 		"exchange_rate": flt(exchange_rate),
# 		"bill_no": ref_doc.get("name"),  # Bill No is Sales Order Name
# 		"account": account
# 	})

# 	frappe.logger().info(f"Reference details fetched: {res}")

# 	return res


@frappe.whitelist()
def get_reference_details_(reference_doctype, reference_name, party_account_currency, party_type=None, party=None):
    if reference_doctype != "Sales Order":
        frappe.throw(_("This function only supports Sales Orders."))

    frappe.logger().info(f"Fetching reference details for {reference_doctype} - {reference_name}")

    ref_doc = frappe.get_doc(reference_doctype, reference_name)
    company_currency = ref_doc.get("company_currency") or erpnext.get_company_currency(ref_doc.company)

    total_amount = ref_doc.get("base_rounded_total") or ref_doc.get("rounded_total") or ref_doc.get("base_grand_total") or ref_doc.get("grand_total")
    outstanding_amount = flt(total_amount) - flt(ref_doc.get("advance_paid"))

    if party_account_currency == company_currency:
        exchange_rate = 1
    else:
        exchange_rate = ref_doc.get("conversion_rate") or get_exchange_rate(party_account_currency, company_currency, ref_doc.transaction_date)

    party = ref_doc.get("customer")
    account = get_party_account("Customer", party, ref_doc.company)

    res = frappe._dict({
        "due_date": ref_doc.get("delivery_date"),
        "total_amount": flt(total_amount),
        "outstanding_amount": flt(outstanding_amount),
        "exchange_rate": flt(exchange_rate),
        "bill_no": ref_doc.get("name"),
        "account": account
    })

    frappe.logger().info(f"Reference details fetched: {res}")
    return res