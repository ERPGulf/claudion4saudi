import frappe

def set_default_theme():
    """Set Peach Grey as the default theme for all users."""
    default_theme = "peach_grey"

    # Update the default theme for all existing users
    frappe.db.sql("""
        UPDATE `tabUser`
        SET desk_theme = %s
        WHERE name NOT IN ('Guest', 'Administrator')
    """, (default_theme,))

    # Set Peach Grey as the default for new users
    frappe.db.set_single_value("System Settings", "desk_theme", default_theme)
    frappe.db.commit()
