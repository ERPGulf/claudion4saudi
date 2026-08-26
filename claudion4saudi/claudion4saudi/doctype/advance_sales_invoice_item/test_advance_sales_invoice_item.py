# Copyright (c) 2025, Claudion and Contributors
# See license.txt

# import frappe
try:  # frappe v16
	from frappe.tests import IntegrationTestCase
except ImportError:  # frappe v15 - IntegrationTestCase does not exist there
	from frappe.tests.utils import FrappeTestCase as IntegrationTestCase


class TestAdvanceSalesInvoiceItem(IntegrationTestCase):
	pass
