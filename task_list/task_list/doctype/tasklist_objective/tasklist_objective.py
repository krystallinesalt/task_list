# Copyright (c) 2026, Deepak Patel and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class TasklistObjective(Document):
	def before_validate(self):
		self.status = self.get_objective_status()

	def validate(self):
		for row in self.get("tasks") or []:
			if row.start_date and row.end_date and getdate(row.end_date) < getdate(row.start_date):
				frappe.throw(
					_("End Date cannot be before Start Date for task row {0}.").format(row.idx),
					frappe.ValidationError,
				)

	def get_objective_status(self):
		tasks = self.get("tasks") or []
		if tasks and all(task.status == "Done" for task in tasks):
			return "Closed"

		return "Open"


@frappe.whitelist(methods=["GET"])
def get_changes(objective: str, offset: object = 0, modified: str | None = None):
	from task_list.objective_history import read_history

	if not isinstance(objective, str) or not objective.strip():
		frappe.throw(_("Objective must be a non-empty string."), frappe.ValidationError)
	# Preserve raw offset types: an int annotation would coerce True to 1.
	if isinstance(offset, bool) or not isinstance(offset, (int, str)):
		frappe.throw(_("History offset must be a non-negative integer."), frappe.ValidationError)
	if isinstance(offset, str):
		if len(offset) > 10 or not offset.isascii() or not offset.isdigit():
			frappe.throw(_("History offset must be a non-negative integer."), frappe.ValidationError)
		offset = int(offset)
	if offset < 0 or offset > 2147483647:
		frappe.throw(_("History offset must be a non-negative integer."), frappe.ValidationError)
	if modified is not None and not isinstance(modified, str):
		frappe.throw(_("Modified timestamp must be a string."), frappe.ValidationError)
	return read_history(objective, offset, modified)
