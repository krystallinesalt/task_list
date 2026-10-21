# Copyright (c) 2026, Deepak Patel and contributors
# For license information, please see license.txt

"""Metadata-driven, display-only projections of native objective history."""

import json
from datetime import date, datetime, time, timedelta

import frappe
from frappe import _
from frappe.model import no_value_fields
from frappe.utils import cstr, formatdate

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
	parent_fields = history_fields(doc.meta, details_only=True)
	task_fields = history_fields(frappe.get_meta(doc.meta.get_field("tasks").options))
	current = {
		"fields": {field: display_value(parent_fields[field], doc.get(field)) for field in parent_fields},
		"task_fields": list(task_fields),
		"tasks": [project_task(row.as_dict(), task_fields) for row in doc.tasks],
	}
	entries = [project_version(row, parent_fields, task_fields) for row in versions[:PAGE_SIZE]]
	entries = [entry for entry in entries if entry is not None]
	resolve_staff_titles(current, entries)
	return {
		"current": current,
		"versions": entries,
		"modified": cstr(doc.modified),
		"has_more": len(versions) > PAGE_SIZE,
		"next_offset": offset + min(len(versions), PAGE_SIZE),
	}


def history_fields(meta, details_only=False):
	permitted = set(
		meta.get_permitted_fieldnames(
			permission_type="read", parenttype="Tasklist Objective", with_virtual_fields=False
		)
	)
	masked = {field.fieldname for field in meta.get_masked_fields(parenttype="Tasklist Objective")}
	fields = {}
	for field in meta.fields:
		if details_only and field.fieldname == "changes_tab":
			break
		if (
			field.fieldtype not in (*no_value_fields, "Password")
			and not field.is_virtual
			and field.fieldname not in masked
			and (frappe.session.user == "Administrator" or field.fieldname in permitted)
		):
			fields[field.fieldname] = field
	return fields


def project_version(row, parent_fields, task_fields):
	entry = {"id": row.name, "at": cstr(row.creation), "by": row.owner, "available": True}
	try:
		data = json.loads(row.data)
		if not isinstance(data, dict):
			raise ValueError("Invalid history object")
		entry["changed"] = project_changes(data.get("changed", []), parent_fields)
		entry["added"] = project_rows(data.get("added", []), task_fields)
		entry["removed"] = project_rows(data.get("removed", []), task_fields)
		entry["rows"] = project_row_changes(data.get("row_changed", []), task_fields)
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
					"before": display_change(allowed[field], before),
					"after": display_change(allowed[field], after),
				}
			)
	return result


def display_change(field, value):
	text = display_value(field, value)
	# Native Small Text diffs contain formatter-generated line breaks, not raw values.
	return text.replace("<br>", "\n") if field.fieldtype in ("Small Text", "Text", "Long Text") else text


def project_rows(items, task_fields):
	if not isinstance(items, list):
		raise ValueError("Invalid row changes")
	result = []
	for item in items:
		if not isinstance(item, list) or len(item) != 2:
			raise ValueError("Invalid row change")
		if item[0] == "tasks":
			result.append(project_task(item[1], task_fields))
	return result


def project_task(row, task_fields):
	if not isinstance(row, dict) or not isinstance(row.get("name"), str) or not row["name"]:
		raise ValueError("Missing task identity")
	position = row.get("idx")
	return {
		"id": row["name"],
		"position": position if isinstance(position, int) else None,
		"values": {field: display_value(task_fields[field], row.get(field)) for field in task_fields},
	}


def project_row_changes(items, task_fields):
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
		changes = project_changes(item[3], task_fields)
		if changes:
			result.append({"id": row_id, "changed": changes})
	return result


def display_value(field, value):
	if isinstance(value, (date, datetime, time, timedelta)):
		if field.fieldtype != "Date":
			return cstr(value)
		return formatdate(value)
	if value is not None and not isinstance(value, (str, int, float, bool)):
		raise ValueError("History values must be scalar")
	text = cstr(value)
	# Added/removed rows use raw dates; field edits already contain formatted dates.
	if field.fieldtype == "Date" and len(text) == 10 and text[4:5] == "-" and text[7:8] == "-":
		return formatdate(text)
	return text


def resolve_staff_titles(current, entries):
	rows = current["tasks"] + [row for entry in entries for key in ("added", "removed") for row in entry[key]]
	names = {row["values"]["person_responsible"] for row in rows if row["values"].get("person_responsible")}
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
		if "person_responsible" not in row["values"]:
			continue
		value = row["values"]["person_responsible"]
		row["values"]["person_responsible"] = titles.get(value, value)
