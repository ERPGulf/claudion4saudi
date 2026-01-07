__version__ = "1.1.1"

# Monkey patch to support Advance Sales Invoice in ERPNext's advance validation
import frappe
from frappe import _

def _patched_check_if_advance_entry_modified(args):
    """
    Custom validation to support Advance Sales Invoice in addition to Payment Entry.
    This replaces erpnext.accounts.utils.check_if_advance_entry_modified
    """
    if not args.get("unreconciled_amount"):
        args.update({"unreconciled_amount": args.get("unadjusted_amount")})

    # Handle Advance Sales Invoice - just verify it exists and is submitted
    if args.voucher_type == "Advance Sales Invoice":
        advance_exists = frappe.db.exists(
            "Advance Sales Invoice",
            {"name": args.get("voucher_no"), "docstatus": 1}
        )
        if not advance_exists:
            frappe.throw(_("Advance Sales Invoice {0} is not submitted or does not exist").format(args.get("voucher_no")))
        return  # Valid - don't throw error

    # For Journal Entry and Payment Entry, use original logic
    if args.voucher_type == "Journal Entry":
        journal_entry = frappe.qb.DocType("Journal Entry")
        journal_acc = frappe.qb.DocType("Journal Entry Account")

        q = (
            frappe.qb.from_(journal_entry)
            .inner_join(journal_acc)
            .on(journal_entry.name == journal_acc.parent)
            .select(journal_acc[args.get("dr_or_cr")])
            .where(
                (journal_acc.account == args.get("account"))
                & (journal_acc.party_type == args.get("party_type"))
                & (journal_acc.party == args.get("party"))
                & (
                    (journal_acc.reference_type.isnull())
                    | (journal_acc.reference_type.isin(["", "Sales Order", "Purchase Order"]))
                )
                & (journal_entry.name == args.get("voucher_no"))
                & (journal_acc.name == args.get("voucher_detail_no"))
                & (journal_entry.docstatus == 1)
            )
        )
    else:
        # Payment Entry
        payment_entry = frappe.qb.DocType("Payment Entry")
        payment_ref = frappe.qb.DocType("Payment Entry Reference")

        q = (
            frappe.qb.from_(payment_entry)
            .select(payment_entry.name)
            .where(payment_entry.name == args.get("voucher_no"))
            .where(payment_entry.docstatus == 1)
            .where(payment_entry.party_type == args.get("party_type"))
            .where(payment_entry.party == args.get("party"))
        )

        if args.voucher_detail_no:
            q = (
                q.inner_join(payment_ref)
                .on(payment_entry.name == payment_ref.parent)
                .where(payment_ref.name == args.get("voucher_detail_no"))
                .where(payment_ref.reference_doctype.isin(("", "Sales Order", "Purchase Order")))
                .where(payment_ref.allocated_amount == args.get("unreconciled_amount"))
            )
        else:
            q = q.where(payment_entry.unallocated_amount == args.get("unreconciled_amount"))

    ret = q.run(as_dict=True)

    if not ret:
        frappe.throw(_("Payment Entry has been modified after you pulled it. Please pull it again."))

# Apply the monkey patch
try:
    import erpnext.accounts.utils
    erpnext.accounts.utils.check_if_advance_entry_modified = _patched_check_if_advance_entry_modified
except Exception:
    pass  # Ignore if ERPNext not loaded yet
