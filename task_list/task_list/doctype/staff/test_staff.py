# Copyright (c) 2026, Deepak Patel and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase


class IntegrationTestStaff(IntegrationTestCase):
	def test_full_name_is_derived_from_first_and_last_name(self):
		staff = frappe.get_doc(
			{
				"doctype": "Staff",
				"first_name": "Ada",
				"last_name": "Lovelace",
				"full_name": "Incorrect Value",
			}
		).insert()

		self.assertEqual(staff.full_name, "Ada Lovelace")

	def test_full_name_is_read_only(self):
		meta = frappe.get_meta("Staff")

		self.assertTrue(meta.get_field("full_name").read_only)
