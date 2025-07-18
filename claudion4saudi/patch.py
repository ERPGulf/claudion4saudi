import erpnext.accounts.utils
import frappe
from frappe import _


# def custom_check_if_advance_entry_modified(entry):
#     frappe.msgprint("Custom advance check triggered.")
#     # pass  # Intentionally do nothing to skip the validation


def custom_check_if_advance_entry_modified(args):
    """
    check if there is already a voucher reference
    check if amount is same
    check if jv is submitted
    """
    if not args.get("unreconciled_amount"):
        args.update({"unreconciled_amount": args.get("unadjusted_amount")})

    ret = None
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
                    | (
                        journal_acc.reference_type.isin(
                            ["", "Sales Order", "Purchase Order"]
                        )
                    )
                )
                & (journal_entry.name == args.get("voucher_no"))
                & (journal_acc.name == args.get("voucher_detail_no"))
                & (journal_entry.docstatus == 1)
            )
        )

    else:
        payment_entry = frappe.qb.DocType("Sales Invoice Advance")
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
                .where(
                    payment_ref.reference_doctype.isin(
                        ("", "Sales Order", "Purchase Order")
                    )
                )
                .where(payment_ref.allocated_amount == args.get("unreconciled_amount"))
            )
        else:
            q = q.where(
                payment_entry.unallocated_amount == args.get("unreconciled_amount")
            )

    ret = q.run(as_dict=True)

    if not ret:
        frappe.throw(
            _(
                """NEW APP - Payment Entry has been modified after you pulled it. Please pull it again."""
            )
        )


def apply_monkey_patches():
    erpnext.accounts.utils.check_if_advance_entry_modified = (
        custom_check_if_advance_entry_modified
    )


from datetime import datetime

# In your results construction


@frappe.whitelist()
def get_advance_sales_invoices(sales_order):
    if not sales_order:
        frappe.throw(_("Sales Order is required"))

    # Step 1: Get matching Advance Sales Invoice names
    invoice_names = frappe.db.sql(
        """
        SELECT DISTINCT asi.name
        FROM `tabAdvance Sales Invoice` asi
        INNER JOIN `tabPayment Entry Reference` ref ON ref.parent = asi.name
        WHERE ref.reference_doctype = 'Sales Order'
        AND ref.reference_name = %s
        AND asi.docstatus = 1
        """,
        (sales_order,),
        as_dict=True,
    )

    # Step 2: Load full documents and build result
    results = []
    for row in invoice_names:
        doc = frappe.get_doc("Advance Sales Invoice", row.name)

        results.append(
            {
                "name": doc.name,
                "grand_total": doc.grand_total,
                "posting_date": doc.posting_date,
                "posting_time": doc.posting_time,
                "custom_uuid": doc.custom_uuid,  # <- Make sure this field exists in your DocType
            }
        )

    return results




def update_user_theme():
    default_theme = frappe.db.get_value(
        "Property Setter",
        {"property": "options", "doc_type": "User", "field_name": "desk_theme"},
        "default_value"
    )
    users = frappe.get_all("User", filters={"enabled": 1, "user_type": "System User"})
    for u in users:
        frappe.db.set_value("User", u.name, "desk_theme", default_theme)
    frappe.db.commit()
