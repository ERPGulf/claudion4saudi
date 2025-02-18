

# from erpnext.accounts.doctype.payment_entry.payment_entry import get_party_details
# from erpnext.setup.utils import get_exchange_rate
# import frappe


# @frappe.whitelist()
# def get_advance_sales_invoice_entry(sales_order):
#     sales_order_doc = frappe.get_doc("Sales Order", sales_order)

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

#     paid_amount = sales_order_doc.advance_paid or 0
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

#     # Reference for Sales Order
#     references = [
#         {
#             "reference_doctype": "Sales Order",
#             "reference_name": sales_order_doc.name,
#             "due_date": sales_order_doc.delivery_date,
#             "total_amount": sales_order_doc.grand_total,
#             "outstanding_amount": sales_order_doc.grand_total - paid_amount,
#             "allocated_amount": paid_amount,
#             "exchange_rate": source_exchange_rate,
#             "account": party_details.get("party_account"),
#         }
#     ]
#     asi_data["references"] = references

#     # Calculate Total Allocated Amount, Base Allocated Amount, and Unallocated Amount
#     total_allocated_amount = sum(d["allocated_amount"] for d in references)
#     base_total_allocated_amount = sum(d["allocated_amount"] * d["exchange_rate"] for d in references)
#     unallocated_amount = paid_amount - total_allocated_amount

#     asi_data["total_allocated_amount"] = abs(total_allocated_amount)
#     asi_data["base_total_allocated_amount"] = abs(base_total_allocated_amount)
#     asi_data["unallocated_amount"] = unallocated_amount

#     frappe.msgprint(f"Total Allocated Amount: {total_allocated_amount}")
#     print(f"Total Allocated Amount: {total_allocated_amount}")

#     # Items Table Mapping
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

#     # Taxes Table Mapping
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
from erpnext.accounts.party import get_party_account
from erpnext.selling.doctype import sales_order
from erpnext.setup.utils import get_exchange_rate
import frappe
from frappe.utils import flt, getdate, nowdate


@frappe.whitelist()
def get_advance_sales_invoice_entry(
    dt="Sales Order",
    dn=sales_order,
    party_amount=None,
    bank_account=None,
    bank_amount=None,
    party_type=None,
    payment_type=None,
    reference_date=None,
    ignore_permissions=False,
):
    doc = frappe.get_doc(dt, dn)

    if not party_type:
        party_type = "Customer"

    party_account = get_party_account(party_type, doc.customer, doc.company)


    if not party_account:
        frappe.throw(_("No Party Account found for Customer {0}").format(doc.customer))

    company_currency = frappe.get_cached_value("Company", doc.company, "default_currency")
    party_account_currency = frappe.get_cached_value("Account", party_account, "account_currency")

    if not payment_type:
        payment_type = "Receive"

    outstanding_amount = doc.grand_total - doc.advance_paid
    grand_total = doc.grand_total

    # bank or cash account
    bank_account_doc = None
    if bank_account:
        bank_account_doc = frappe.get_doc("Account", bank_account)

    source_exchange_rate = 1
    target_exchange_rate = 1

    if party_account_currency != company_currency:
        source_exchange_rate = get_exchange_rate(
            from_currency=party_account_currency,
            to_currency=company_currency,
            transaction_date=doc.transaction_date,
        )

    if bank_account_doc and bank_account_doc.account_currency != company_currency:
        target_exchange_rate = get_exchange_rate(
            from_currency=bank_account_doc.account_currency,
            to_currency=company_currency,
            transaction_date=doc.transaction_date,
        )

    paid_amount = outstanding_amount if not party_amount else flt(party_amount)
    base_paid_amount = paid_amount * source_exchange_rate
    received_amount = paid_amount * (source_exchange_rate / target_exchange_rate)
    base_received_amount = received_amount * target_exchange_rate

    advance_sales_invoice = frappe.new_doc("Advance Sales Invoice")
    advance_sales_invoice.company = doc.company
    advance_sales_invoice.party_type = "Customer"
    advance_sales_invoice.party = doc.customer
    advance_sales_invoice.payment_type = payment_type
    advance_sales_invoice.posting_date = nowdate()
    advance_sales_invoice.reference_date = doc.transaction_date
    advance_sales_invoice.paid_from = party_account
    advance_sales_invoice.paid_to = bank_account if bank_account else None
    advance_sales_invoice.paid_from_account_currency = party_account_currency
    advance_sales_invoice.paid_to_account_currency = (
        bank_account_doc.account_currency if bank_account_doc else company_currency
    )
    advance_sales_invoice.paid_amount = paid_amount
    advance_sales_invoice.base_paid_amount = base_paid_amount
    advance_sales_invoice.received_amount = received_amount
    advance_sales_invoice.base_received_amount = base_received_amount
    advance_sales_invoice.source_exchange_rate = source_exchange_rate
    advance_sales_invoice.target_exchange_rate = target_exchange_rate

    # Add reference
    advance_sales_invoice.append(
        "references",
        {
            "reference_doctype": dt,
            "reference_name": dn,
            "due_date": doc.delivery_date,
            "total_amount": grand_total,
            "outstanding_amount": outstanding_amount,
            "allocated_amount": paid_amount,
            "exchange_rate": source_exchange_rate,
            "account": party_account,
        },
    )

    # Add items from Sales Order to Custom Items Table
    for item in doc.items:
        advance_sales_invoice.append(
            "custom_item",
            {
                "item_code": item.item_code,
                "delivery_date": item.delivery_date,
                "qty": item.qty,
                "rate": item.rate,
                "amount": item.amount,
                "actual_qty": item.actual_qty,
            },
        )

    # Add taxes from Sales Order to Taxes Table
    for tax in doc.taxes:
        advance_sales_invoice.append(
            "taxes",
            {
                "charge_type": tax.charge_type,
                "account_head": tax.account_head,
                "description": tax.description,
                "rate": tax.rate,
                "tax_amount": tax.tax_amount,
                "base_tax_amount": tax.base_tax_amount,
                "total": tax.total,
                "base_total": tax.base_total,
                "cost_center": tax.cost_center,
            },
        )

    # advance_sales_invoice.set_missing_values()

    return advance_sales_invoice
