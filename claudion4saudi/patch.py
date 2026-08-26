import frappe
from frappe import _


# def custom_check_if_advance_entry_modified(entry):
#     frappe.msgprint("Custom advance check triggered.")
#     # pass  # Intentionally do nothing to skip the validation


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
    """Backfill desk_theme ONLY for users whose current value is no longer valid.

    Previously this force-set every enabled System User's desk_theme to the
    Property Setter default on every single migrate, silently clobbering each
    user's own choice. It also ran unconditionally, so on a site where the
    Property Setter had not been applied yet `default_theme` was None and every
    user's theme was wiped.
    """
    ps = frappe.db.get_value(
        "Property Setter",
        {"property": "options", "doc_type": "User", "field_name": "desk_theme"},
        ["default_value", "value"],
        as_dict=True,
    )
    if not ps or not ps.default_value:
        # Property Setter not applied on this site - nothing safe to do.
        return

    allowed = {o.strip() for o in (ps.value or "").split("\n") if o.strip()}
    allowed.add(ps.default_value)

    for u in frappe.get_all(
        "User",
        filters={"enabled": 1, "user_type": "System User"},
        fields=["name", "desk_theme"],
    ):
        # Never overwrite a user's own valid choice.
        if u.desk_theme in allowed:
            continue
        frappe.db.set_value("User", u.name, "desk_theme", ps.default_value)
    # No frappe.db.commit() - migrate manages the transaction.
