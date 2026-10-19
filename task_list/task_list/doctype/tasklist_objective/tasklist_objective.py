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
