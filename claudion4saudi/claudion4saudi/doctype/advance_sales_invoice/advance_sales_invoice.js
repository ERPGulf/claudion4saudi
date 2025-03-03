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

//   get_outstanding_invoices_or_orders: function (
//     frm,
//     get_outstanding_invoices,
//     get_orders_to_be_billed
//   ) {
//     const today = frappe.datetime.get_today();
//     let fields = [
//       { fieldtype: "Section Break", label: __("Posting Date") },
//       {
//         fieldtype: "Date",
//         label: __("From Date"),
//         fieldname: "from_posting_date",
//         default: frappe.datetime.add_days(today, -30),
//       },
//       { fieldtype: "Column Break" },
//       {
//         fieldtype: "Date",
//         label: __("To Date"),
//         fieldname: "to_posting_date",
//         default: today,
//       },
//       { fieldtype: "Section Break", label: __("Due Date") },
//       { fieldtype: "Date", label: __("From Date"), fieldname: "from_due_date" },
//       { fieldtype: "Column Break" },
//       { fieldtype: "Date", label: __("To Date"), fieldname: "to_due_date" },
//       { fieldtype: "Section Break", label: __("Outstanding Amount") },
//       {
//         fieldtype: "Float",
//         label: __("Greater Than Amount"),
//         fieldname: "outstanding_amt_greater_than",
//         default: 0,
//       },
//       { fieldtype: "Column Break" },
//       {
//         fieldtype: "Float",
//         label: __("Less Than Amount"),
//         fieldname: "outstanding_amt_less_than",
//       },
//     ];

//     fields.push({ fieldtype: "Section Break" });

//     fields = fields.concat([
//       { fieldtype: "Section Break" },
//       {
//         fieldtype: "Check",
//         label: __("Allocate Payment Amount"),
//         fieldname: "allocate_payment_amount",
//         default: 1,
//       },
//     ]);

//     let btn_text = get_outstanding_invoices
//       ? "Get Outstanding Invoices"
//       : "Get Outstanding Orders";

//     frappe.prompt(
//       fields,
//       function (filters) {
//         frappe.flags.allocate_payment_amount = true;
//         frm.events.validate_filters_data(frm, filters);
//         frm.doc.cost_center = filters.cost_center;
//         frm.events.get_outstanding_documents(
//           frm,
//           filters,
//           get_outstanding_invoices,
//           get_orders_to_be_billed
//         );
//       },
//       __("Filters"),
//       __(btn_text)
//     );
//   },

//   get_outstanding_invoices(frm) {
//     frm.events.get_outstanding_invoices_or_orders(frm, true, false);
//   },

//   get_outstanding_orders(frm) {
//     frm.events.get_outstanding_invoices_or_orders(frm, false, true);
//   },

//   validate_filters_data(frm, filters) {
//     const fields = {
//       "Posting Date": ["from_posting_date", "to_posting_date"],
//       "Due Date": ["from_due_date", "to_due_date"],
//       "Advance Amount": [
//         "outstanding_amt_greater_than",
//         "outstanding_amt_less_than",
//       ],
//     };

//     for (let key in fields) {
//       let from_field = fields[key][0];
//       let to_field = fields[key][1];

//       if (filters[from_field] && !filters[to_field]) {
//         frappe.throw(
//           __("Error: {0} is a mandatory field", [to_field.replace(/_/g, " ")])
//         );
//       } else if (
//         filters[from_field] &&
//         filters[from_field] > filters[to_field]
//       ) {
//         frappe.throw(
//           __("{0}: {1} must be less than {2}", [
//             key,
//             from_field.replace(/_/g, " "),
//             to_field.replace(/_/g, " "),
//           ])
//         );
//       }
//     }
//   },
//   set_exchange_gain_loss_deduction: async function (frm) {
//     // wait for allocate_party_amount_against_ref_docs to finish
//     await frappe.after_ajax();
//     const base_paid_amount = frm.doc.base_paid_amount || 0;
//     const base_received_amount = frm.doc.base_received_amount || 0;
//     const exchange_gain_loss = flt(
//       base_paid_amount - base_received_amount,
//       get_deduction_amount_precision()
//     );

//     if (!exchange_gain_loss) {
//       frm.events.delete_exchange_gain_loss(frm);
//       return;
//     }

//     const account_fieldname = "exchange_gain_loss_account";
//     let row = (frm.doc.deductions || []).find((t) => t.is_exchange_gain_loss);

//     if (!row) {
//       const response = await get_company_defaults(frm.doc.company);

//       const account =
//         response.message?.[account_fieldname] ||
//         (await prompt_for_missing_account(frm, account_fieldname));

//       row = frm.add_child("deductions");
//       row.account = account;
//       row.cost_center = response.message?.cost_center;
//       row.is_exchange_gain_loss = 1;
//     }

//     row.amount = exchange_gain_loss;
//     frm.refresh_field("deductions");
//     frm.events.set_unallocated_amount(frm);
//   },

//   delete_exchange_gain_loss: function (frm) {
//     const exchange_gain_loss_row = (frm.doc.deductions || []).find(
//       (row) => row.is_exchange_gain_loss
//     );

//     if (!exchange_gain_loss_row) return;

//     exchange_gain_loss_row.amount = 0;
//     frm
//       .get_field("deductions")
//       .grid.grid_rows[exchange_gain_loss_row.idx - 1].remove();
//     frm.refresh_field("deductions");
//   },

//   set_write_off_deduction: async function (frm) {
//     const difference_amount = flt(
//       frm.doc.difference_amount,
//       get_deduction_amount_precision()
//     );
//     if (!difference_amount) return;

//     const account_fieldname = "write_off_account";
//     const response = await get_company_defaults(frm.doc.company);
//     const write_off_account =
//       response.message?.[account_fieldname] ||
//       (await prompt_for_missing_account(frm, account_fieldname));

//     if (!write_off_account) return;

//     let row = (frm.doc["deductions"] || []).find(
//       (t) => t.account == write_off_account
//     );
//     if (!row) {
//       row = frm.add_child("deductions");
//       row.account = write_off_account;
//       row.cost_center = response.message?.cost_center;
//     }

//     row.amount = flt(row.amount) + difference_amount;
//     frm.refresh_field("deductions");
//     frm.events.set_unallocated_amount(frm);
//   },
// });

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

  get_outstanding_invoices_or_orders: function (
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

    fields.push({ fieldtype: "Section Break" });

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
          __("Error: {0} is a mandatory field", [to_field.replace(/_/g, " ")])
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
  set_exchange_gain_loss_deduction: async function (frm) {
    // wait for allocate_party_amount_against_ref_docs to finish
    await frappe.after_ajax();
    const base_paid_amount = frm.doc.base_paid_amount || 0;
    const base_received_amount = frm.doc.base_received_amount || 0;
    const exchange_gain_loss = flt(
      base_paid_amount - base_received_amount,
      get_deduction_amount_precision()
    );

    if (!exchange_gain_loss) {
      frm.events.delete_exchange_gain_loss(frm);
      return;
    }

    const account_fieldname = "exchange_gain_loss_account";
    let row = (frm.doc.deductions || []).find((t) => t.is_exchange_gain_loss);

    if (!row) {
      const response = await get_company_defaults(frm.doc.company);

      const account =
        response.message?.[account_fieldname] ||
        (await prompt_for_missing_account(frm, account_fieldname));

      row = frm.add_child("deductions");
      row.account = account;
      row.cost_center = response.message?.cost_center;
      row.is_exchange_gain_loss = 1;
    }

    row.amount = exchange_gain_loss;
    frm.refresh_field("deductions");
    frm.events.set_unallocated_amount(frm);
  },

  delete_exchange_gain_loss: function (frm) {
    const exchange_gain_loss_row = (frm.doc.deductions || []).find(
      (row) => row.is_exchange_gain_loss
    );

    if (!exchange_gain_loss_row) return;

    exchange_gain_loss_row.amount = 0;
    frm
      .get_field("deductions")
      .grid.grid_rows[exchange_gain_loss_row.idx - 1].remove();
    frm.refresh_field("deductions");
  },

  set_write_off_deduction: async function (frm) {
    const difference_amount = flt(
      frm.doc.difference_amount,
      get_deduction_amount_precision()
    );
    if (!difference_amount) return;

    const account_fieldname = "write_off_account";
    const response = await get_company_defaults(frm.doc.company);
    const write_off_account =
      response.message?.[account_fieldname] ||
      (await prompt_for_missing_account(frm, account_fieldname));

    if (!write_off_account) return;

    let row = (frm.doc["deductions"] || []).find(
      (t) => t.account == write_off_account
    );
    if (!row) {
      row = frm.add_child("deductions");
      row.account = write_off_account;
      row.cost_center = response.message?.cost_center;
    }

    row.amount = flt(row.amount) + difference_amount;
    frm.refresh_field("deductions");
    frm.events.set_unallocated_amount(frm);
  },
});
frappe.ui.form.on("Payment Entry Reference", {
  reference_name: function (frm, cdt, cdn) {
    let row = frappe.model.get_doc(cdt, cdn);

    if (!row || !row.reference_name) {
      console.error("Row does not exist or reference_name is missing", cdn);
      return;
    }

    frappe.call({
      method: "claudion4saudi.advance_sales_invoice_.get_reference_details_",
      args: {
        reference_doctype: "Sales Order",
        reference_name: row.reference_name,
        party_account_currency:
          frm.doc.payment_type === "Receive"
            ? frm.doc.paid_from_account_currency
            : frm.doc.paid_to_account_currency,
        party_type: frm.doc.party_type,
        party: frm.doc.party,
      },
      callback: function (r) {
        if (r.message) {
          console.log("Reference Data:", r.message);

          let updated_row = frappe.model.get_doc(cdt, cdn);
          if (!updated_row) {
            console.error(
              "Row was removed before the API call completed!",
              cdn
            );
            return;
          }

          frappe.model.set_value(
            cdt,
            cdn,
            "total_amount",
            r.message.total_amount || 0
          );
          frappe.model.set_value(
            cdt,
            cdn,
            "outstanding_amount",
            r.message.outstanding_amount || 0
          );
          frappe.model.set_value(
            cdt,
            cdn,
            "exchange_rate",
            r.message.exchange_rate || 1
          );
          frappe.model.set_value(cdt, cdn, "bill_no", r.message.bill_no || "");
          frappe.model.set_value(
            cdt,
            cdn,
            "due_date",
            r.message.due_date || ""
          );

          frm.refresh_field("references"); // Ensure UI updates correctly
        }
      },
      error: function (err) {
        console.error("Error fetching reference details:", err);
      },
    });
  },
});
