from erpnext.accounts.doctype.payment_entry.payment_entry import get_party_details
from erpnext.setup.utils import get_exchange_rate
import frappe


@frappe.whitelist()
def get_advance_sales_invoice_entry(sales_order):
    sales_order_doc = frappe.get_doc("Sales Order", sales_order)

    party_details = get_party_details(
        company=sales_order_doc.company,
        party_type="Customer",
        party=sales_order_doc.customer,
        date=sales_order_doc.transaction_date,
    )

    company_currency = frappe.get_cached_value("Company", sales_order_doc.company, "default_currency")

    source_exchange_rate = 1
    target_exchange_rate = 1

    # Source exchange rate based on paid_from account currency
    if party_details.get("party_account_currency") != company_currency:
        source_exchange_rate = get_exchange_rate(
            from_currency=party_details.get("party_account_currency"),
            to_currency=company_currency,
            transaction_date=sales_order_doc.transaction_date,
        )

    bank_account_currency = company_currency
    if party_details.get("bank_account"):
        bank_account_currency = frappe.get_cached_value("Account", party_details.get("bank_account"), "account_currency")
        if bank_account_currency != company_currency:
            target_exchange_rate = get_exchange_rate(
                from_currency=bank_account_currency,
                to_currency=company_currency,
                transaction_date=sales_order_doc.transaction_date,
            )

    # Set paid_amount to Sales Order grand total initially (but editable later)
    paid_amount = sales_order_doc.grand_total or 0
    base_paid_amount = paid_amount * source_exchange_rate
    received_amount = paid_amount * (source_exchange_rate / target_exchange_rate)
    base_received_amount = received_amount * target_exchange_rate

    asi_data = {
        "company": sales_order_doc.company,
        "party_type": "Customer",
        "party": sales_order_doc.customer,
        "party_name": party_details.get("party_name"),
        "party_balance": party_details.get("party_balance"),
        "paid_from": party_details.get("party_account"),
        "paid_to": party_details.get("bank_account"),
        "paid_from_account_currency": party_details.get("party_account_currency"),
        "posting_date": frappe.utils.nowdate(),
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

    # Single Reference Entry - WITHOUT payment terms
    references = [
        {
            "reference_doctype": "Sales Order",
            "reference_name": sales_order_doc.name,
            # "bill_no": sales_order_doc.get("bill_no") or "",
            # "due_date": sales_order_doc.delivery_date or frappe.utils.nowdate(),
            "total_amount": sales_order_doc.grand_total or 0,
            "outstanding_amount": sales_order_doc.grand_total or 0,
            "allocated_amount": paid_amount,

            # "exchange_rate": source_exchange_rate or 1,
            "account": party_details.get("party_account") or "",
        }
    ]
    

    asi_data["references"] = references

    # Items Table Mapping
    custom_items = []
    for item in sales_order_doc.items:
        custom_items.append(
            {
                "item_code": item.item_code,
                "delivery_date": item.delivery_date,
                "qty": item.qty,
                "rate": item.rate,
                "amount": item.amount,
                "actual_qty": item.actual_qty,
            }
        )
    asi_data["custom_item"] = custom_items

    # Taxes Table Mapping
    asi_taxes = []
    for tax in sales_order_doc.taxes:
        asi_taxes.append(
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
            }
        )
    asi_data["taxes"] = asi_taxes

    return asi_data
