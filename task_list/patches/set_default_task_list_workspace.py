# Copyright (c) 2026, Deepak Patel and contributors
# For license information, please see license.txt

from task_list.workspace import set_default_workspace_for_users


def execute():
	"""Assign the public Task List workspace to existing System Users."""
	set_default_workspace_for_users()
