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

frappe.provide("erpnext.accounts.dimensions");

cur_frm.cscript.tax_table = "Advance Taxes and Charges";
erpnext.accounts.taxes.setup_tax_validations("Payment Entry");
erpnext.accounts.taxes.setup_tax_filters("Advance Taxes and Charges");

frappe.ui.form.on("Advance Sales Invoice", {
  onload: function (frm) {
    console.log("Advance Sales Invoice Loaded");

    frm.ignore_doctypes_on_cancel_all = [
      "Sales Invoice",
      "Purchase Invoice",
      "Journal Entry",
      "Repost Payment Ledger",
      "Repost Accounting Ledger",
      "Unreconcile Payment",
      "Unreconcile Payment Entries",
      "Bank Transaction",
    ];

    if (frm.doc.__islocal) {
      if (!frm.doc.paid_from) frm.set_value("paid_from_account_currency", null);
      if (!frm.doc.paid_to) frm.set_value("paid_to_account_currency", null);
    }

    erpnext.accounts.dimensions.setup_dimension_filters(frm, frm.doctype);

    frm.set_query("project", function (doc) {
      let filters = { company: doc.company };
      if (doc.party_type === "Customer") filters.customer = doc.party;
      return {
        query: "erpnext.controllers.queries.get_project_name",
        filters,
      };
    });

    if (frm.doc.reference_no) {
      frm.events.get_sales_order_references(frm);
    }

    if (frm.is_new()) {
      set_default_party_type(frm);
    }
  },

  refresh: function (frm) {
    console.log("Advance Sales Invoice JS Loaded");

    if (frm.doc.references && frm.doc.references.length > 0) {
      frm.trigger("calculate_totals");
    }

    // Add buttons for fetching outstanding invoices/orders
    frm.add_custom_button(
      __("Get Outstanding Invoices"),
      function () {
        frm.events.get_outstanding_documents(frm, true, false);
      },
      __("Actions")
    );

    frm.add_custom_button(
      __("Get Outstanding Orders"),
      function () {
        frm.events.get_outstanding_documents(frm, false, true);
      },
      __("Actions")
    );
  },

  reference_no: function (frm) {
    if (frm.doc.reference_no) {
      frm.events.get_sales_order_references(frm);
    }
  },

  get_sales_order_references: function (frm) {
    frappe.call({
      method:
        "claudion4saudi.advance_sales_invoice_.get_advance_sales_invoice_entry",
      args: { sales_order: frm.doc.reference_no },
      callback: function (r) {
        if (r.message) {
          let data = r.message;
          frm.clear_table("references");

          (data.references || []).forEach((ref) => {
            let row = frm.add_child("references");
            Object.assign(row, ref);
          });

          frm.refresh_field("references");
        }
      },
    });
  },

  paid_amount: function (frm) {
    if (!frm.doc.paid_amount) return;

    frm.set_value(
      "base_paid_amount",
      flt(frm.doc.paid_amount) * flt(frm.doc.source_exchange_rate)
    );

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

    (frm.doc.references || []).forEach((d) => {
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

  get_outstanding_documents: function (frm, get_invoices, get_orders) {
    frappe.call({
      method:
        "erpnext.accounts.doctype.payment_entry.payment_entry.get_outstanding_reference_documents",
      args: {
        posting_date: frm.doc.posting_date,
        company: frm.doc.company,
        party_type: frm.doc.party_type,
        party: frm.doc.party,
        get_outstanding_invoices: get_invoices,
        get_orders_to_be_billed: get_orders,
      },
      callback: function (r) {
        if (r.message) {
          frm.clear_table("references");
          r.message.forEach((d) => {
            let row = frm.add_child("references");
            row.reference_doctype = d.voucher_type;
            row.reference_name = d.voucher_no;
            row.total_amount = d.invoice_amount;
            row.outstanding_amount = d.outstanding_amount;
            row.allocated_amount = d.outstanding_amount;
          });
          frm.refresh_field("references");
          frm.trigger("calculate_totals");
        }
      },
    });
  },

  sales_taxes_and_charges_template: function (frm) {
    frm.trigger("fetch_taxes_from_template");
  },

  fetch_taxes_from_template: function (frm) {
    if (!frm.doc.sales_taxes_and_charges_template) return;

    frappe.call({
      method: "erpnext.controllers.accounts_controller.get_taxes_and_charges",
      args: {
        master_doctype: "Sales Taxes and Charges Template",
        master_name: frm.doc.sales_taxes_and_charges_template,
      },
      callback: function (r) {
        if (!r.exc && r.message) {
          frm.clear_table("taxes");
          r.message.forEach((tax) => frm.add_child("taxes", tax));
          frm.refresh_field("taxes");
        }
      },
    });
  },
});

// Handle deductions and taxes
frappe.ui.form.on("Advance Taxes and Charges", {
  rate: function (frm) {
    frm.trigger("apply_taxes");
  },

  tax_amount: function (frm) {
    frm.trigger("apply_taxes");
  },

  charge_type: function (frm) {
    frm.trigger("apply_taxes");
  },

  included_in_paid_amount: function (frm) {
    frm.trigger("apply_taxes");
  },

  taxes_remove: function (frm) {
    frm.trigger("apply_taxes");
  },
});

frappe.ui.form.on("Payment Entry Deduction", {
  amount: function (frm) {
    frm.trigger("set_unallocated_amount");
  },

  deductions_remove: function (frm) {
    frm.trigger("set_unallocated_amount");
  },
});

// Handle allocation for references
frappe.ui.form.on("Payment Entry Reference", {
  reference_doctype: function (frm, cdt, cdn) {
    let row = frappe.get_doc(cdt, cdn);
    frm.events.validate_reference_document(frm, row);
  },

  allocated_amount: function (frm) {
    frm.trigger("calculate_totals");
  },

  references_remove: function (frm) {
    frm.trigger("calculate_totals");
  },
});

// Utility functions
function set_default_party_type(frm) {
  if (frm.doc.party) return;
  let party_type = frm.doc.payment_type === "Receive" ? "Customer" : "Supplier";
  frm.set_value("party_type", party_type);
}
