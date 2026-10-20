# Copyright (c) 2026, Deepak Patel and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from task_list.task_list.tests.factories import build_objective, make_objective, make_staff, task_row


class IntegrationTestTasklistObjective(IntegrationTestCase):
	def setUp(self):
		self.staff = make_staff()

	def test_task_rows_require_mandatory_fields_and_default_status(self):
		objective = make_objective([task_row(self.staff.name)])

		self.assertEqual(objective.tasks[0].doctype, "Tasklist Objective Task")
		self.assertEqual(objective.tasks[0].status, "Not done")
		self.assertEqual(objective.tasks[0].priority, "Low")

		meta = frappe.get_meta("Tasklist Objective Task")
		priority_field = meta.get_field("priority")
		self.assertEqual(priority_field.fieldtype, "Select")
		self.assertEqual(priority_field.options, "Mandatory\nHigh\nMedium\nLow")
		self.assertEqual(priority_field.default, "Low")
		self.assertEqual(priority_field.reqd, 1)

		for fieldname in ("action_plan", "remarks"):
			field = meta.get_field(fieldname)
			self.assertEqual(field.reqd, 0, fieldname)
			self.assertEqual(field.in_list_view, 1, fieldname)

		for fieldname in (
			"task",
			"priority",
			"type",
			"person_responsible",
			"start_date",
			"end_date",
			"status",
		):
			self.assertEqual(meta.get_field(fieldname).reqd, 1, fieldname)

		for fieldname in ("task", "person_responsible", "start_date", "end_date"):
			with self.subTest(missing=fieldname), self.assertRaises(frappe.MandatoryError):
				make_objective([task_row(self.staff.name, omit=(fieldname,))])

	def test_action_plan_is_optional(self):
		objective = make_objective([task_row(self.staff.name, omit=("type", "action_plan"))])

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
		from task_list.patches.add_priority_to_tasklist_objective_tasks import execute

		objective = make_objective([task_row(self.staff.name)])
		row_name = objective.tasks[0].name
		frappe.db.set_value("Tasklist Objective Task", row_name, "priority", "")

		# The patch is idempotent: a rerun keeps the backfilled value.
		for _run in range(2):
			execute()
			self.assertEqual(frappe.db.get_value("Tasklist Objective Task", row_name, "priority"), "Low")

	def test_status_opens_by_default_and_closes_only_when_all_tasks_are_done(self):
		objective = make_objective(
			[
				task_row(self.staff.name),
				task_row(self.staff.name, task="Approve changes", type="Corrective"),
			]
		)
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

	def test_objective_without_tasks_is_open(self):
		self.assertEqual(make_objective().status, "Open")

	def test_status_is_derived_on_the_server_not_taken_from_the_client(self):
		objective = make_objective([task_row(self.staff.name)], status="Closed")

		self.assertEqual(objective.status, "Open")

	def test_end_date_cannot_be_before_start_date(self):
		objective = build_objective(
			[task_row(self.staff.name, start_date="2026-09-03", end_date="2026-09-02")]
		)

		with self.assertRaises(frappe.ValidationError):
			objective.insert()

	def test_end_date_can_equal_start_date(self):
		objective = make_objective(
			[task_row(self.staff.name, start_date="2026-09-03", end_date="2026-09-03")]
		)

		self.assertEqual(objective.tasks[0].end_date, "2026-09-03")

	def test_end_date_can_be_after_start_date(self):
		objective = make_objective(
			[task_row(self.staff.name, start_date="2026-09-03", end_date="2026-09-04")]
		)

		self.assertEqual(objective.tasks[0].end_date, "2026-09-04")

	def test_person_responsible_links_to_staff(self):
		field = frappe.get_meta("Tasklist Objective Task").get_field("person_responsible")

		self.assertEqual(field.fieldtype, "Link")
		self.assertEqual(field.options, "Staff")

	def test_type_includes_corrective_and_preventive(self):
		type_field = frappe.get_meta("Tasklist Objective Task").get_field("type")

		self.assertEqual(type_field.fieldtype, "Select")
		self.assertIn("Corrective", type_field.options.splitlines())
		self.assertIn("Preventive", type_field.options.splitlines())
		self.assertEqual(type_field.default, "Corrective")

		objective = build_objective([task_row(self.staff.name, type="Other")])
		with self.assertRaises(frappe.ValidationError):
			objective.insert()

	def test_type_defaults_to_corrective(self):
		objective = make_objective([task_row(self.staff.name, omit=("type",))])

		self.assertEqual(objective.tasks[0].type, "Corrective")


class IntegrationTestObjectiveTabs(IntegrationTestCase):
	def test_details_and_activity_layout(self):
		meta = frappe.get_meta("Tasklist Objective")
		fields = {field.fieldname: field for field in meta.fields}
		self.assertEqual(fields["details_tab"].fieldtype, "Tab Break")
		self.assertEqual(fields["activity_tab"].fieldtype, "Tab Break")
		self.assertEqual(fields["activity_content"].fieldtype, "HTML")
		# An empty mount prevents field refresh from replacing the live native footer.
		self.assertFalse(fields["activity_content"].options)
		order = [field.fieldname for field in meta.fields]
		self.assertLess(order.index("details_tab"), order.index("objective"))
		self.assertLess(order.index("tasks"), order.index("activity_tab"))
		self.assertLess(order.index("activity_tab"), order.index("activity_content"))
