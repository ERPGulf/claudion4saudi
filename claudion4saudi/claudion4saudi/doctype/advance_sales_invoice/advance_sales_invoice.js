frappe.ui.form.on("Advance Sales Invoice", {
  refresh(frm) {
    console.log("Advance Sales Invoice JS Loaded");

    if (frm.doc.references && frm.doc.references.length > 0) {
      frm.trigger("calculate_totals");
    }
  },

  onload_post_render(frm) {
    if (frm.fields_dict.references && frm.doc.references.length > 0) {
      frappe.model.sync(frm.doc);
      frm.fields_dict.references.grid.refresh();
      frm.refresh_field("references");
    }
  },
  refresh: function (frm) {
    frm.events.hide_unhide_fields(frm);
  },
  hide_unhide_fields: function (frm) {
    var company_currency = frm.doc.company
      ? frappe.get_doc(":Company", frm.doc.company)?.default_currency
      : "";

    frm.toggle_display(
      "source_exchange_rate",
      frm.doc.paid_amount &&
        frm.doc.paid_from_account_currency != company_currency
    );

    frm.toggle_display(
      "target_exchange_rate",
      frm.doc.received_amount &&
        frm.doc.paid_to_account_currency != company_currency &&
        frm.doc.paid_from_account_currency != frm.doc.paid_to_account_currency
    );

    frm.toggle_display(
      "base_paid_amount",
      frm.doc.paid_from_account_currency != company_currency
    );

    if (frm.doc.payment_type == "Pay") {
      frm.toggle_display(
        "base_total_taxes_and_charges",
        frm.doc.total_taxes_and_charges &&
          frm.doc.paid_to_account_currency != company_currency
      );
    } else {
      frm.toggle_display(
        "base_total_taxes_and_charges",
        frm.doc.total_taxes_and_charges &&
          frm.doc.paid_from_account_currency != company_currency
      );
    }

    frm.toggle_display(
      "base_received_amount",
      frm.doc.paid_to_account_currency != company_currency &&
        frm.doc.paid_from_account_currency !=
          frm.doc.paid_to_account_currency &&
        frm.doc.base_paid_amount != frm.doc.base_received_amount
    );

    frm.toggle_display(
      "received_amount",
      frm.doc.payment_type == "Internal Transfer" ||
        frm.doc.paid_from_account_currency != frm.doc.paid_to_account_currency
    );

    frm.toggle_display(
      ["base_total_allocated_amount"],
      frm.doc.paid_amount &&
        frm.doc.received_amount &&
        frm.doc.base_total_allocated_amount &&
        ((frm.doc.payment_type == "Receive" &&
          frm.doc.paid_from_account_currency != company_currency) ||
          (frm.doc.payment_type == "Pay" &&
            frm.doc.paid_to_account_currency != company_currency))
    );

    var party_amount =
      frm.doc.payment_type == "Receive"
        ? frm.doc.paid_amount
        : frm.doc.received_amount;

    frm.toggle_display(
      "write_off_difference_amount",
      frm.doc.difference_amount &&
        frm.doc.party &&
        frm.doc.total_allocated_amount > party_amount
    );
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

    frm.events.reallocate_amounts(frm);
  },

  reallocate_amounts: function (frm) {
    if (!frm.doc.references || frm.doc.references.length === 0) return;

    let total_outstanding = frappe.utils.sum(
      (frm.doc.references || []).map((d) => flt(d.outstanding_amount))
    );

    if (total_outstanding === 0) return;

    let new_paid_amount = flt(frm.doc.paid_amount);
    let total_allocated = frappe.utils.sum(
      (frm.doc.references || []).map((d) => flt(d.allocated_amount))
    );

    let allocation_ratio = new_paid_amount / total_allocated;

    (frm.doc.references || []).forEach(function (d) {
      let new_allocated_amount = flt(d.allocated_amount) * allocation_ratio;

      d.allocated_amount = Math.min(new_allocated_amount, d.outstanding_amount);
    });

    frm.refresh_field("references");
    frm.events.calculate_totals(frm);
  },

  calculate_totals: function (frm) {
    let total_allocated_amount = 0;
    let base_total_allocated_amount = 0;
    let exchange_rate =
      frm.doc.payment_type == "Receive"
        ? frm.doc.source_exchange_rate
        : frm.doc.target_exchange_rate;

    (frm.doc.references || []).forEach(function (d) {
      if (d.allocated_amount) {
        total_allocated_amount += flt(d.allocated_amount);
        base_total_allocated_amount +=
          flt(d.allocated_amount) * flt(exchange_rate);
      }
    });

    frm.set_value("total_allocated_amount", total_allocated_amount);
    frm.set_value("base_total_allocated_amount", base_total_allocated_amount);

    frm.events.set_unallocated_amount(frm);
  },
  unallocated_amount: function (frm) {
    let base_paid_amount = flt(frm.doc.base_paid_amount || 0);
    let base_total_allocated_amount = flt(
      frm.doc.base_total_allocated_amount || 0
    );
    let base_unallocated_amount =
      flt(frm.doc.unallocated_amount || 0) *
      (frm.doc.payment_type == "Receive"
        ? frm.doc.source_exchange_rate
        : frm.doc.target_exchange_rate);

    let difference_amount =
      base_paid_amount -
      (base_total_allocated_amount + base_unallocated_amount);

    if (difference_amount) {
      frappe.call({
        method: "claudion4saudi.advance_sales_invoice_.get_company_defaults",
        args: {
          company: frm.doc.company,
        },
        callback: function (r) {
          if (r.message) {
            let { write_off_account, cost_center } = r.message;

            let deduction_row = (frm.doc.deductions || []).find(
              (row) => row.account == write_off_account
            );

            if (!deduction_row) {
              deduction_row = frm.add_child("deductions");
              deduction_row.account = write_off_account;
              deduction_row.cost_center = cost_center;
            }

            deduction_row.amount = difference_amount;

            console.log("Deductions Table Updated:", frm.doc.deductions);
            frm.refresh_field("deductions");
          } else {
            frappe.msgprint(__("Failed to fetch company defaults."));
          }
        },
      });
    }
  },

  set_unallocated_amount: function (frm) {
    let unallocated_amount = 0;
    let deductions_to_consider = 0;
    let included_taxes = 0;

    (frm.doc.deductions || []).forEach((row) => {
      if (!row.is_exchange_gain_loss) {
        deductions_to_consider += flt(row.amount);
      }
    });

    if (frm.doc.party) {
      if (
        frm.doc.payment_type == "Receive" &&
        frm.doc.base_total_allocated_amount <
          frm.doc.base_paid_amount + deductions_to_consider
      ) {
        unallocated_amount =
          (frm.doc.base_paid_amount +
            deductions_to_consider -
            frm.doc.base_total_allocated_amount -
            included_taxes) /
          frm.doc.source_exchange_rate;
      } else if (
        frm.doc.payment_type == "Pay" &&
        frm.doc.base_total_allocated_amount <
          frm.doc.base_received_amount - deductions_to_consider
      ) {
        unallocated_amount =
          (frm.doc.base_received_amount -
            deductions_to_consider -
            frm.doc.base_total_allocated_amount -
            included_taxes) /
          frm.doc.target_exchange_rate;
      }
    }

    frm.set_value("unallocated_amount", unallocated_amount);
    frm.trigger("set_difference_amount");
  },

  set_difference_amount: function (frm) {
    let difference_amount = 0;
    let base_unallocated_amount =
      flt(frm.doc.unallocated_amount) *
      (frm.doc.payment_type == "Receive"
        ? frm.doc.source_exchange_rate
        : frm.doc.target_exchange_rate);
    let base_party_amount =
      flt(frm.doc.base_total_allocated_amount) + base_unallocated_amount;

    if (frm.doc.payment_type == "Receive") {
      difference_amount = base_party_amount - flt(frm.doc.base_received_amount);
    } else if (frm.doc.payment_type == "Pay") {
      difference_amount = flt(frm.doc.base_paid_amount) - base_party_amount;
    } else {
      difference_amount =
        flt(frm.doc.base_paid_amount) - flt(frm.doc.base_received_amount);
    }

    let total_deductions = frappe.utils.sum(
      (frm.doc.deductions || []).map((d) => flt(d.amount))
    );

    frm.set_value("difference_amount", difference_amount - total_deductions);
  },

  allocate_party_amount_against_ref_docs: async function (
    frm,
    paid_amount,
    paid_amount_change
  ) {
    await frm.call("allocate_amount_to_references", {
      paid_amount: paid_amount,
      paid_amount_change: paid_amount_change,
      allocate_payment_amount: frappe.flags.allocate_payment_amount ?? false,
    });

    frm.events.calculate_totals(frm);
  },
});

frappe.ui.form.on("Payment Entry Reference", {
  allocated_amount: function (frm) {
    frm.events.calculate_totals(frm);
  },

  references_remove: function (frm) {
    frm.events.calculate_totals(frm);
  },
});

frappe.ui.form.on("Advance Sales Invoice", {
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
function get_company_defaults(company) {
  return frappe.call({
    method:
      "erpnext.accounts.doctype.payment_entry.payment_entry.get_company_defaults",
    args: {
      company: company,
    },
  });
}
console.log("ped");
frappe.ui.form.on("Payment Entry Deduction", {
  before_deductions_remove: function (doc, cdt, cdn) {
    console.log("before_deductions_remove");
    const row = frappe.get_doc(cdt, cdn);
    if (row.is_exchange_gain_loss && row.amount) {
      frappe.throw(__("Cannot delete Exchange Gain/Loss row"));
    }
  },

  amount: function (frm) {
    frm.events.set_unallocated_amount(frm);
  },

  deductions_remove: function (frm) {
    frm.events.set_unallocated_amount(frm);
  },
});

function set_default_party_type(frm) {
  if (frm.doc.party) return;

  let party_type;
  if (frm.doc.payment_type == "Receive") {
    party_type = "Customer";
  } else if (frm.doc.payment_type == "Pay") {
    party_type = "Supplier";
  }

  if (party_type) frm.set_value("party_type", party_type);
}

function get_included_taxes(frm) {
  let included_taxes = 0;
  for (const tax of frm.doc.taxes) {
    if (!tax.included_in_paid_amount) continue;

    if (tax.add_deduct_tax == "Add") {
      included_taxes += tax.base_tax_amount;
    } else {
      included_taxes -= tax.base_tax_amount;
    }
  }

  return included_taxes;
}

function prompt_for_missing_account(frm, account) {
  return new Promise((resolve) => {
    const dialog = frappe.prompt(
      {
        label: __(frappe.unscrub(account)),
        fieldname: account,
        fieldtype: "Link",
        options: "Account",
        get_query: () => ({
          filters: {
            company: frm.doc.company,
          },
        }),
      },
      (values) => resolve(values?.[account]),
      __("Please Specify Account")
    );
  });
}

function get_deduction_amount_precision() {
  return frappe.meta.get_field_precision(
    frappe.meta.get_field("Payment Entry Deduction", "amount")
  );
}
