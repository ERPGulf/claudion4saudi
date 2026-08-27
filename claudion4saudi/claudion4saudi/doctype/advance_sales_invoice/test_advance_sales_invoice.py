# Copyright (c) 2025, Claudion and Contributors
# See license.txt

import frappe

# These are unit tests over metadata - they need no documents, so they use a base
# that does not build test-record dependencies. IntegrationTestCase would call
# make_test_records() for every linked DocType, which drags in ERPNext's standard
# Supplier fixtures; those omit custom_company, which this app makes mandatory, so
# the suite errors out before any assertion runs. v15 has no UnitTestCase, but its
# FrappeTestCase creates no test records either, so behaviour matches on both.
try:  # frappe v16
	from frappe.tests import UnitTestCase as ClaudionTestCase
except ImportError:  # frappe v15
	from frappe.tests.utils import FrappeTestCase as ClaudionTestCase

# Custom fields this app's fixtures must put on Advance Sales Invoice. If the
# fixture fails to sync, these disappear from meta and the test fails.
# These tests assert on metadata only and create no documents, so they need no
# test-record fixtures. Declaring every first-level dependency here stops the
# runner walking the link graph -- that walk reaches ERPNext's standard Supplier
# records, which omit custom_company (made mandatory by this app's fixtures) and
# abort the whole suite with MandatoryError before any assertion runs.
# IGNORE_TEST_RECORD_DEPENDENCIES is the v16 name; test_ignore is the v15 name.
IGNORE_TEST_RECORD_DEPENDENCIES = [
	"Account",
	"Advance Sales Invoice",
	"Auto Repeat",
	"Bank Account",
	"Company",
	"Contact",
	"Cost Center",
	"Currency",
	"DocType",
	"Item",
	"Item Tax Template",
	"Letter Head",
	"Mode of Payment",
	"Payment Order",
	"Payment Request",
	"Payment Term",
	"Print Heading",
	"Project",
	"Purchase Taxes and Charges Template",
	"Sales Taxes and Charges Template",
	"Tax Withholding Category",
	"UOM",
]
test_ignore = IGNORE_TEST_RECORD_DEPENDENCIES

EXPECTED_CUSTOM_FIELDS = (
	"custom_uuid",
	"custom_zatca_status",
	"custom_zatca_tax_category",
	"custom_ksa_einvoicing_xml",
	"custom_zatca_full_response",
)


class TestAdvanceSalesInvoice(ClaudionTestCase):
	def test_doctype_and_custom_fields_present(self):
		self.assertTrue(
			frappe.db.exists("DocType", "Advance Sales Invoice"),
			"Advance Sales Invoice DocType is missing",
		)

		meta = frappe.get_meta("Advance Sales Invoice")
		self.assertGreater(len(meta.fields), 0, "Advance Sales Invoice meta has no fields")

		fieldnames = {f.fieldname for f in meta.fields}
		missing = [f for f in EXPECTED_CUSTOM_FIELDS if f not in fieldnames]
		self.assertEqual(
			missing, [], f"custom fields missing from Advance Sales Invoice meta: {missing}"
		)
