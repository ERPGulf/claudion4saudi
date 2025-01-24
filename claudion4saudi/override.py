@frappe.whitelist()
def switch_theme(theme):
    theme_mapping = {
        "Light": "Frappe Light",
        "Dark": "Timeless Night",
        "Automatic": "Automatic",
        "Blue": "Blue",
        "Red": "Red",
        "Peach_Grey": "Peach Grey",
        "Purple": "Purple"
    }

    if theme in theme_mapping:
        theme_option = theme_mapping[theme]
        frappe.db.set_value("User", frappe.session.user, "desk_theme", theme_option)
        return f"Theme set to {theme_option}"
    else:
        frappe.throw("Invalid theme selected")