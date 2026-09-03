# Copyright (c) 2026, Deepak Patel and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase


# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]



class IntegrationTestTasklistObjective(IntegrationTestCase):
	"""
	Integration tests for TasklistObjective.
	Use this class for testing interactions between multiple components.
	"""

	def test_task_rows_require_all_fields_and_default_status(self):
		staff = frappe.get_doc(
			{
				"doctype": "Staff",
				"first_name": "Quality",
				"last_name": "Manager",
			}
		).insert()

		objective = frappe.get_doc(
			{
				"doctype": "Tasklist Objective",
				"objective": "Objective with task rows",
				"team": "Operations",
				"department": "Quality",
				"tasks": [
					{
						"task": "Review process",
						"type": "Preventive",
						"person_responsible": staff.name,
						"start_date": "2026-09-03",
						"end_date": "2026-09-03",
						"action_plan": "Review the process and document improvements.",
					}
				],
			}
		).insert()

		self.assertEqual(objective.tasks[0].doctype, "Tasklist Objective Task")
		self.assertEqual(objective.tasks[0].status, "Not done")

		task_values = {
			"task": "Review process",
			"type": "Preventive",
			"person_responsible": staff.name,
			"start_date": "2026-09-03",
			"end_date": "2026-09-03",
			"action_plan": "Review the process and document improvements.",
			"status": "Not done",
		}

		task_fieldnames = (
			"task",
			"type",
			"person_responsible",
			"start_date",
			"end_date",
			"action_plan",
			"status",
		)
		meta = frappe.get_meta("Tasklist Objective Task")
		for fieldname in task_fieldnames:
			self.assertEqual(meta.get_field(fieldname).reqd, 1)

		for fieldname in ("task", "person_responsible", "start_date", "end_date", "action_plan"):
			incomplete_task = task_values.copy()
			incomplete_task.pop(fieldname)
			incomplete_objective = frappe.get_doc(
				{
					"doctype": "Tasklist Objective",
					"objective": f"Missing {fieldname}",
					"team": "Operations",
					"department": "Quality",
					"tasks": [incomplete_task],
				}
			)

			with self.assertRaises(frappe.MandatoryError):
				incomplete_objective.insert()

	def test_end_date_cannot_be_before_start_date(self):
		staff = frappe.get_doc(
			{
				"doctype": "Staff",
				"first_name": "Quality",
				"last_name": "Manager",
			}
		).insert()

		objective = frappe.get_doc(
			{
				"doctype": "Tasklist Objective",
				"objective": "Objective with invalid task dates",
				"team": "Operations",
				"department": "Quality",
				"tasks": [
					{
						"task": "Review process",
						"type": "Preventive",
						"person_responsible": staff.name,
						"start_date": "2026-09-03",
						"end_date": "2026-09-02",
						"action_plan": "Review the process and document improvements.",
						"status": "Not done",
					}
				],
			}
		)

		with self.assertRaises(frappe.ValidationError):
			objective.insert()

	def test_end_date_can_be_after_start_date(self):
		staff = frappe.get_doc(
			{
				"doctype": "Staff",
				"first_name": "Quality",
				"last_name": "Manager",
			}
		).insert()

		objective = frappe.get_doc(
			{
				"doctype": "Tasklist Objective",
				"objective": "Objective with valid task dates",
				"team": "Operations",
				"department": "Quality",
				"tasks": [
					{
						"task": "Review process",
						"type": "Preventive",
						"person_responsible": staff.name,
						"start_date": "2026-09-03",
						"end_date": "2026-09-04",
						"action_plan": "Review the process and document improvements.",
						"status": "Not done",
					}
				],
			}
		).insert()

		self.assertEqual(objective.tasks[0].end_date, "2026-09-04")

	def test_person_responsible_links_to_staff(self):
		field = frappe.get_meta("Tasklist Objective Task").get_field("person_responsible")

		self.assertEqual(field.fieldtype, "Link")
		self.assertEqual(field.options, "Staff")

	def test_type_allows_only_corrective_or_preventive(self):
		staff = frappe.get_doc(
			{
				"doctype": "Staff",
				"first_name": "Quality",
				"last_name": "Manager",
			}
		).insert()
		type_field = frappe.get_meta("Tasklist Objective Task").get_field("type")

		self.assertEqual(type_field.fieldtype, "Select")
		self.assertEqual(type_field.options, "Corrective\nPreventive")
		self.assertEqual(type_field.default, "Corrective")

		objective = frappe.get_doc(
			{
				"doctype": "Tasklist Objective",
				"objective": "Objective with invalid type",
				"team": "Operations",
				"department": "Quality",
				"tasks": [
					{
						"task": "Review process",
						"type": "Other",
						"person_responsible": staff.name,
						"start_date": "2026-09-03",
						"end_date": "2026-09-03",
						"action_plan": "Review the process and document improvements.",
					}
				],
			}
		)

		with self.assertRaises(frappe.ValidationError):
			objective.insert()

	def test_type_defaults_to_corrective(self):
		staff = frappe.get_doc(
			{
				"doctype": "Staff",
				"first_name": "Quality",
				"last_name": "Manager",
			}
		).insert()

		objective = frappe.get_doc(
			{
				"doctype": "Tasklist Objective",
				"objective": "Objective with default type",
				"team": "Operations",
				"department": "Quality",
				"tasks": [
					{
						"task": "Review process",
						"person_responsible": staff.name,
						"start_date": "2026-09-03",
						"end_date": "2026-09-03",
						"action_plan": "Review the process and document improvements.",
					}
				],
			}
		).insert()

		self.assertEqual(objective.tasks[0].type, "Corrective")
