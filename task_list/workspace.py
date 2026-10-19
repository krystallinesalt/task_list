# Copyright (c) 2026, Deepak Patel and contributors
# For license information, please see license.txt

import frappe

DEFAULT_WORKSPACE = "Task List"


def set_default_workspace_for_users():
	"""Assign the public Task List workspace to System Users without a choice."""
	if not frappe.db.exists("Workspace", DEFAULT_WORKSPACE):
		return

	user = frappe.qb.DocType("User")
	(
		frappe.qb.update(user)
		.set(user.default_workspace, DEFAULT_WORKSPACE)
		.where(
			(user.user_type == "System User")
			& (user.default_workspace.isnull() | (user.default_workspace == ""))
		)
	).run()


def set_default_workspace_for_user(doc, event=None):
	"""Set the workspace for a newly created System User when it is blank."""
	if doc.user_type != "System User" or doc.default_workspace:
		return

	if frappe.db.exists("Workspace", DEFAULT_WORKSPACE):
		doc.db_set("default_workspace", DEFAULT_WORKSPACE, update_modified=False)
