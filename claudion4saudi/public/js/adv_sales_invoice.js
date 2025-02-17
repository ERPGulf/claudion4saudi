frappe.ui.form.on("Sales Order", {
  refresh: function (frm) {
    console.log("asdfgh");

    frm.add_custom_button(
      "Advance Sales Invoice",
      () => {
        frappe.call({
          method:
            "claudion4saudi.advance_sales_invoice_.get_advance_sales_invoice_entry",
          args: { sales_order: frm.doc.name },
          callback: function (response) {
            if (response.message) {
              frappe.model.with_doctype("Advance Sales Invoice", () => {
                let asi = frappe.model.get_new_doc("Advance Sales Invoice");

                Object.assign(asi, response.message);

                frappe.ui.form.make_quick_entry(
                  "Advance Sales Invoice",
                  null,
                  null,
                  asi
                );
              });
            } else {
              frappe.msgprint({
                title: __("No Data Found"),
                message: __(
                  "No payment entry data available for this Sales Order."
                ),
                indicator: "orange",
              });
            }
          },
        });
      },
      __("Create"),
      Infinity
    );
  },
});
