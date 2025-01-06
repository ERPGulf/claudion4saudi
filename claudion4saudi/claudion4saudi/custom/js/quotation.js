frappe.ui.form.on("Quotation Item", {
    item_code: function (frm, cdt, cdn) {
        var row = locals[cdt][cdn]
        var customer = frm.doc.party_name;
        frappe.call({
            method: "claudion4saudi.claudion4saudi.custom.py.quotation.sales_invoice_list",
            args: {
                item: row.item_code,
                company: frm.doc.company,
            },
            callback: function (r) {
                frm.clear_table("custom_quote_sales_price");
                frm.clear_table("custom_purchase_item_details");
                frm.refresh_field("custom_quote_sales_price");
                frm.refresh_field("custom_purchase_item_details");
                if (r.message) {
                    // Clear the custom_quote_sales_price and custom_purchase_item_details tables


                    // Update custom_quote_sales_price with Sales Invoice data (si_list)
                    if (r.message.si_list) {
                        r.message.si_list.forEach(function (invoice) {
                            var sales_row = frm.add_child("custom_quote_sales_price");
                            sales_row.quotation = invoice.parent;  // Assuming sales_invoice field in child table
                            sales_row.amount = invoice.rate;  // Assuming amount field in child table
                            sales_row.customer = invoice.party_name
                        });
                        frm.refresh_field("custom_quote_sales_price");
                    }

                    // Update custom_purchase_item_details with Purchase Invoice data (pi_list)
                    if (r.message.pi_list) {
                        r.message.pi_list.forEach(function (invoice) {
                            var purchase_row = frm.add_child("custom_purchase_item_details");
                            purchase_row.purchase_invoice = invoice.parent;  // Assuming purchase_invoice field in child table
                            purchase_row.amount = invoice.rate;  // Assuming amount field in child table
                            purchase_row.supplier = invoice.supplier;
                        });
                        frm.refresh_field("custom_purchase_item_details");
                    }
                }
            },
        });
        frappe.call({
            method: "claudion4saudi.claudion4saudi.custom.py.quotation.fetch_rate_details",
            args: {
                item_code: row.item_code,
                customer: customer
            },
            freeze: true,
            callback: function (r) {

                frm.clear_table("custom_quotation_itemwise_rate_details");
                if (r.message) {
                    frm.set_value('custom_quotation_itemwise_rate_details', r.message);
                }
                refresh_field('custom_quotation_itemwise_rate_details');
            }
        });

    }
})