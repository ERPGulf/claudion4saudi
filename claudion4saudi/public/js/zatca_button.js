// frappe.ui.form.on("Advance Sales Invoice", {
//   refresh: function (frm) {
//     if (frm.doc.docstatus === 0) {
//       frm.add_custom_button(
//         __("Send Invoice to Zatca"),
//         function () {
//           frappe.msgprint(__("Zatca Submission"));
//         },
//         __("Zatca Phase-2")
//       );
//     }
//   },
// });

frappe.ui.form.on("Advance Sales Invoice", {
  refresh: function (frm) {
    if (frm.doc.docstatus === 0) {
      frm.add_custom_button(
        __("Send Invoice to Zatca"),
        function () {
          frappe.call({
            method:
              "zatca_erpgulf.zatca_erpgulf.advance_payment.zatca_background_on_submit",
            args: {
              invoice_number: frm.doc.name,
              source_doc: frm.doc,
            },
            callback: function (r) {
              console.log(r.message);
              frm.reload_doc();
            },
          });
        },
        __("Zatca Phase-2")
      );
    }
  },
});
