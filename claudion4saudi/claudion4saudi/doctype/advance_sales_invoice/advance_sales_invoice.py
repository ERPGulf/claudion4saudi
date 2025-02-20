# # Copyright (c) 2025, Claudion and contributors
# # For license information, please see license.txt

# import frappe
# from frappe.model.document import Document


# class AdvanceSalesInvoice(Document):
# 	# frappe.msgprint("python loads")
# 	pass

import frappe
from frappe.model.document import Document


class AdvanceSalesInvoice(Document):
    def on_submit(self):
        if self.paid_amount and self.references:
            self.allocate_amount_to_references(self.paid_amount)
    @frappe.whitelist()
    def allocate_amount_to_references(self, paid_amount, paid_amount_change=False, allocate_payment_amount=False):
        from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry

        if not self.references:
            self.references = []

        # Create a mock PaymentEntry document object
        pe = frappe.new_doc("Advance Sales Invoice")
        pe.paid_amount = paid_amount
        pe.paid_amount_change = paid_amount_change
        pe.allocate_payment_amount = allocate_payment_amount
        pe.references = self.references

        # Call the instance method
        pe.allocate_payment_amount_to_references()

        # Update this document's references after allocation
        self.references = pe.references
