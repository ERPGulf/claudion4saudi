import frappe

@frappe.whitelist()
def switch_theme(theme):
    if theme in ["Dark", "Light", "Automatic", "Blue", "Red", "Peach_grey", "Purple"]:
        frappe.db.set_value("User", frappe.session.user, "desk_theme", theme)
        return "Theme set to " + theme



# import frappe


# @frappe.whitelist()
# def switch_theme(theme):
#     theme_option = ""
#     if theme == "Light":
#         theme_option = "Frappe Light"
#     if theme == "Dark":
#         theme_option = "Timeless Night"
#     if theme == "Automatic":
#         theme_option = "Automatic"
#     if theme == "Blue":
#         theme_option = "Blue"
#     if theme == "Red":
#         theme_option = "Red"
#     if theme == "Peach_grey":
#         theme_option = "Peach Grey"
#     if theme == "Purple":
#         theme_option = "Purple"

#     # frappe.throw("Theme: " + theme)
#     # valid_themes = ["light", "dark", "automatic", "blue", "red", "peach_grey", "purple"]
#     # if theme in valid_themes:
#     frappe.db.set_value("User", frappe.session.user, "desk_theme", theme_option)
#     return "Theme set to " + theme_option
