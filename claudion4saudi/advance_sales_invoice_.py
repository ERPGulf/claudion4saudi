from erpnext.accounts.doctype.payment_entry.payment_entry import get_party_details
from erpnext.setup.utils import get_exchange_rate
from erpnext.accounts.party import get_party_account
import frappe
from frappe.utils import flt


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

    # ---- Reference Details (Logic from get_reference_details) ----
    reference_doctype = "Sales Order"
    reference_name = sales_order_doc.name
    party_account_currency = party_details.get("party_account_currency")

    # Get outstanding amount and other fields as per get_reference_details logic
    total_amount = sales_order_doc.grand_total or 0
    outstanding_amount = flt(total_amount) - flt(sales_order_doc.get("advance_paid"))
    exchange_rate = source_exchange_rate  # Same as paid_from_account_currency exchange rate
    account = get_party_account("Customer", sales_order_doc.customer, sales_order_doc.company)

    references = [
        {
            "reference_doctype": reference_doctype,
            "reference_name": reference_name,
            "due_date": sales_order_doc.delivery_date or frappe.utils.nowdate(),
            "total_amount": total_amount,
            "outstanding_amount": outstanding_amount,
            "allocated_amount": paid_amount,
            "exchange_rate": exchange_rate,
            "account": account,
        }
    ]

    asi_data["references"] = references

    # ---- Custom Items Table Mapping ----
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

    # ---- Taxes Table Mapping ----
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


import frappe
from frappe.utils import flt
from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_request_outstanding_set_in_references, get_references_outstanding_amount, allocate_open_payment_requests_to_references


@frappe.whitelist()

def allocate_amount_to_references(self, paid_amount, paid_amount_change, allocate_payment_amount):
    """
    Allocate `Allocated Amount` and `Payment Request` against `Reference` based on `Paid Amount` and `Outstanding Amount`.\n
    :param paid_amount: Paid Amount / Received Amount.
    :param paid_amount_change: Flag to check if `Paid Amount` is changed or not.
    :param allocate_payment_amount: Flag to allocate amount or not. (Payment Request is also dependent on this flag)
    """
    if not self.references:
        return

    if not allocate_payment_amount:
        for ref in self.references:
            ref.allocated_amount = 0
        return

    # calculating outstanding amounts
    precision = self.precision("paid_amount")
    total_positive_outstanding_including_order = 0
    total_negative_outstanding = 0
    paid_amount -= sum(flt(d.amount, precision) for d in self.deductions)

    for ref in self.references:
        reference_outstanding_amount = flt(ref.outstanding_amount)
        abs_outstanding_amount = abs(reference_outstanding_amount)

        if reference_outstanding_amount > 0:
            total_positive_outstanding_including_order += abs_outstanding_amount
        else:
            total_negative_outstanding += abs_outstanding_amount

    # calculating allocated outstanding amounts
    allocated_negative_outstanding = 0
    allocated_positive_outstanding = 0

    # checking party type and payment type
    if (self.payment_type == "Receive" and self.party_type == "Customer") or (
        self.payment_type == "Pay" and self.party_type in ("Supplier", "Employee")
    ):
        if total_positive_outstanding_including_order > paid_amount:
            remaining_outstanding = flt(
                total_positive_outstanding_including_order - paid_amount, precision
            )
            allocated_negative_outstanding = min(remaining_outstanding, total_negative_outstanding)

        allocated_positive_outstanding = paid_amount + allocated_negative_outstanding

    elif self.party_type in ("Supplier", "Employee"):
        if paid_amount > total_negative_outstanding:
            if total_negative_outstanding == 0:
                frappe.msgprint(
                    _("Cannot {0} from {1} without any negative outstanding invoice").format(
                        self.payment_type,
                        self.party_type,
                    )
                )
            else:
                frappe.msgprint(
                    _("Paid Amount cannot be greater than total negative outstanding amount {0}").format(
                        total_negative_outstanding
                    )
                )

            return

        else:
            allocated_positive_outstanding = flt(total_negative_outstanding - paid_amount, precision)
            allocated_negative_outstanding = paid_amount + min(
                total_positive_outstanding_including_order, allocated_positive_outstanding
            )

    # inner function to set `allocated_amount` to those row which have no PR
    def _allocation_to_unset_pr_row(
        row, outstanding_amount, allocated_positive_outstanding, allocated_negative_outstanding
    ):
        if outstanding_amount > 0 and allocated_positive_outstanding >= 0:
            row.allocated_amount = min(allocated_positive_outstanding, outstanding_amount)
            allocated_positive_outstanding = flt(
                allocated_positive_outstanding - row.allocated_amount, precision
            )
        elif outstanding_amount < 0 and allocated_negative_outstanding:
            row.allocated_amount = min(allocated_negative_outstanding, abs(outstanding_amount)) * -1
            allocated_negative_outstanding = flt(
                allocated_negative_outstanding - abs(row.allocated_amount), precision
            )
        return allocated_positive_outstanding, allocated_negative_outstanding

    # allocate amount based on `paid_amount` is changed or not
    if not paid_amount_change:
        for ref in self.references:
            allocated_positive_outstanding, allocated_negative_outstanding = _allocation_to_unset_pr_row(
                ref,
                ref.outstanding_amount,
                allocated_positive_outstanding,
                allocated_negative_outstanding,
            )

        allocate_open_payment_requests_to_references(self.references, self.precision("paid_amount"))

    else:
        payment_request_outstanding_amounts = (
            get_payment_request_outstanding_set_in_references(self.references) or {}
        )
        references_outstanding_amounts = get_references_outstanding_amount(self.references) or {}
        remaining_references_allocated_amounts = references_outstanding_amounts.copy()

        # Re allocate amount to those references which have PR set (Higher priority)
        for ref in self.references:
            if not ref.payment_request:
                continue

            # fetch outstanding_amount of `Reference` (Payment Term) and `Payment Request` to allocate new amount
            key = (ref.reference_doctype, ref.reference_name, ref.get("payment_term"))
            reference_outstanding_amount = references_outstanding_amounts[key]
            pr_outstanding_amount = payment_request_outstanding_amounts[ref.payment_request]

            if reference_outstanding_amount > 0 and allocated_positive_outstanding >= 0:
                # allocate amount according to outstanding amounts
                outstanding_amounts = (
                    allocated_positive_outstanding,
                    reference_outstanding_amount,
                    pr_outstanding_amount,
                )

                ref.allocated_amount = min(outstanding_amounts)

                # update amounts to track allocation
                allocated_amount = ref.allocated_amount
                allocated_positive_outstanding = flt(
                    allocated_positive_outstanding - allocated_amount, precision
                )
                remaining_references_allocated_amounts[key] = flt(
                    remaining_references_allocated_amounts[key] - allocated_amount, precision
                )
                payment_request_outstanding_amounts[ref.payment_request] = flt(
                    payment_request_outstanding_amounts[ref.payment_request] - allocated_amount, precision
                )

            elif reference_outstanding_amount < 0 and allocated_negative_outstanding:
                # allocate amount according to outstanding amounts
                outstanding_amounts = (
                    allocated_negative_outstanding,
                    abs(reference_outstanding_amount),
                    pr_outstanding_amount,
                )

                ref.allocated_amount = min(outstanding_amounts) * -1

                # update amounts to track allocation
                allocated_amount = abs(ref.allocated_amount)
                allocated_negative_outstanding = flt(
                    allocated_negative_outstanding - allocated_amount, precision
                )
                remaining_references_allocated_amounts[key] += allocated_amount  # negative amount
                payment_request_outstanding_amounts[ref.payment_request] = flt(
                    payment_request_outstanding_amounts[ref.payment_request] - allocated_amount, precision
                )
        # Re allocate amount to those references which have no PR (Lower priority)
        for ref in self.references:
            if ref.payment_request:
                continue

            key = (ref.reference_doctype, ref.reference_name, ref.get("payment_term"))
            reference_outstanding_amount = remaining_references_allocated_amounts[key]

            allocated_positive_outstanding, allocated_negative_outstanding = _allocation_to_unset_pr_row(
                ref,
                reference_outstanding_amount,
                allocated_positive_outstanding,
                allocated_negative_outstanding,
            )