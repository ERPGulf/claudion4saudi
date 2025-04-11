
from erpnext.accounts.party import get_party_account
from erpnext.controllers.accounts_controller import AccountsController
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice

from erpnext.controllers.accounts_controller import get_advance_journal_entries, get_advance_payment_entries_for_regional
import frappe
from frappe import _dict

def get_advance_sales_invoice_entries(party_type, party, party_account, order_list, include_unallocated=True, company=None):
    if not order_list:
        return []

    if not company:
        frappe.throw("Company is required to fetch advance sales invoices")

    advance_sales_invoices = frappe.get_all(
        "Advance Sales Invoice",
        filters={
            "docstatus": 1,
            "party": party,
            "party_type": party_type,
            "paid_from": ["in", party_account],
            "reference_name": ["in", order_list],
            "company": company
        },
        fields=[
            "name", "posting_date", "total_allocated_amount", "paid_amount",
            "unallocated_amount", "references.reference_doctype", "paid_to"
        ],
        order_by="posting_date desc"
    )

    result = []

    for adv_inv in advance_sales_invoices:
        if include_unallocated or adv_inv.unallocated_amount > 0:
            result.append(_dict({
                "reference_type": "Advance Sales Invoice",
                "reference_name": adv_inv.name,
                "posting_date": adv_inv.posting_date,
                "advance_amount": adv_inv.paid_amount,
                "allocated_amount": adv_inv.total_allocated_amount,
                "unallocated_amount": adv_inv.unallocated_amount,
                "sales_order": adv_inv.references[0].reference_name if adv_inv.references else None,
                "reference_doctype": adv_inv.references[0].reference_doctype if adv_inv.references else None,
                "exchange_rate": 1,
                "account": adv_inv.paid_to,
                "amount": adv_inv.paid_amount,
            }))

    return result


class CustomSalesInvoice(SalesInvoice):

    def get_advance_entries(self, include_unallocated=True):
        frappe.msgprint("Getting advance entries for Sales Invoice")
        party_account = []
        default_advance_account = None

        if self.doctype in ["Sales Invoice", "POS Invoice"]:
            party_type = "Customer"
            party = self.customer
            amount_field = "credit_in_account_currency"
            order_field = "sales_order"
            order_doctype = "Sales Order"
            party_account.append(self.debit_to)
        else:
            party_type = "Supplier"
            party = self.supplier
            amount_field = "debit_in_account_currency"
            order_field = "purchase_order"
            order_doctype = "Purchase Order"
            party_account.append(self.credit_to)

        party_accounts = get_party_account(
            party_type, party=party, company=self.company, include_advance=True
        )

        if party_accounts:
            party_account.append(party_accounts[0])
            default_advance_account = party_accounts[1] if len(party_accounts) == 2 else None

        order_list = list(set(d.get(order_field) for d in self.get("items") if d.get(order_field)))

        journal_entries = get_advance_journal_entries(
            party_type, party, party_account, amount_field, order_doctype, order_list, include_unallocated
        )

        payment_entries = get_advance_payment_entries_for_regional(
            party_type,
            party,
            party_account,
            order_doctype,
            order_list,
            default_advance_account,
            include_unallocated,
        )

        advance_sales_invoices = get_advance_sales_invoice_entries(
            party_type,
            party,
            party_account,
            order_list,
            include_unallocated,
            company=self.company
        )

        res = journal_entries + payment_entries + advance_sales_invoices

        frappe.msgprint("Advance entries fetched successfully")
        frappe.msgprint(f"Advance entries: {res}")

        return res
