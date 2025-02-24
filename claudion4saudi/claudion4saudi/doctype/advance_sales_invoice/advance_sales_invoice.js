// frappe.ui.form.on("Advance Sales Invoice", {
//   refresh(frm) {
//     console.log("Advance Sales Invoice JS Loaded");

//     if (frm.doc.references && frm.doc.references.length > 0) {
//       frm.trigger("calculate_totals");
//     }
//   },

//   paid_amount: function (frm) {
//     if (!frm.doc.paid_amount) return;

//     frm.set_value(
//       "base_paid_amount",
//       flt(frm.doc.paid_amount) * flt(frm.doc.source_exchange_rate)
//     );

//     let company_currency = frappe.get_doc(
//       ":Company",
//       frm.doc.company
//     )?.default_currency;

//     if (
//       frm.doc.paid_from_account_currency === frm.doc.paid_to_account_currency
//     ) {
//       frm.set_value("received_amount", frm.doc.paid_amount);
//       frm.set_value("base_received_amount", frm.doc.base_paid_amount);
//     } else {
//       frm.set_value(
//         "received_amount",
//         flt(frm.doc.paid_amount) *
//           (flt(frm.doc.source_exchange_rate) /
//             flt(frm.doc.target_exchange_rate))
//       );
//       frm.set_value(
//         "base_received_amount",
//         flt(frm.doc.received_amount) * flt(frm.doc.target_exchange_rate)
//       );
//     }

//     frm.trigger("calculate_totals");
//   },

//   calculate_totals: function (frm) {
//     let total_allocated_amount = 0;
//     let base_total_allocated_amount = 0;

//     (frm.doc.references || []).forEach(function (d) {
//       total_allocated_amount += flt(d.allocated_amount);
//       base_total_allocated_amount +=
//         flt(d.allocated_amount) * flt(d.exchange_rate || 1);
//     });

//     frm.set_value("total_allocated_amount", total_allocated_amount);
//     frm.set_value("base_total_allocated_amount", base_total_allocated_amount);

//     let unallocated_amount = flt(frm.doc.paid_amount) - total_allocated_amount;
//     frm.set_value(
//       "unallocated_amount",
//       unallocated_amount < 0 ? 0 : unallocated_amount
//     );
//   },
// });

// // For Payment Entry Reference Child Table
// frappe.ui.form.on("Payment Entry Reference", {
//   allocated_amount: function (frm, cdt, cdn) {
//     frm.trigger("calculate_totals");
//   },
//   exchange_rate: function (frm, cdt, cdn) {
//     frm.trigger("calculate_totals");
//   },
// });

frappe.ui.form.on("Advance Sales Invoice", {
  refresh(frm) {
    console.log("Advance Sales Invoice JS Loaded");

    if (frm.doc.references && frm.doc.references.length > 0) {
      frm.trigger("calculate_totals");
    }
  },

  paid_amount(frm) {
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

  calculate_totals(frm) {
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

  get_outstanding_invoices_or_orders(
    frm,
    get_outstanding_invoices,
    get_orders_to_be_billed
  ) {
    const today = frappe.datetime.get_today();
    let fields = [
      { fieldtype: "Section Break", label: __("Posting Date") },
      {
        fieldtype: "Date",
        label: __("From Date"),
        fieldname: "from_posting_date",
        default: frappe.datetime.add_days(today, -30),
      },
      { fieldtype: "Column Break" },
      {
        fieldtype: "Date",
        label: __("To Date"),
        fieldname: "to_posting_date",
        default: today,
      },
      { fieldtype: "Section Break", label: __("Due Date") },
      { fieldtype: "Date", label: __("From Date"), fieldname: "from_due_date" },
      { fieldtype: "Column Break" },
      { fieldtype: "Date", label: __("To Date"), fieldname: "to_due_date" },
      { fieldtype: "Section Break", label: __("Outstanding Amount") },
      {
        fieldtype: "Float",
        label: __("Greater Than Amount"),
        fieldname: "outstanding_amt_greater_than",
        default: 0,
      },
      { fieldtype: "Column Break" },
      {
        fieldtype: "Float",
        label: __("Less Than Amount"),
        fieldname: "outstanding_amt_less_than",
      },
    ];

    if (frm.dimension_filters) {
      let column_break_insertion_point = Math.ceil(
        frm.dimension_filters.length / 2
      );
      fields.push({ fieldtype: "Section Break" });

      frm.dimension_filters.map((elem, idx) => {
        fields.push({
          fieldtype: "Link",
          label:
            elem.document_type == "Cost Center" ? "Cost Center" : elem.label,
          options: elem.document_type,
          fieldname: elem.fieldname || elem.document_type,
        });
        if (idx + 1 == column_break_insertion_point) {
          fields.push({ fieldtype: "Column Break" });
        }
      });
    }

    fields = fields.concat([
      { fieldtype: "Section Break" },
      {
        fieldtype: "Check",
        label: __("Allocate Payment Amount"),
        fieldname: "allocate_payment_amount",
        default: 1,
      },
    ]);

    let btn_text = get_outstanding_invoices
      ? "Get Outstanding Invoices"
      : "Get Outstanding Orders";

    frappe.prompt(
      fields,
      function (filters) {
        frappe.flags.allocate_payment_amount = true;
        frm.events.validate_filters_data(frm, filters);
        frm.doc.cost_center = filters.cost_center;
        frm.events.get_outstanding_documents(
          frm,
          filters,
          get_outstanding_invoices,
          get_orders_to_be_billed
        );
      },
      __("Filters"),
      __(btn_text)
    );
  },

  get_outstanding_invoices(frm) {
    frm.events.get_outstanding_invoices_or_orders(frm, true, false);
  },

  get_outstanding_orders(frm) {
    frm.events.get_outstanding_invoices_or_orders(frm, false, true);
  },

  validate_filters_data(frm, filters) {
    const fields = {
      "Posting Date": ["from_posting_date", "to_posting_date"],
      "Due Date": ["from_due_date", "to_due_date"],
      "Advance Amount": [
        "outstanding_amt_greater_than",
        "outstanding_amt_less_than",
      ],
    };

    for (let key in fields) {
      let from_field = fields[key][0];
      let to_field = fields[key][1];

      if (filters[from_field] && !filters[to_field]) {
        frappe.throw(
          __("Error: {0} is mandatory field", [to_field.replace(/_/g, " ")])
        );
      } else if (
        filters[from_field] &&
        filters[from_field] > filters[to_field]
      ) {
        frappe.throw(
          __("{0}: {1} must be less than {2}", [
            key,
            from_field.replace(/_/g, " "),
            to_field.replace(/_/g, " "),
          ])
        );
      }
    }
  },
});

// For Payment Entry Reference Child Table
frappe.ui.form.on("Payment Entry Reference", {
  allocated_amount(frm, cdt, cdn) {
    frm.trigger("calculate_totals");
  },
  exchange_rate(frm, cdt, cdn) {
    frm.trigger("calculate_totals");
  },
});
