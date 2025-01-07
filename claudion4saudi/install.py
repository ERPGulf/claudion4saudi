import frappe

def set_default_theme():
    """Set Peach Grey as the default theme for all users."""
    default_theme = "Peach_grey"

    frappe.db.sql("""
        UPDATE `tabUser`
        SET desk_theme = %s
        WHERE name NOT IN ('Guest', 'Administrator')
    """, (default_theme,))

    frappe.db.set_single_value("System Settings", "desk_theme", default_theme)
    frappe.db.commit()



def validate_theme_availability():
    themes = ["light", "dark", "automatic", "blue", "red", "peach_grey", "purple"]
    desk_theme = frappe.db.get_single_value("System Settings", "desk_theme")
    if desk_theme not in themes:
        frappe.db.set_single_value("System Settings", "desk_theme", "Peach_grey")
