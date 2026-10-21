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

	def test_new_metadata_fields_are_projected_without_field_lists(self):
		parent = frappe.get_meta("Tasklist Objective")
		child = frappe.get_meta("Tasklist Objective Task")
		parent_field = frappe.get_doc(
			{"doctype": "DocField", "fieldname": "custom_summary", "fieldtype": "Data"}
		)
		child_field = frappe.get_doc({"doctype": "DocField", "fieldname": "custom_due", "fieldtype": "Date"})
		parent_fields = list(parent.fields)
		parent_fields.insert(1, parent_field)
		self.add_version(
			{
				"changed": [["custom_summary", "Old", "New"]],
				"row_changed": [
					["tasks", 0, self.objective.tasks[0].name, [["custom_due", "", "15-09-2026"]]]
				],
				"removed": [["tasks", {"name": "old-row", "custom_due": "2026-09-15"}]],
			}
		)
		with (
			patch.object(parent, "fields", parent_fields),
			patch.object(child, "fields", [*child.fields, child_field]),
		):
			result = get_changes(self.objective.name)
		self.assertIn("custom_summary", result["current"]["fields"])
		self.assertIn("custom_due", result["current"]["tasks"][0]["values"])
		self.assertIn("custom_due", result["current"]["task_fields"])
		version = result["versions"][0]
		self.assertEqual(version["changed"], [{"field": "custom_summary", "before": "Old", "after": "New"}])
		self.assertEqual(version["rows"][0]["changed"][0]["field"], "custom_due")
		self.assertEqual(version["removed"][0]["values"]["custom_due"], formatdate("2026-09-15"))

	def test_deleted_fields_are_omitted_from_current_and_recorded_history(self):
		parent = frappe.get_meta("Tasklist Objective")
		child = frappe.get_meta("Tasklist Objective Task")
		self.add_version(
			{
				"changed": [
					["team", "deleted-parent-before", "deleted-parent-after"],
					["objective", "Before", "After"],
				],
				"row_changed": [
					[
						"tasks",
						0,
						self.objective.tasks[0].name,
						[
							["remarks", "deleted-child-before", "deleted-child-after"],
							["task", "Before", "After"],
						],
					]
				],
				"removed": [
					["tasks", {"name": "old-row", "remarks": "deleted-child-value", "task": "Old task"}]
				],
			}
		)
		with (
			patch.object(parent, "fields", [field for field in parent.fields if field.fieldname != "team"]),
			patch.object(child, "fields", [field for field in child.fields if field.fieldname != "remarks"]),
		):
			result = get_changes(self.objective.name)
		self.assertNotIn("team", result["current"]["fields"])
		self.assertNotIn("remarks", result["current"]["task_fields"])
		self.assertNotIn("remarks", result["current"]["tasks"][0]["values"])
		self.assertNotIn("deleted-", json.dumps(result))
		version = result["versions"][0]
		self.assertEqual([change["field"] for change in version["changed"]], ["objective"])
		self.assertEqual([change["field"] for change in version["rows"][0]["changed"]], ["task"])

	def test_masked_fields_are_excluded_from_current_and_history_without_clearance(self):
		parent = frappe.get_meta("Tasklist Objective")
		child = frappe.get_meta("Tasklist Objective Task")
		self.objective.team = "masked-parent-current"
		self.objective.tasks[0].remarks = "masked-child-current"
		self.objective.save(ignore_version=False)
		self.add_version(
			{
				"changed": [
					["team", "masked-parent-before", "masked-parent-after"],
					["objective", "Before", "After"],
				],
				"removed": [["tasks", {"name": "old-row", "remarks": "masked-child-removed"}]],
			}
		)
		with (
			patch.object(parent, "get_masked_fields", return_value=[parent.get_field("team")]),
			patch.object(child, "get_masked_fields", return_value=[child.get_field("remarks")]),
		):
			result = get_changes(self.objective.name)
		self.assertNotIn("team", result["current"]["fields"])
		self.assertNotIn("remarks", result["current"]["task_fields"])
		self.assertNotIn("masked-", json.dumps(result))
		with (
			patch.object(parent, "get_masked_fields", return_value=[]),
			patch.object(child, "get_masked_fields", return_value=[]),
		):
			cleared = get_changes(self.objective.name)
		self.assertEqual(cleared["current"]["fields"]["team"], "masked-parent-current")
		self.assertEqual(cleared["current"]["tasks"][0]["values"]["remarks"], "masked-child-current")

	def test_discovery_excludes_sensitive_virtual_layout_and_restricted_fields(self):
		from task_list.objective_history import history_fields

		fields = [
			frappe._dict(fieldname=name, fieldtype=kind, permlevel=level, is_virtual=virtual)
			for name, kind, level, virtual in (
				("ordinary", "Data", 0, False),
				("secret", "Password", 0, False),
				("restricted", "Data", 1, False),
				("computed", "Data", 0, True),
				("layout", "HTML", 0, False),
				("nested", "Table", 0, False),
			)
		]
		meta = frappe._dict(
			fields=fields,
			get_masked_fields=lambda **kwargs: [],
			get_permitted_fieldnames=lambda **kwargs: ["ordinary", "secret", "computed", "layout", "nested"],
		)
		with patch.dict(frappe.session, user="reader@example.com"):
			self.assertEqual(list(history_fields(meta)), ["ordinary"])

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

	def test_empty_task_table_still_describes_readable_columns(self):
		empty = get_changes(make_objective().name)
		self.assertEqual(empty["current"]["tasks"], [])
		self.assertIn("task", empty["current"]["task_fields"])

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
