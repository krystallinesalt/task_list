# Copyright (c) 2026, Deepak Patel and contributors
# For license information, please see license.txt

"""Fixed, display-only projections of native objective history."""

import json
from datetime import date, datetime

import frappe
from frappe import _
from frappe.utils import cstr, formatdate

OBJECTIVE_FIELDS = ("objective", "team", "objective_type", "department", "status")
TASK_FIELDS = (
	"task",
	"priority",
	"type",
	"person_responsible",
	"start_date",
	"end_date",
	"action_plan",
	"remarks",
	"status",
)
PAGE_SIZE = 50


def read_history(objective, offset, modified):
	frappe.has_permission("Tasklist Objective", "read", throw=True)
	doc = frappe.get_doc("Tasklist Objective", objective)
	doc.check_permission("read")
	frappe.has_permission("Version", "read", throw=True)
	if modified is not None and modified != cstr(doc.modified):
		frappe.throw(
			_("The objective changed. Reload history before loading older saves."),
			frappe.TimestampMismatchError,
		)
	if offset and modified is None:
		frappe.throw(
			_("Loading older saves requires the original modified timestamp."), frappe.ValidationError
		)

	versions = frappe.qb.get_query(
		"Version",
		fields=["name", "creation", "owner", "data"],
		filters={"ref_doctype": "Tasklist Objective", "docname": doc.name},
		order_by="creation desc, name desc",
		offset=offset,
		limit=PAGE_SIZE + 1,
		ignore_permissions=False,
	).run(as_dict=True)
	current = {
		"fields": {field: display_value(field, doc.get(field)) for field in OBJECTIVE_FIELDS},
		"tasks": [project_task(row.as_dict()) for row in doc.tasks],
	}
	entries = [project_version(row) for row in versions[:PAGE_SIZE]]
	entries = [entry for entry in entries if entry is not None]
	resolve_staff_titles(current, entries)
	return {
		"current": current,
		"versions": entries,
		"modified": cstr(doc.modified),
		"has_more": len(versions) > PAGE_SIZE,
		"next_offset": offset + min(len(versions), PAGE_SIZE),
	}


def project_version(row):
	entry = {"id": row.name, "at": cstr(row.creation), "by": row.owner, "available": True}
	try:
		data = json.loads(row.data)
		if not isinstance(data, dict):
			raise ValueError("Invalid history object")
		entry["changed"] = project_changes(data.get("changed", []), OBJECTIVE_FIELDS)
		entry["added"] = project_rows(data.get("added", []))
		entry["removed"] = project_rows(data.get("removed", []))
		entry["rows"] = project_row_changes(data.get("row_changed", []))
		if not any(entry[key] for key in ("changed", "added", "removed", "rows")):
			return None
	except (ValueError, TypeError, KeyError):
		entry.update(available=False, changed=[], added=[], removed=[], rows=[])
	return entry


def project_changes(items, allowed):
	if not isinstance(items, list):
		raise ValueError("Invalid field changes")
	result = []
	for item in items:
		if not isinstance(item, list) or len(item) != 3 or not isinstance(item[0], str):
			raise ValueError("Invalid field change")
		field, before, after = item
		if field in allowed:
			result.append(
				{
					"field": field,
					"before": display_change(field, before),
					"after": display_change(field, after),
				}
			)
	return result


def display_change(field, value):
	text = display_value(field, value)
	# Native Small Text diffs contain formatter-generated line breaks, not raw values.
	return text.replace("<br>", "\n") if field in ("action_plan", "remarks") else text


def project_rows(items):
	if not isinstance(items, list):
		raise ValueError("Invalid row changes")
	result = []
	for item in items:
		if not isinstance(item, list) or len(item) != 2:
			raise ValueError("Invalid row change")
		if item[0] == "tasks":
			result.append(project_task(item[1]))
	return result


def project_task(row):
	if not isinstance(row, dict) or not isinstance(row.get("name"), str) or not row["name"]:
		raise ValueError("Missing task identity")
	position = row.get("idx")
	return {
		"id": row["name"],
		"position": position if isinstance(position, int) else None,
		"values": {field: display_value(field, row.get(field)) for field in TASK_FIELDS},
	}


def project_row_changes(items):
	if not isinstance(items, list):
		raise ValueError("Invalid task edits")
	result = []
	for item in items:
		if not isinstance(item, list) or len(item) != 4:
			raise ValueError("Invalid task edit")
		if item[0] != "tasks":
			continue
		# Native v16 stores [table, index, row name, changes].
		row_id = item[2]
		if not isinstance(row_id, str) or not row_id:
			raise ValueError("Missing edited task identity")
		changes = project_changes(item[3], TASK_FIELDS)
		if changes:
			result.append({"id": row_id, "changed": changes})
	return result


def display_value(field, value):
	if field in ("start_date", "end_date") and isinstance(value, (date, datetime)):
		return formatdate(value)
	if value is not None and not isinstance(value, (str, int, float, bool)):
		raise ValueError("History values must be scalar")
	text = cstr(value)
	# Added/removed rows use raw dates; field edits already contain formatted dates.
	if field in ("start_date", "end_date") and len(text) == 10 and text[4:5] == "-" and text[7:8] == "-":
		return formatdate(text)
	return text


def resolve_staff_titles(current, entries):
	rows = current["tasks"] + [row for entry in entries for key in ("added", "removed") for row in entry[key]]
	names = {row["values"]["person_responsible"] for row in rows if row["values"]["person_responsible"]}
	if not names or not frappe.has_permission("Staff", "read"):
		return
	staff = frappe.qb.get_query(
		"Staff",
		fields=["name", "full_name"],
		filters={"name": ["in", sorted(names)]},
		ignore_permissions=False,
	).run(as_dict=True)
	titles = {cstr(row.name): row.full_name for row in staff}
	for row in rows:
		value = row["values"]["person_responsible"]
		row["values"]["person_responsible"] = titles.get(value, value)
