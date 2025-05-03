frappe.ui.form.on("Sales Invoice", {
    custom_fetch_advance_sales_invoice: function (frm) {
        let sales_order = frm.doc.items && frm.doc.items.length > 0 ? frm.doc.items[0].sales_order : null;

        if (!sales_order) {
            frappe.msgprint("No Sales Order found in the first item.");
            return;
        }

        frappe.call({
            method: "claudion4saudi.patch.get_advance_sales_invoices",
            args: { sales_order: sales_order },
            callback: function (r) {
                if (r.message && r.message.length) {
                    frm.clear_table("custom_advances_copy");

                    r.message.forEach(row => {
                        let child = frm.add_child("custom_advances_copy");
                        child.reference_name = row.name;
                        child.difference_posting_date= row.posting_date;
                        child.advance_amount = row.grand_total;
                        child.posting_time = row.posting_time;
                        child.uuid = row.custom_uuid;  // <- this pulls UUID from advance invoice
                    });

                    frm.refresh_field("custom_advances_copy");
                    frappe.msgprint("Advance Sales Invoices fetched.");
                } else {
                    frappe.msgprint("No matching Advance Sales Invoices found.");
                }
            }
        });
    }
});
