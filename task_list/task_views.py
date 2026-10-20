# Copyright (c) 2026, Deepak Patel and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, today


def get_task_view(view):
	"""Read unfinished child rows through the current user's objective boundary."""
	if view not in ("my", "overdue"):
		raise ValueError("Unknown task view")
	frappe.has_permission("Tasklist Objective", "read", throw=True)
	frappe.has_permission("Tasklist Objective", "report", throw=True)
	filters = {"tasks.status": "Not done"}
	if view == "my":
		staff = frappe.qb.get_query(
			"Staff",
			fields=["name"],
			filters={"user": frappe.session.user},
			ignore_permissions=False,
		).run(pluck=True)
		if not staff:
			return (
				get_columns(),
				[],
				_("Link your login account in the User field of a Staff record to see My Tasks."),
			)
		filters["tasks.person_responsible"] = ["in", staff]
	else:
		filters["tasks.end_date"] = ["<", getdate(today())]

	rows = frappe.qb.get_query(
		"Tasklist Objective",
		fields=[
			"name as objective",
			"team",
			"department",
			"tasks.task as task",
			"tasks.person_responsible as person_responsible",
			"tasks.priority as priority",
			"tasks.start_date as start_date",
			"tasks.end_date as end_date",
			"tasks.status as status",
		],
		filters=filters,
		order_by="tasks.end_date asc, name asc, tasks.idx asc",
		ignore_permissions=False,
	).run(as_dict=True)
	return get_columns(), rows, None


def get_columns():
	return [
		{
			"fieldname": "objective",
			"label": _("Objective"),
			"fieldtype": "Link",
			"options": "Tasklist Objective",
			"width": 220,
		},
		{"fieldname": "task", "label": _("Task"), "fieldtype": "Data", "width": 240},
		{
			"fieldname": "person_responsible",
			"label": _("Person Responsible"),
			"fieldtype": "Link",
			"options": "Staff",
			"width": 160,
		},
		{"fieldname": "priority", "label": _("Priority"), "fieldtype": "Data", "width": 110},
		{"fieldname": "end_date", "label": _("End Date"), "fieldtype": "Date", "width": 110},
		{"fieldname": "start_date", "label": _("Start Date"), "fieldtype": "Date", "width": 110},
		{"fieldname": "status", "label": _("Status"), "fieldtype": "Data", "width": 110},
		{"fieldname": "team", "label": _("Team"), "fieldtype": "Data", "width": 140},
		{"fieldname": "department", "label": _("Department"), "fieldtype": "Data", "width": 140},
	]
