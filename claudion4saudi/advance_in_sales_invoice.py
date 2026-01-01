from erpnext.accounts.party import get_party_account
from erpnext.controllers.accounts_controller import AccountsController
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice

from erpnext.controllers.accounts_controller import (
    get_advance_journal_entries,
    get_advance_payment_entries_for_regional,
)
import frappe
from frappe import _dict


def get_advance_sales_invoice_entries(
    party_type, party, party_account, order_list, include_unallocated=True, company=None
):
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
            "company": company,
        },
        fields=[
            "name",
            "posting_date",
            "total_allocated_amount",
            "paid_amount",
            "unallocated_amount",
            "references.reference_doctype",
            "paid_to",
            "total",  # Pre-tax amount (e.g., 100)
            "total_taxes_and_charges",  # Tax amount (e.g., 15)
            "grand_total",  # Total with tax (e.g., 115)
        ],
        order_by="posting_date desc",
    )

    result = []

    for adv_inv in advance_sales_invoices:
        # if include_unallocated or adv_inv.unallocated_amount > 0:
        if True:
            result.append(
                _dict(
                    {
                        "reference_type": "Advance Sales Invoice",
                        "reference_name": adv_inv.name,
                        "posting_date": adv_inv.posting_date,
                        # CRITICAL: advance_amount must be grand_total (items + tax = 2,300)
                        # This is the actual amount paid by customer
                        "advance_amount": adv_inv.grand_total,  # Full amount WITH tax (2,300)
                        "allocated_amount": adv_inv.total_allocated_amount,  # Should also be grand_total (2,300)
                        "unallocated_amount": adv_inv.unallocated_amount,
                        "sales_order": (
                            adv_inv.references[0].reference_name
                            if adv_inv.references
                            else None
                        ),
                        "reference_doctype": (
                            adv_inv.references[0].reference_doctype
                            if adv_inv.references
                            else None
                        ),
                        "exchange_rate": 1,
                        "account": adv_inv.paid_to,
                        "amount": adv_inv.grand_total,  # Full amount WITH tax (2,300)
                        # Tax breakdown for proper allocation
                        "advance_total": adv_inv.total,  # Pre-tax amount (2,000)
                        "advance_tax": adv_inv.total_taxes_and_charges,  # Tax amount (300)
                        "advance_grand_total": adv_inv.grand_total,  # Total with tax (2,300)
                    }
                )
            )

    return result



class CustomSalesInvoice(SalesInvoice):

    def get_advance_entries(self, include_unallocated=True):
        # frappe.msgprint("Getting advance entries for Sales Invoice")
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
            default_advance_account = (
                party_accounts[1] if len(party_accounts) == 2 else None
            )

        order_list = list(
            set(d.get(order_field) for d in self.get("items") if d.get(order_field))
        )

        journal_entries = get_advance_journal_entries(
            party_type,
            party,
            party_account,
            amount_field,
            order_doctype,
            order_list,
            include_unallocated,
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

        linked_sales_orders = set(order_list)

        filtered_payment_entries = []
        for pe in payment_entries:
            if pe.get("remarks"):
                for so in linked_sales_orders:
                    if so in pe["remarks"]:
                        filtered_payment_entries.append(pe)
                        break

        advance_sales_invoices = get_advance_sales_invoice_entries(
            party_type,
            party,
            party_account,
            order_list,
            include_unallocated,
            company=self.company,
        )

        res = journal_entries + filtered_payment_entries + advance_sales_invoices

        frappe.msgprint("Advance entries fetched successfully")

        return res
    
    def calculate_taxes_and_totals(self):
        """Override for Advance Sales Invoice handling"""
        
        # Call parent method - calculates standard taxes (FULL amounts)
        super().calculate_taxes_and_totals()
        
        # NO additional adjustment needed!
        # The allocated_amount in advances table already includes tax (23,000)
        # Standard ERPNext calculates: Outstanding = Grand Total - Total Advance
        # Which gives: 230,000 - 23,000 = 207,000 ✓
    
    # NOTE: adjust_total_advance_for_advance_sales_invoice() REMOVED
    # The allocated_amount from get_advance_entries_for_advance_sales_invoice() 
    # already returns grand_total (23,000 including tax).
    # Adding extra tax here was causing Total Advance = 26,000 (wrong!)
    #
    # NOTE: Tax reduction methods also removed - we now show full amounts 
    # and only deduct advance from outstanding, not from tax/grand total
    # This is cleaner and consistent with standard ERPNext behavior
    #
    # Final SI now shows:
    # - Items: 200,000
    # - Tax: 30,000 (full)
    # - Grand Total: 230,000
    # - Total Advance: 23,000 (includes 3,000 tax portion)
    # - Outstanding: 207,000

    def update_against_document_in_jv(self):
        """
        Override to handle Advance Sales Invoice separately from standard Payment Entry/Journal Entry.
        
        For Advance Sales Invoice:
        - We create our own reconciliation GL entries
        - Skip the standard reconcile_against_document which doesn't know about our structure
        
        For Payment Entry / Journal Entry:
        - Use standard ERPNext logic
        """
        from frappe.utils import flt
        from erpnext.accounts.utils import reconcile_against_document
        from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_dimensions
        from erpnext.accounts.general_ledger import make_gl_entries
        
        party_type = "Customer"
        party = self.customer
        party_account = self.debit_to
        dr_or_cr = "credit_in_account_currency"
        
        # Separate advances into two lists
        standard_advances = []  # Payment Entry, Journal Entry
        advance_si_list = []    # Advance Sales Invoice
        
        for d in self.get("advances"):
            if flt(d.allocated_amount) > 0:
                if d.reference_type == "Advance Sales Invoice":
                    advance_si_list.append(d)
                else:
                    # Standard Payment Entry or Journal Entry
                    args = frappe._dict({
                        "voucher_type": d.reference_type,
                        "voucher_no": d.reference_name,
                        "voucher_detail_no": d.reference_row,
                        "against_voucher_type": self.doctype,
                        "against_voucher": self.name,
                        "account": party_account,
                        "party_type": party_type,
                        "party": party,
                        "is_advance": "Yes",
                        "dr_or_cr": dr_or_cr,
                        "unadjusted_amount": flt(d.advance_amount),
                        "allocated_amount": flt(d.allocated_amount),
                        "precision": d.precision("advance_amount"),
                        "exchange_rate": (
                            self.conversion_rate
                            if self.party_account_currency != self.company_currency
                            else 1
                        ),
                        "grand_total": (
                            self.base_grand_total
                            if self.party_account_currency == self.company_currency
                            else self.grand_total
                        ),
                        "outstanding_amount": self.outstanding_amount,
                        "difference_account": frappe.get_cached_value(
                            "Company", self.company, "exchange_gain_loss_account"
                        ),
                        "exchange_gain_loss": flt(d.get("exchange_gain_loss")),
                        "difference_posting_date": d.get("difference_posting_date"),
                    })
                    standard_advances.append(args)
        
        # Handle standard advances (Payment Entry / Journal Entry) with ERPNext logic
        if standard_advances:
            active_dimensions = get_dimensions()[0]
            for x in standard_advances:
                for dim in active_dimensions:
                    if self.get(dim.fieldname):
                        x.update({dim.fieldname: self.get(dim.fieldname)})
            reconcile_against_document(standard_advances, active_dimensions=active_dimensions)
        
        # Handle Advance Sales Invoice with our custom GL logic
        if advance_si_list:
            self._reconcile_advance_sales_invoices(advance_si_list, party_account, party_type, party)
    
    def _reconcile_advance_sales_invoices(self, advance_si_list, party_account, party_type, party):
        """
        Create reconciliation GL entries for Advance Sales Invoice.
        
        When Advance SI was submitted, GL created:
        - Bank Debit: 11,500
        - Deferred Revenue Credit: 10,000 (items)
        - VAT Credit: 1,500 (tax)
        
        Now for reconciliation, we need to:
        - Debit Deferred Revenue: 10,000 (reverse items advance)
        - Debit VAT: 1,500 (reverse VAT advance)
        - Credit Debtors: 11,500 (reduce receivable by full advance)
        
        This ensures:
        - Debtors: 115,000 - 11,500 = 103,500 ✓
        - VAT: 1,500 + 15,000 - 1,500 = 15,000 ✓
        - Deferred Revenue: 10,000 - 10,000 = 0 ✓
        """
        from frappe.utils import flt
        from erpnext.accounts.general_ledger import make_gl_entries
        
        # Get Deferred Revenue account
        deferred_revenue_account = frappe.db.get_value(
            "Company", self.company, "default_advance_received_account"
        )
        if not deferred_revenue_account:
            frappe.throw(_("Please set Default Advance Received Account in Company {0}").format(self.company))
        
        gl_entries = []
        
        for d in advance_si_list:
            # Get Advance SI details
            adv_si = frappe.db.get_value(
                "Advance Sales Invoice",
                d.reference_name,
                ["paid_amount", "total_taxes_and_charges", "grand_total"],
                as_dict=True
            )
            
            if not adv_si:
                continue
            
            # Calculate proportional amounts based on allocation ratio
            # If partial allocation, scale down proportionally
            allocation_ratio = flt(d.allocated_amount) / flt(adv_si.grand_total) if adv_si.grand_total else 1
            items_amount = flt(adv_si.paid_amount) * allocation_ratio
            tax_amount = flt(adv_si.total_taxes_and_charges) * allocation_ratio
            total_amount = flt(d.allocated_amount)  # Full allocated amount (items + tax)
            
            # Get VAT account from Advance SI taxes (stored in "Advance Taxes and Charges" table)
            vat_account = frappe.db.get_value(
                "Advance Taxes and Charges",
                {"parent": d.reference_name, "parenttype": "Advance Sales Invoice"},
                "account_head"
            )
            
            sales_order = d.get("against_order") or self._get_sales_order_from_advance_si(d.reference_name)
            
            # 1. Debit Deferred Revenue (reverse items advance)
            gl_entries.append(
                self.get_gl_dict({
                    "account": deferred_revenue_account,
                    "party_type": party_type,
                    "party": party,
                    "against": party_account,
                    "debit": items_amount,
                    "debit_in_account_currency": items_amount,
                    "cost_center": self.cost_center,
                    "against_voucher_type": "Sales Order",
                    "against_voucher": sales_order,
                }, item=self)
            )
            
            # 2. Debit VAT (reverse VAT advance)
            if tax_amount > 0 and vat_account:
                gl_entries.append(
                    self.get_gl_dict({
                        "account": vat_account,
                        "against": party_account,
                        "debit": tax_amount,
                        "debit_in_account_currency": tax_amount,
                        "cost_center": self.cost_center,
                    }, item=self)
                )
            
            # 3. Credit Debtors (reduce receivable by full advance amount)
            gl_entries.append(
                self.get_gl_dict({
                    "account": party_account,
                    "party_type": party_type,
                    "party": party,
                    "against": deferred_revenue_account,
                    "credit": total_amount,
                    "credit_in_account_currency": total_amount,
                    "cost_center": self.cost_center,
                    "against_voucher_type": self.doctype,
                    "against_voucher": self.name,
                }, item=self)
            )
        
        if gl_entries:
            make_gl_entries(gl_entries, merge_entries=False)
    
    def _get_sales_order_from_advance_si(self, advance_si_name):
        """Get the linked Sales Order from Advance Sales Invoice"""
        references = frappe.get_all(
            "Payment Entry Reference",
            filters={
                "parent": advance_si_name,
                "reference_doctype": "Sales Order"
            },
            fields=["reference_name"],
            limit=1
        )
        return references[0].reference_name if references else None




# my_custom_app/customizations/utils.py

import frappe
from erpnext.accounts.utils import (
    update_reference_in_payment_entry as original_update_reference_in_payment_entry,
)


def update_reference_in_payment_entry(lst, active_dimensions=None):
    # Check if the payment_entry is an AdvanceSalesInvoice
    for payment_entry in lst:
        if hasattr(payment_entry, "get_exchange_rate"):
            return original_update_reference_in_payment_entry(lst, active_dimensions)

        # If it's not, handle it differently
        elif payment_entry.doctype == "Advance Sales Invoice":
            # Return a default or fallback value for exchange rate if needed
            payment_entry.exchange_rate = 1
        else:
            # Handle other cases as needed
            payment_entry.exchange_rate = 1

    return lst  # Return the modified list
