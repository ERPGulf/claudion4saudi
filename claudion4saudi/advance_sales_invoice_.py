# from erpnext.accounts.doctype.payment_entry.payment_entry import get_party_details
# from erpnext.setup.utils import get_exchange_rate
# from erpnext.accounts.party import get_party_account
# import frappe
# from frappe.utils import flt

# frappe.msgprint("python loads")

# @frappe.whitelist()
# def get_advance_sales_invoice_entry(sales_order):
#     sales_order_doc = frappe.get_doc("Sales Order", sales_order)

#     # Fetch Party Details
#     party_details = get_party_details(
#         company=sales_order_doc.company,
#         party_type="Customer",
#         party=sales_order_doc.customer,
#         date=sales_order_doc.transaction_date,
#     )

#     company_currency = frappe.get_cached_value("Company", sales_order_doc.company, "default_currency")

#     source_exchange_rate = 1
#     target_exchange_rate = 1

#     # Source exchange rate based on paid_from account currency
#     if party_details.get("party_account_currency") != company_currency:
#         source_exchange_rate = get_exchange_rate(
#             from_currency=party_details.get("party_account_currency"),
#             to_currency=company_currency,
#             transaction_date=sales_order_doc.transaction_date,
#         )

#     bank_account_currency = company_currency
#     if party_details.get("bank_account"):
#         bank_account_currency = frappe.get_cached_value("Account", party_details.get("bank_account"), "account_currency")
#         if bank_account_currency != company_currency:
#             target_exchange_rate = get_exchange_rate(
#                 from_currency=bank_account_currency,
#                 to_currency=company_currency,
#                 transaction_date=sales_order_doc.transaction_date,
#             )

#     # Set paid_amount to Sales Order grand total initially (but editable later)
#     paid_amount = sales_order_doc.grand_total or 0
#     base_paid_amount = paid_amount * source_exchange_rate
#     received_amount = paid_amount * (source_exchange_rate / target_exchange_rate)
#     base_received_amount = received_amount * target_exchange_rate

#     asi_data = {
#         "company": sales_order_doc.company,
#         "party_type": "Customer",
#         "party": sales_order_doc.customer,
#         "party_name": party_details.get("party_name"),
#         "party_balance": party_details.get("party_balance"),
#         "paid_from": party_details.get("party_account"),
#         "paid_to": party_details.get("bank_account"),
#         "paid_from_account_currency": party_details.get("party_account_currency"),
#         "posting_date": frappe.utils.nowdate(),
#         "reference_date": sales_order_doc.transaction_date,
#         "reference_no": sales_order_doc.name,
#         "payment_type": "Receive",
#         "paid_amount": paid_amount,
#         "base_paid_amount": base_paid_amount,
#         "received_amount": received_amount,
#         "base_received_amount": base_received_amount,
#         "source_exchange_rate": source_exchange_rate,
#         "target_exchange_rate": target_exchange_rate,
#         "payment_reference": sales_order_doc.name,
#     }

#     # ---- Reference Details (Logic from get_reference_details) ----
#     reference_doctype = "Sales Order"
#     reference_name = sales_order_doc.name
#     party_account_currency = party_details.get("party_account_currency")

#     # Get outstanding amount and other fields as per get_reference_details logic
#     total_amount = sales_order_doc.grand_total or 0
#     outstanding_amount = flt(total_amount) - flt(sales_order_doc.get("advance_paid"))
#     exchange_rate = source_exchange_rate  # Same as paid_from_account_currency exchange rate
#     account = get_party_account("Customer", sales_order_doc.customer, sales_order_doc.company)

#     references = [
#         {
#             "reference_doctype": reference_doctype,
#             "reference_name": reference_name,
#             "due_date": sales_order_doc.delivery_date or frappe.utils.nowdate(),
#             "total_amount": total_amount,
#             "outstanding_amount": outstanding_amount,
#             "allocated_amount": paid_amount,
#             "exchange_rate": exchange_rate,
#             "account": account,
#         }
#     ]

#     asi_data["references"] = references

#     # ---- Custom Items Table Mapping ----
#     custom_items = []
#     for item in sales_order_doc.items:
#         custom_items.append(
#             {
#                 "item_code": item.item_code,
#                 "delivery_date": item.delivery_date,
#                 "qty": item.qty,
#                 "rate": item.rate,
#                 "amount": item.amount,
#                 "actual_qty": item.actual_qty,
#             }
#         )
#     asi_data["custom_item"] = custom_items

#     # ---- Taxes Table Mapping ----
#     asi_taxes = []
#     for tax in sales_order_doc.taxes:
#         asi_taxes.append(
#             {
#                 "charge_type": tax.charge_type,
#                 "account_head": tax.account_head,
#                 "description": tax.description,
#                 "rate": tax.rate,
#                 "tax_amount": tax.tax_amount,
#                 "base_tax_amount": tax.base_tax_amount,
#                 "total": tax.total,
#                 "base_total": tax.base_total,
#                 "cost_center": tax.cost_center,
#             }
#         )
#     asi_data["taxes"] = asi_taxes

#     return asi_data

from erpnext.accounts.doctype.payment_entry.payment_entry import get_party_details
from erpnext.setup.utils import get_exchange_rate
from erpnext.accounts.party import get_party_account
import frappe
from frappe.utils import flt, nowdate

@frappe.whitelist()
def get_advance_sales_invoice_entry(sales_order):
    sales_order_doc = frappe.get_doc("Sales Order", sales_order)

    # Fetch Party Details
    party_details = get_party_details(
        company=sales_order_doc.company,
        party_type="Customer",
        party=sales_order_doc.customer,
        date=sales_order_doc.transaction_date,
    )

    company_currency = frappe.get_cached_value("Company", sales_order_doc.company, "default_currency")

    # Get Party Account Fallback
    party_account = party_details.get("party_account") or get_party_account("Customer", sales_order_doc.customer, sales_order_doc.company)
    party_account_currency = party_details.get("party_account_currency") or company_currency

    # Get Bank Account Details
    bank_account = party_details.get("bank_account") or None
    bank_account_currency = (
        frappe.get_cached_value("Account", bank_account, "account_currency") if bank_account else company_currency
    )

    # Fetch Exchange Rates
    source_exchange_rate = (
        get_exchange_rate(from_currency=party_account_currency, to_currency=company_currency, transaction_date=sales_order_doc.transaction_date)
        if party_account_currency != company_currency
        else 1
    )

    target_exchange_rate = (
        get_exchange_rate(from_currency=bank_account_currency, to_currency=company_currency, transaction_date=sales_order_doc.transaction_date)
        if bank_account_currency != company_currency
        else 1
    )

    # Paid Amount Logic
    paid_amount = flt(sales_order_doc.grand_total, 2)
    base_paid_amount = flt(paid_amount * source_exchange_rate, 2)
    received_amount = flt(paid_amount * (source_exchange_rate / target_exchange_rate), 2)
    base_received_amount = flt(received_amount * target_exchange_rate, 2)

    asi_data = {
        "company": sales_order_doc.company,
        "party_type": "Customer",
        "party": sales_order_doc.customer,
        "party_name": party_details.get("party_name"),
        "party_balance": party_details.get("party_balance"),
        "paid_from": party_account,
        "paid_to": bank_account,
        "paid_from_account_currency": party_account_currency,
        "posting_date": nowdate(),
        "reference_date": sales_order_doc.transaction_date,
        "reference_no": sales_order_doc.name,
        "payment_type": "Receive",
        "paid_amount": paid_amount,
        "base_paid_amount": base_paid_amount,
        "received_amount": received_amount,
        "base_received_amount": base_received_amount,
        "source_exchange_rate": source_exchange_rate,
        "target_exchange_rate": target_exchange_rate,
        "payment_reference": sales_order_doc.name,
    }

    # ---- Reference Details ----
    references = []
    for so_item in sales_order_doc.items:
        reference_doctype = "Sales Order"
        reference_name = sales_order_doc.name
        total_amount = flt(sales_order_doc.grand_total, 2)
        outstanding_amount = flt(total_amount - flt(sales_order_doc.get("advance_paid", 0)), 2)

        references.append({
            "reference_doctype": reference_doctype,
            "reference_name": reference_name,
            "due_date": sales_order_doc.delivery_date or nowdate(),
            "total_amount": total_amount,
            "outstanding_amount": outstanding_amount,
            "allocated_amount": paid_amount,
            "exchange_rate": source_exchange_rate,
            "account": party_account,
        })
    
    asi_data["references"] = references

    # ---- Custom Items Table ----
    asi_data["custom_item"] = [
        {
            "item_code": item.item_code,
            "delivery_date": item.delivery_date,
            "qty": flt(item.qty, 2),
            "rate": flt(item.rate, 2),
            "amount": flt(item.amount, 2),
            "actual_qty": flt(item.actual_qty, 2),
        }
        for item in sales_order_doc.items
    ]

    # ---- Taxes Table ----
    asi_data["taxes"] = [
        {
            "charge_type": tax.charge_type,
            "account_head": tax.account_head,
            "description": tax.description,
            "rate": flt(tax.rate, 2),
            "tax_amount": flt(tax.tax_amount, 2),
            "base_tax_amount": flt(tax.base_tax_amount, 2),
            "total": flt(tax.total, 2),
            "base_total": flt(tax.base_total, 2),
            "cost_center": tax.cost_center,
        }
        for tax in sales_order_doc.taxes
    ]

    return asi_data
