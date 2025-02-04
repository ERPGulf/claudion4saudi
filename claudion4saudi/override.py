import frappe


@frappe.whitelist()
def switch_theme(theme):
    theme_mapping = {
        "Light": "Frappe Light",
        "Dark": "Timeless Night",
        "Automatic": "Automatic",
        "Blue": "Blue",
        "Red": "Red",
        "peachgrey": "Peach Grey",
        "Purple": "Purple",
        "Themei": "Theme I",
        "ClaudionTheme2": "Claudion Theme 2",
        "ClaudionTheme3": "Claudion Theme 3",
        "ClaudionTheme4": "Claudion Theme 4",
    }
    frappe.db.set_value("User", frappe.session.user, "desk_theme", theme)
    return "success"
    # if theme in theme_mapping:
    #     theme_option = theme_mapping[theme]
    #     # frappe.db.set_value("User", frappe.session.user, "desk_theme", "ClaudionTheme3")
    #     frappe.db.set_value("User", frappe.session.user, "desk_theme", theme_option)
    #     return f"Theme set to {theme_option}"
    # else:
    #     frappe.throw("Invalid theme selected")
