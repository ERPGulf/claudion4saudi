frappe.ui.form.on("Advance Sales Invoice", {
  refresh(frm) {
    console.log("Advance Sales Invoice JS Loaded");

    if (frm.doc.references && frm.doc.references.length > 0) {
      frm.trigger("calculate_totals");
    }
  },

  paid_amount: function (frm) {
    if (!frm.doc.paid_amount) return;

    frm.set_value(
      "base_paid_amount",
      flt(frm.doc.paid_amount) * flt(frm.doc.source_exchange_rate)
    );

    let company_currency = frappe.get_doc(
      ":Company",
      frm.doc.company
    )?.default_currency;

    if (
      frm.doc.paid_from_account_currency === frm.doc.paid_to_account_currency
    ) {
      frm.set_value("received_amount", frm.doc.paid_amount);
      frm.set_value("base_received_amount", frm.doc.base_paid_amount);
    } else {
      frm.set_value(
        "received_amount",
        flt(frm.doc.paid_amount) *
          (flt(frm.doc.source_exchange_rate) /
            flt(frm.doc.target_exchange_rate))
      );
      frm.set_value(
        "base_received_amount",
        flt(frm.doc.received_amount) * flt(frm.doc.target_exchange_rate)
      );
    }

    frm.trigger("calculate_totals");
  },

  calculate_totals: function (frm) {
    let total_allocated_amount = 0;
    let base_total_allocated_amount = 0;

    (frm.doc.references || []).forEach(function (d) {
      total_allocated_amount += flt(d.allocated_amount);
      base_total_allocated_amount +=
        flt(d.allocated_amount) * flt(d.exchange_rate || 1);
    });

    frm.set_value("total_allocated_amount", total_allocated_amount);
    frm.set_value("base_total_allocated_amount", base_total_allocated_amount);

    let unallocated_amount = flt(frm.doc.paid_amount) - total_allocated_amount;
    frm.set_value(
      "unallocated_amount",
      unallocated_amount < 0 ? 0 : unallocated_amount
    );
  },
});

// For Payment Entry Reference Child Table
frappe.ui.form.on("Payment Entry Reference", {
  allocated_amount: function (frm, cdt, cdn) {
    frm.trigger("calculate_totals");
  },
  exchange_rate: function (frm, cdt, cdn) {
    frm.trigger("calculate_totals");
  },
});
