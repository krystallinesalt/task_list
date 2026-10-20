# Copyright (c) 2026, Deepak Patel and contributors
# For license information, please see license.txt

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from task_list.task_list.tests.factories import make_objective, make_staff, task_row, unique_name
from task_list.task_views import get_task_view


class IntegrationTestTaskViews(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		self.original_user = frappe.session.user
		frappe.set_user("Administrator")
		self.addCleanup(frappe.set_user, self.original_user)
		self.mine = make_staff(user="Administrator")
		self.unlinked = make_staff()

	def test_staff_user_link_is_optional(self):
		field = frappe.get_meta("Staff").get_field("user")
		self.assertEqual((field.fieldtype, field.options), ("Link", "User"))
		self.assertFalse(field.reqd)
		self.assertFalse(self.unlinked.user)

	def test_my_tasks_spans_objectives_and_staff_for_current_user_only(self):
		second = make_staff(user="Administrator")
		other = make_staff(user="Guest")
		first = make_objective(
			[
				task_row(self.mine.name, task="Mine"),
				task_row(self.mine.name, task="Finished", status="Done"),
				task_row(other.name, task="Other user"),
				task_row(self.unlinked.name, task="Unlinked"),
			]
		)
		last = make_objective([task_row(second.name, task="Also mine")])
		rows = get_task_view("my")[1]
		actual = {(row.objective, row.task) for row in rows if row.objective in {first.name, last.name}}
		self.assertEqual(actual, {(first.name, "Mine"), (last.name, "Also mine")})

	def test_reports_return_all_rows_and_ignore_user_override_filters(self):
		objective = make_objective(
			[task_row(self.mine.name, task=f"Task {index}", end_date="2026-09-04") for index in range(25)]
		)
		for name in ("My Tasks", "Overdue Tasks"):
			with patch("task_list.task_views.today", return_value="2026-09-05"):
				rows = frappe.get_doc("Report", name).execute_module({"user": "Guest"})[1]
			self.assertEqual(len([row for row in rows if row.objective == objective.name]), 25)

	def test_overdue_excludes_today_future_and_completed(self):
		objective = make_objective(
			[
				task_row(self.mine.name, task="Past", end_date="2026-09-04"),
				task_row(self.unlinked.name, task="Unlinked past", end_date="2026-09-04"),
				task_row(self.mine.name, task="Today", end_date="2026-09-05"),
				task_row(self.mine.name, task="Future", end_date="2026-09-06"),
				task_row(self.mine.name, task="Done", end_date="2026-09-04", status="Done"),
			]
		)
		with patch("task_list.task_views.today", return_value="2026-09-05"):
			rows = get_task_view("overdue")[1]
		self.assertEqual(
			{row.task for row in rows if row.objective == objective.name}, {"Past", "Unlinked past"}
		)

	def test_user_without_staff_gets_setup_guidance(self):
		user = self.make_user()
		frappe.set_user(user.name)
		result = get_task_view("my")
		self.assertEqual(result[1], [])
		self.assertIn("Staff", result[2])
		self.assertIn("User", result[2])

	def test_linked_user_without_tasks_has_no_setup_warning(self):
		user = self.make_user()
		make_staff(user=user.name)
		frappe.set_user(user.name)
		self.assertEqual(get_task_view("my")[1:], ([], None))

	def test_guest_is_denied_even_with_staff_link(self):
		make_staff(user="Guest")
		frappe.set_user("Guest")
		for view in ("my", "overdue"):
			with self.assertRaises(frappe.PermissionError):
				get_task_view(view)

	def test_parent_user_permissions_scope_both_reports(self):
		user = self.make_user()
		staff = make_staff(user=user.name)
		visible = make_objective([task_row(staff.name)])
		hidden = make_objective([task_row(staff.name)])
		# Administrator sets up the real User Permission boundary for this test.
		frappe.get_doc(
			{
				"doctype": "User Permission",
				"user": user.name,
				"allow": "Tasklist Objective",
				"for_value": visible.name,
				"apply_to_all_doctypes": 1,
			}
		).insert(ignore_permissions=True)
		frappe.set_user(user.name)
		for view in ("my", "overdue"):
			with patch("task_list.task_views.today", return_value="2026-09-05"):
				rows = get_task_view(view)[1]
			self.assertIn(visible.name, {row.objective for row in rows})
			self.assertNotIn(hidden.name, {row.objective for row in rows})

	def test_report_metadata_and_entry_points(self):
		for name in ("My Tasks", "Overdue Tasks"):
			report = frappe.get_doc("Report", name)
			self.assertEqual(report.ref_doctype, "Tasklist Objective")
			self.assertFalse(report.prepared_report)
			self.assertEqual({row.role for row in report.roles}, {"System Manager"})
			columns, rows, _message = report.execute_module({})
			self.assertEqual(columns[0]["options"], "Tasklist Objective")
			self.assertIsInstance(rows, list)

	def make_user(self):
		# Deterministic test setup runs as Administrator, outside the tested user boundary.
		return frappe.get_doc(
			{
				"doctype": "User",
				"email": unique_name("task-view") + "@example.com",
				"first_name": "Task View",
				"send_welcome_email": 0,
				"roles": [{"role": "System Manager"}],
			}
		).insert(ignore_permissions=True)
