import frappe

def after_migrate():
    default_theme = frappe.db.get_value(
        "Property Setter", 
        {"property": "options", "doc_type": "User", "field_name": "desk_theme"}, 
        "default_value"
    )

    users = frappe.get_all("User", filters={"enabled": 1, "user_type": "System User"})
    for user in users:
        frappe.db.set_value("User", user.name, "desk_theme", default_theme)

    frappe.db.commit()
