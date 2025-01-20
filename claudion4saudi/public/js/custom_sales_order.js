frappe.ui.form.on("Sales Order", {
  refresh: function (frm) {
    if (flt(frm.doc.per_billed, 6) < 100) {
      console.log("js ok");
      frm.add_custom_button(
        "Partial Invoice",
        () => {
          frappe.prompt(
            {
              label: __("Payment Term"),
              fieldname: "payment_term",
              fieldtype: "Link",
              options: "Payment Term",
              description: "Select a Payment Term",
              get_query: () => {
                return {
                  query:
                    "claudion4saudi.deposit_invoice.deposit_invoice.get_payment_schedule_query",
                  filters: { parent: frm.doc.name },
                };
              },
            },
            (values) => {
              frappe.model.open_mapped_doc({
                method:
                  "claudion4saudi.deposit_invoice.deposit_invoice.make_deposit_invoice",
                frm: frm,
                args: { payment_term: values.payment_term },
              });
            },
            "Deposit Invoice"
          );
        },
        __("Create")
      );
    }
  },
  validate: function (frm) {
    // Calculate the sum of payment amounts in the payment_schedule table
    let total_payment = 0;
    frm.doc.payment_schedule.forEach((row) => {
      total_payment += row.payment_amount;
    });

    // Check if the sum of payment amounts matches the grand total
    if (total_payment !== frm.doc.grand_total) {
      frappe.throw(
        `The sum of Payment Amounts in Payment Schedule must be ${frm.doc.grand_total} but it is ${total_payment}.`
      );
    }
  },
});
frappe.ui.form.on("Payment Schedule", {
  payment_amount: calculate_pers,
  invoice_portion: calculate_pers_p,
});
function calculate_pers(frm, cdt, cdn) {
  const row = frappe.get_doc(cdt, cdn);
  row.invoice_portion = (row.payment_amount / frm.doc.grand_total) * 100;
  frm.refresh_field("payment_schedule");
}
function calculate_pers_p(frm, cdt, cdn) {
  const row = frappe.get_doc(cdt, cdn);
  row.payment_amount = (row.invoice_portion / 100) * frm.doc.grand_total;
  frm.refresh_field("payment_schedule");
}
