frappe.ui.form.on("Item", {
  refresh: function (Frm) {},
  onload: function (frm) {
    console.log("testing from item js");
    if (frappe.session.user != "Administrator" && frm.is_new()) {
      frappe.call({
        method:
          "claudion4saudi.claudion4saudi.custom.py.item.user_permission_checking",
        args: {
          user: frappe.session.user,
        },
        callback: function (r) {
          if (r.message) {
            const company = r.message[0];
            const item_tax_templates = r.message[1];
            frm.set_value("item_defaults", [
              {
                company: company,
              },
            ]);
            frm.clear_table("taxes");
            if (item_tax_templates.length > 0) {
              item_tax_templates.forEach((template) => {
                const row = frm.add_child("taxes");
                row.item_tax_template = template.name;
                row.tax_category = template.custom_tax_category;
              });
              frm.refresh_field("taxes");
            }
          }
        },
      });
    }
  },
  custom_company: function (frm) {
    frappe.call({
      method: "claudion4saudi.claudion4saudi.custom.py.item.itemtax_template",
      args: {
        company: frm.doc.custom_company,
      },
      callback: function (r) {
        if (r.message) {
          const item_tax_templates = r.message;
          frm.set_value("item_defaults", [
            {
              company: frm.doc.custom_company,
            },
          ]);
          frm.clear_table("taxes");
          if (item_tax_templates.length > 0) {
            item_tax_templates.forEach((template) => {
              const row = frm.add_child("taxes");
              row.item_tax_template = template.name;
              row.tax_category = template.custom_tax_category;
            });
            frm.refresh_field("taxes");
          }
        }
      },
    });
  },
});
