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
