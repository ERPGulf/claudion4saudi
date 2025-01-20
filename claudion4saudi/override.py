# import frappe

# @frappe.whitelist()
# def switch_theme(theme):
#     if theme in ["Dark", "Light", "Automatic", "Blue", "Red", "Peach_grey", "Purple"]:
#         frappe.db.set_value("User", frappe.session.user, "desk_theme", theme)


import frappe

@frappe.whitelist()
def switch_theme(theme):
    valid_themes = ["light", "dark", "automatic", "blue", "red", "peach_grey", "purple"]
    if theme in valid_themes:
        frappe.db.set_value("User", frappe.session.user, "desk_theme", theme)
