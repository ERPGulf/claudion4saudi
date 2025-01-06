import frappe


@frappe.whitelist()
def user_permission_checking(user):
    if user:
        user_permission = frappe.db.get_all("User Permission", filters={"user":user, "allow":"Company"}, fields=["for_value"])
        if len(user_permission) == 1:
            company = user_permission[0]["for_value"]
            item_tax_template = frappe.db.get_all(
                    "Item Tax Template", 
                    filters={"company": company}, 
                    fields=["name", "custom_tax_category", "custom_order_type"]
                )
            tax_template_by_order_type = {}
            for tax in item_tax_template:
                if tax["custom_order_type"] is not None:
                    order_type = int(tax["custom_order_type"])
                    if order_type not in tax_template_by_order_type:
                        tax_template_by_order_type[order_type] = []
                    tax_template_by_order_type[order_type].append(tax)
            sorted_tax_template_list = []
            for order_type in sorted(tax_template_by_order_type):
                sorted_tax_template_list.extend(tax_template_by_order_type[order_type])
            return company, sorted_tax_template_list

@frappe.whitelist()
def itemtax_template(company):
    if company:
        item_tax_template = frappe.db.get_all(
            "Item Tax Template", 
            filters={"company": company}, 
            fields=["name", "custom_tax_category", "custom_order_type"]
        )
        tax_template_by_order_type = {}
        for tax in item_tax_template:
            if tax["custom_order_type"] is not None:
                order_type = int(tax["custom_order_type"])
                if order_type not in tax_template_by_order_type:
                    tax_template_by_order_type[order_type] = []
                tax_template_by_order_type[order_type].append(tax)
        sorted_tax_template_list = []
        for order_type in sorted(tax_template_by_order_type):
            sorted_tax_template_list.extend(tax_template_by_order_type[order_type])
        frappe.errprint(sorted_tax_template_list)
        return sorted_tax_template_list


