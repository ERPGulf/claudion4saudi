
import frappe

@frappe.whitelist()
def switch_theme(theme):
    valid_themes = ["Dark", "Light", "Automatic", "Blue", "Red", "Peach_grey", "Purple"]
    default_theme = "Peach_grey"  # Set peach_grey as the default theme
    if theme in valid_themes:
        frappe.db.set_value("User", frappe.session.user, "desk_theme", theme)
    else:
        frappe.db.set_value("User", frappe.session.user, "desk_theme", default_theme)
