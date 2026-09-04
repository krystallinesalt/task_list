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

	def test_task_rows_require_mandatory_fields_and_default_status(self):
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
		self.assertEqual(objective.tasks[0].priority, "Low")

		meta = frappe.get_meta("Tasklist Objective Task")
		priority_field = meta.get_field("priority")
		self.assertEqual(priority_field.fieldtype, "Select")
		self.assertEqual(priority_field.options, "Mandatory\nHigh\nMedium\nLow")
		self.assertEqual(priority_field.default, "Low")
		self.assertEqual(priority_field.reqd, 1)

		action_plan_field = meta.get_field("action_plan")
		self.assertEqual(action_plan_field.reqd, 0)
		self.assertEqual(action_plan_field.in_list_view, 1)

		remarks_field = meta.get_field("remarks")
		self.assertEqual(remarks_field.reqd, 0)
		self.assertEqual(remarks_field.in_list_view, 1)

		task_values = {
			"task": "Review process",
			"priority": "Low",
			"type": "Preventive",
			"person_responsible": staff.name,
			"start_date": "2026-09-03",
			"end_date": "2026-09-03",
			"action_plan": "Review the process and document improvements.",
			"status": "Not done",
		}

		task_fieldnames = (
			"task",
			"priority",
			"type",
			"person_responsible",
			"start_date",
			"end_date",
			"status",
		)
		for fieldname in task_fieldnames:
			self.assertEqual(meta.get_field(fieldname).reqd, 1)

		for fieldname in ("task", "person_responsible", "start_date", "end_date"):
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

	def test_action_plan_is_optional(self):
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
				"objective": "Objective without action plan",
				"team": "Operations",
				"department": "Quality",
				"tasks": [
					{
						"task": "Review process",
						"person_responsible": staff.name,
						"start_date": "2026-09-03",
						"end_date": "2026-09-03",
					}
				],
			}
		).insert()

		self.assertFalse(objective.tasks[0].action_plan)
		self.assertFalse(objective.tasks[0].remarks)

	def test_objective_type_is_a_link(self):
		field = frappe.get_meta("Tasklist Objective").get_field("objective_type")

		self.assertEqual(field.fieldtype, "Link")
		self.assertEqual(field.options, "Objective Type")

		objective_type = frappe.get_doc(
			{"doctype": "Objective Type", "objective_type": "Quality Improvement"}
		).insert()
		self.assertEqual(objective_type.name, "Quality Improvement")

	def test_priority_patch_backfills_blank_values(self):
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
				"objective": "Objective priority migration",
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

		frappe.db.set_value("Tasklist Objective Task", objective.tasks[0].name, "priority", "")

		from task_list.patches.add_priority_to_tasklist_objective_tasks import execute

		execute()
		self.assertEqual(
			frappe.db.get_value("Tasklist Objective Task", objective.tasks[0].name, "priority"),
			"Low",
		)

		execute()
		self.assertEqual(
			frappe.db.get_value("Tasklist Objective Task", objective.tasks[0].name, "priority"),
			"Low",
		)

	def test_status_opens_by_default_and_closes_only_when_all_tasks_are_done(self):
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
				"objective": "Objective status tracking",
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
					},
					{
						"task": "Approve changes",
						"type": "Corrective",
						"person_responsible": staff.name,
						"start_date": "2026-09-03",
						"end_date": "2026-09-03",
						"action_plan": "Approve the documented process improvements.",
					},
				],
			}
		).insert()

		self.assertEqual(objective.status, "Open")

		objective.tasks[0].status = "Done"
		objective.save()
		self.assertEqual(objective.status, "Open")

		objective.tasks[1].status = "Done"
		objective.save()
		self.assertEqual(objective.status, "Closed")

		objective.tasks[0].status = "Not done"
		objective.save()
		self.assertEqual(objective.status, "Open")

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

	def test_type_includes_corrective_and_preventive(self):
		staff = frappe.get_doc(
			{
				"doctype": "Staff",
				"first_name": "Quality",
				"last_name": "Manager",
			}
		).insert()
		type_field = frappe.get_meta("Tasklist Objective Task").get_field("type")

		self.assertEqual(type_field.fieldtype, "Select")
		self.assertIn("Corrective", type_field.options.splitlines())
		self.assertIn("Preventive", type_field.options.splitlines())
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
