
# import frappe
# from frappe.utils import nowdate

# @frappe.whitelist()
# def create_advance_sales_invoice(sales_order):
#     so_doc = frappe.get_doc("Sales Order", sales_order)

#     asi_doc = frappe.new_doc("Advance Sales Invoice")
#     asi_doc.payment_type = "Receive"  
#     asi_doc.party_type = "Customer"
#     asi_doc.party = so_doc.customer
#     asi_doc.company = so_doc.company
#     asi_doc.custom_sales_order_reference = sales_order  

#     asi_doc.posting_date = nowdate()
    
#     asi_doc.paid_from = frappe.db.get_value("Company", so_doc.company, "default_receivable_account")
#     asi_doc.paid_from_account_currency = frappe.db.get_value("Account", asi_doc.paid_from, "account_currency")
    
#     asi_doc.paid_to = frappe.db.get_value("Company", so_doc.company, "default_cash_account") 
#     asi_doc.paid_to_account_currency = frappe.db.get_value("Account", asi_doc.paid_to, "account_currency")

#     asi_doc.paid_amount = so_doc.grand_total
#     asi_doc.source_exchange_rate = 1.0  
#     asi_doc.base_paid_amount = asi_doc.paid_amount  
#     asi_doc.received_amount = asi_doc.paid_amount
#     asi_doc.target_exchange_rate = 1.0
#     asi_doc.base_received_amount = asi_doc.base_paid_amount

#     if not frappe.get_meta("Advance Sales Invoice").has_field("custom_item"):
#         frappe.throw("The 'custom_item' table does not exist in Advance Sales Invoice. Please verify your customization.")

#     for item in so_doc.items:
#         asi_doc.append("custom_item", {
#             "item_code": item.item_code,
#             "delivery_date": item.delivery_date,
#             "qty": item.qty,
#             "rate": item.rate,
#             "amount": item.amount
#         })

#     asi_doc.insert(ignore_permissions=True)
#     return asi_doc.name


import frappe
from frappe.utils import nowdate, flt, getdate
from erpnext.accounts.party import get_party_bank_account  # ✅ Import function to fetch bank account

@frappe.whitelist()
def create_advance_sales_invoice(sales_order):
    so_doc = frappe.get_doc("Sales Order", sales_order)

    over_billing_allowance = frappe.db.get_single_value("Accounts Settings", "over_billing_allowance") or 0
    if flt(so_doc.per_billed, 2) >= (100.0 + over_billing_allowance):
        frappe.throw(_("Can only make payment against unbilled Sales Order."))

    asi_doc = frappe.new_doc("Advance Sales Invoice")
    asi_doc.payment_type = "Receive"
    asi_doc.party_type = "Customer"
    asi_doc.party = so_doc.customer
    asi_doc.company = so_doc.company
    asi_doc.custom_sales_order_reference = sales_order
    asi_doc.posting_date = nowdate()

    asi_doc.paid_from = frappe.db.get_value("Company", so_doc.company, "default_receivable_account")
    asi_doc.paid_from_account_currency = frappe.db.get_value("Account", asi_doc.paid_from, "account_currency")

    asi_doc.paid_to = frappe.db.get_value("Company", so_doc.company, "default_cash_account")
    asi_doc.paid_to_account_currency = frappe.db.get_value("Account", asi_doc.paid_to, "account_currency")

    asi_doc.source_exchange_rate = frappe.db.get_value("Currency Exchange", 
        {"from_currency": asi_doc.paid_from_account_currency, "to_currency": asi_doc.paid_to_account_currency}, 
        "exchange_rate") or 1.0

    asi_doc.target_exchange_rate = frappe.db.get_value("Currency Exchange", 
        {"from_currency": asi_doc.paid_to_account_currency, "to_currency": asi_doc.paid_from_account_currency}, 
        "exchange_rate") or 1.0

    asi_doc.paid_amount = so_doc.grand_total if so_doc.grand_total else 0
    asi_doc.base_paid_amount = asi_doc.paid_amount * asi_doc.source_exchange_rate
    asi_doc.received_amount = asi_doc.paid_amount * asi_doc.source_exchange_rate
    asi_doc.base_received_amount = asi_doc.base_paid_amount * asi_doc.target_exchange_rate

    for tax in so_doc.taxes:
        charge_type = tax.charge_type
        if charge_type == "On Net Total":
            charge_type = "Actual"  

        asi_doc.append("taxes", {
            "charge_type": charge_type,
            "account_head": tax.account_head,
            "description": tax.description,
            "rate": tax.rate,
            "tax_amount": tax.tax_amount,
            "total": tax.total
        })

    vat_rate = 0
    for tax in so_doc.taxes:
        if "VAT" in tax.account_head:
            vat_rate = tax.rate / 100

    if vat_rate > 0:
        vat_amount = asi_doc.paid_amount * vat_rate
        asi_doc.paid_amount -= vat_amount  
        asi_doc.append("taxes", {
            "charge_type": "Actual",
            "account_head": "VAT Account",
            "description": "VAT on Advance Payment",
            "rate": vat_rate * 100,
            "tax_amount": vat_amount
        })

    for item in so_doc.items:
        asi_doc.append("custom_item", {
            "item_code": item.item_code,
            "delivery_date": item.delivery_date,
            "qty": item.qty,
            "rate": item.rate,
            "amount": item.amount
        })

    asi_doc.party_bank_account = get_party_bank_account("Customer", asi_doc.party)

    asi_doc.party_name = frappe.db.get_value("Customer", asi_doc.party, "customer_name")
    asi_doc.party_balance = frappe.db.get_value("Accounts", asi_doc.paid_from, "account_balance")

    asi_doc.letter_head = frappe.db.get_single_value("System Settings", "default_letter_head") or ""

    asi_doc.mode_of_payment = so_doc.get("mode_of_payment") or ""

    asi_doc.insert(ignore_permissions=True)
    return asi_doc.name
