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

# These tests assert on metadata only and create no documents, so they need no
# test-record fixtures. Declaring every first-level dependency here stops the
# runner walking the link graph -- that walk reaches ERPNext's standard Supplier
# records, which omit custom_company (made mandatory by this app's fixtures) and
# abort the whole suite with MandatoryError before any assertion runs.
# IGNORE_TEST_RECORD_DEPENDENCIES is the v16 name; test_ignore is the v15 name.
IGNORE_TEST_RECORD_DEPENDENCIES = [
	"Item",
	"UOM",
]
test_ignore = IGNORE_TEST_RECORD_DEPENDENCIES

EXPECTED_FIELDS = ("item_code", "qty", "rate", "amount")


class TestAdvanceSalesInvoiceItem(ClaudionTestCase):
	def test_doctype_and_fields_present(self):
		self.assertTrue(
			frappe.db.exists("DocType", "Advance Sales Invoice Item"),
			"Advance Sales Invoice Item DocType is missing",
		)

		meta = frappe.get_meta("Advance Sales Invoice Item")
		self.assertGreater(len(meta.fields), 0, "meta has no fields")
		self.assertTrue(meta.istable, "Advance Sales Invoice Item should be a child table")

		fieldnames = {f.fieldname for f in meta.fields}
		missing = [f for f in EXPECTED_FIELDS if f not in fieldnames]
		self.assertEqual(missing, [], f"fields missing from meta: {missing}")
