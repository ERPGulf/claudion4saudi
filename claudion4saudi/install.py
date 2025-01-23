import frappe

def after_install():
    default_theme = frappe.db.get_value(
        "Property Setter", 
        {"property": "options", "doctype": "User", "field_name": "desk_theme"}, 
        "default_value"
    )
    
    # valid_themes = ["Purple", "Frappe Light", "Timeless Night", "Automatic", "Blue", "Red", "Peach Grey"]
    # if default_theme not in valid_themes:
    #     frappe.log_error(f"Invalid default theme '{default_theme}' specified in Property Setter.", "Installation Error")
    #     return

    users = frappe.get_all("User", filters={"enabled": 1, "user_type": "System User"})
    for user in users:
        frappe.db.set_value("User", user.name, "desk_theme", default_theme)

    frappe.db.commit()
    frappe.msgprint(f"Default theme set to '{default_theme}' for all users.")
