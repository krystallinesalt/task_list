# Copyright (c) 2026, Deepak Patel and contributors
# For license information, please see license.txt

import frappe


def execute():
	"""Backfill the new priority field without changing existing values."""
	task = frappe.qb.DocType("Tasklist Objective Task")
	(
		frappe.qb.update(task)
		.set(task.priority, "Low")
		.where(task.priority.isnull() | (task.priority == ""))
	).run()
