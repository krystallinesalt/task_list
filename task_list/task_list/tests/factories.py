# Copyright (c) 2026, Deepak Patel and contributors
# For license information, please see license.txt

"""Test record builders. Names are unique so tests stay independent and rerunnable."""

import frappe

DEFAULT_TASK_DATE = "2026-09-03"


def unique_name(prefix):
	return f"{prefix}-{frappe.generate_hash(length=8)}"


def make_staff(**overrides):
	values = {"doctype": "Staff", "first_name": "Quality", "last_name": "Manager", **overrides}
	return frappe.get_doc(values).insert()


def task_row(person_responsible, *, omit=(), **overrides):
	"""Return a valid Tasklist Objective Task row; ``omit`` drops fields to test defaults."""
	row = {
		"task": "Review process",
		"type": "Preventive",
		"person_responsible": person_responsible,
		"start_date": DEFAULT_TASK_DATE,
		"end_date": DEFAULT_TASK_DATE,
		"action_plan": "Review the process and document improvements.",
		**overrides,
	}
	for fieldname in omit:
		row.pop(fieldname)
	return row


def build_objective(tasks=(), **overrides):
	"""Return an unsaved Tasklist Objective with the given task rows."""
	values = {
		"doctype": "Tasklist Objective",
		"objective": unique_name("Objective"),
		"team": "Operations",
		"department": "Quality",
		"tasks": list(tasks),
		**overrides,
	}
	return frappe.get_doc(values)


def make_objective(tasks=(), **overrides):
	return build_objective(tasks, **overrides).insert()
