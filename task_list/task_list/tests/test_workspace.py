# Copyright (c) 2026, Deepak Patel and contributors
# For license information, please see license.txt

import frappe
from frappe.desk.doctype.workspace.workspace import get_workspace_app, triage_module
from frappe.tests import IntegrationTestCase

from task_list.workspace import DEFAULT_WORKSPACE


class IntegrationTestTaskListWorkspace(IntegrationTestCase):
	def test_workspace_is_public_and_contains_task_list_shortcuts(self):
		workspace = frappe.get_doc("Workspace", DEFAULT_WORKSPACE)

		self.assertEqual(workspace.module, "Task List")
		self.assertEqual(get_workspace_app(workspace), "task_list")
		self.assertEqual(workspace.public, 1)
		self.assertFalse(workspace.for_user)
		self.assertSetEqual(
			{shortcut.link_to for shortcut in workspace.shortcuts},
			{"Tasklist Objective", "Staff", "Objective Type", "My Tasks", "Overdue Tasks"},
		)

	def test_new_system_user_gets_task_list_as_default_workspace(self):
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": "task-list-default-workspace@example.com",
				"first_name": "Task List",
				"user_type": "System User",
				"roles": [{"role": "System Manager"}],
			}
		).insert(ignore_permissions=True)

		self.assertEqual(user.reload().default_workspace, DEFAULT_WORKSPACE)

	def test_explicit_user_workspace_is_preserved(self):
		# A private, non-standard page, so developer mode never exports it to app files.
		explicit_workspace = frappe.get_doc(
			{
				"doctype": "Workspace",
				"label": "Task List Explicit Workspace",
				"title": "Task List Explicit Workspace",
				"public": 0,
				"for_user": frappe.session.user,
				"module": triage_module(frappe.session.user),
				"content": "[]",
			}
		).insert(ignore_permissions=True)
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": "task-list-explicit-workspace@example.com",
				"first_name": "Explicit Workspace",
				"user_type": "System User",
				"default_workspace": explicit_workspace.name,
				"roles": [{"role": "System Manager"}],
			}
		).insert(ignore_permissions=True)

		self.assertEqual(user.reload().default_workspace, explicit_workspace.name)
