frappe.ui.form.on("Sales Invoice", {
  refresh: function (frm) {
    if (frm.doc.custom_sales_order_payment_term) {
      frm.set_df_property("items", "read_only", 1);
    }
  },
});
