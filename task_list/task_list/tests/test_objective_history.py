# Copyright (c) 2026, Deepak Patel and contributors
# For license information, please see license.txt

import json
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import cstr, formatdate

from task_list.task_list.doctype.tasklist_objective.tasklist_objective import get_changes
from task_list.task_list.tests.factories import make_objective, make_staff, task_row, unique_name


class IntegrationTestObjectiveHistory(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		self.original_user = frappe.session.user
		frappe.set_user("Administrator")
		self.addCleanup(frappe.set_user, self.original_user)
		self.staff = make_staff()
		self.objective = make_objective([task_row(self.staff.name, task="Inspection")])

	def test_real_saves_project_objective_and_child_diffs_without_writes(self):
		doc = self.objective
		row_id = doc.tasks[0].name
		doc.team = "New Team"
		doc.tasks[0].status = "Done"
		doc.append("tasks", task_row(self.staff.name, task="New task"))
		doc.save(ignore_version=False)
		added_id = doc.tasks[1].name
		doc.remove(doc.tasks[1])
		doc.tasks[0].end_date = "2026-09-15"
		doc.save(ignore_version=False)
		before = doc.reload().as_dict()
		result = get_changes(doc.name)
		self.assertEqual(len(result["versions"]), 2)
		latest, earlier = result["versions"]
		self.assertEqual(latest["removed"][0]["id"], added_id)
		self.assertEqual(latest["rows"][0]["id"], row_id)
		self.assertEqual(latest["rows"][0]["changed"][0]["after"], formatdate("2026-09-15"))
		self.assertEqual(earlier["added"][0]["values"]["person_responsible"], self.staff.full_name)
		self.assertIn({"field": "team", "before": "Operations", "after": "New Team"}, earlier["changed"])
		self.assertEqual(result["current"]["tasks"][0]["id"], row_id)
		self.assertEqual(doc.reload().as_dict(), before)

	def test_multiline_task_edits_keep_line_breaks_without_interpreting_html(self):
		row = self.objective.tasks[0]
		row.action_plan = "First line\nSecond <em>line</em>"
		row.remarks = "One\nTwo"
		self.objective.save(ignore_version=False)
		result = get_changes(self.objective.name)
		changes = {item["field"]: item for item in result["versions"][0]["rows"][0]["changed"]}
		self.assertEqual(changes["action_plan"]["after"], row.action_plan)
		self.assertEqual(changes["remarks"]["after"], row.remarks)
		self.assertEqual(result["current"]["tasks"][0]["values"]["action_plan"], row.action_plan)

	def test_paging_is_stable_and_rejects_concurrent_saves(self):
		for team in ("One", "Two", "Three"):
			self.objective.team = team
			self.objective.save(ignore_version=False)
		with patch("task_list.objective_history.PAGE_SIZE", 2):
			first = get_changes(self.objective.name)
			self.assertTrue(first["has_more"])
			self.assertEqual(first["next_offset"], 2)
			older = get_changes(self.objective.name, offset="2", modified=first["modified"])
			self.assertEqual(len(older["versions"]), 1)
			self.assertFalse(older["has_more"])
			self.objective.team = "Four"
			self.objective.save(ignore_version=False)
			with self.assertRaises(frappe.TimestampMismatchError):
				get_changes(self.objective.name, offset=2, modified=first["modified"])

	def test_types_are_checked_before_document_reads(self):
		bad_arguments = (
			[{"objective": value} for value in (None, [], {}, True, 12, "")]
			+ [{"objective": self.objective.name, "offset": value} for value in (-1, "-1", [], {}, True, "x")]
			+ [{"objective": self.objective.name, "modified": []}]
		)
		for arguments in bad_arguments:
			with self.subTest(arguments=arguments), patch("frappe.get_doc") as read:
				with self.assertRaises((frappe.ValidationError, TypeError)):
					get_changes(**arguments)
				read.assert_not_called()

	def test_offset_upper_boundary(self):
		with patch("task_list.objective_history.read_history", return_value={}) as read:
			for offset in (2147483646, 2147483647):
				self.assertEqual(get_changes(self.objective.name, offset=offset), {})
			self.assertEqual(read.call_count, 2)
			with self.assertRaises(frappe.ValidationError):
				get_changes(self.objective.name, offset=2147483648)

	def test_older_page_requires_saved_anchor(self):
		with self.assertRaises(frappe.ValidationError):
			get_changes(self.objective.name, offset=1)

	def test_projection_drops_unrelated_and_nested_fields(self):
		self.add_version(
			{
				"changed": [["team", "Before", "After"], ["private_note", "secret", "secret"]],
				"added": [["tasks", {"name": "historic-task", "task": "Old task", "secret": "hidden"}]],
			}
		)
		result = get_changes(self.objective.name)
		self.assertNotIn("secret", json.dumps(result))
		self.assertEqual(
			result["versions"][0]["changed"], [{"field": "team", "before": "Before", "after": "After"}]
		)

	def test_corrupt_history_is_explicit_and_never_returned_raw(self):
		for payload in ("not-json", "[]", '{"changed": "bad"}', '{"row_changed": [["tasks", 0, null, []]]}'):
			self.add_version(payload)
		result = get_changes(self.objective.name)
		self.assertEqual(len(result["versions"]), 4)
		self.assertTrue(all(not row["available"] for row in result["versions"]))
		self.assertNotIn("data", result["versions"][0])

	def test_empty_history_and_metadata_only_entries(self):
		self.add_version({"comment": "Metadata only"})
		result = get_changes(self.objective.name)
		self.assertEqual(result["versions"], [])
		self.assertEqual(result["modified"], cstr(self.objective.modified))

	def test_objective_permission_is_checked_before_version_reads(self):
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": unique_name("history") + "@example.com",
				"first_name": "History",
				"send_welcome_email": 0,
				"roles": [{"role": "System Manager"}],
			}
		).insert()
		visible = make_objective()
		# Administrator sets up a real User Permission restriction for the tested user.
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
		self.assertEqual(get_changes(visible.name)["versions"], [])
		with self.assertRaises(frappe.PermissionError):
			get_changes(self.objective.name)
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			get_changes(visible.name)

	def add_version(self, data):
		# Administrator inserts synthetic native Version payloads to exercise legacy/corrupt records.
		return frappe.get_doc(
			{
				"doctype": "Version",
				"ref_doctype": "Tasklist Objective",
				"docname": self.objective.name,
				"data": data if isinstance(data, str) else json.dumps(data),
			}
		).insert(ignore_permissions=True)
