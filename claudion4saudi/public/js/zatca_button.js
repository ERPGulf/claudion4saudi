frappe.ui.form.on("Advance Sales Invoice", {
  refresh: function (frm) {
      if (
          frm.doc.docstatus === 1 &&
          !["CLEARED", "REPORTED"].includes(frm.doc.custom_zatca_status)
      ) {
          frm.add_custom_button(__("Send invoice to Zatca"), function () {
              frm.call({
                  method: "zatca_erpgulf.zatca_erpgulf.advance_payment.zatca_background",
                  args: {
                      invoice_number: frm.doc.name,
                      source_doc: frm.doc
                  },
                  freeze: true,
                  freeze_message: __("Sending invoice to ZATCA..."),
                  callback: function (r) {
                      if (r.message) {
                          frappe.msgprint(r.message);
                      }
                      frm.reload_doc();
                  }
              });
          }, __("Zatca Phase-2"));
      }
  }
});
