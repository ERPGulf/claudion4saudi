# import frappe

# def apply_theme(doc, method):
#     """Apply the theme when desk_theme is updated."""
#     frappe.msgprint("msg frm user theme")
#     if frappe.session.user == doc.name:  # Ensure the logged-in user is the one changing the theme
#         frappe.db.set_value("User", doc.name, "desk_theme", doc.desk_theme)
#         frappe.db.commit()
#         frappe.response["message"] = "Theme updated. Reloading..."
#         frappe.response["reload"] = True  # This triggers a reload in the UI

