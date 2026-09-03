# Copyright (c) 2026, Deepak Patel and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate


class TasklistObjective(Document):
	def validate(self):
		for row in self.get("tasks") or []:
			if row.start_date and row.end_date and getdate(row.end_date) < getdate(row.start_date):
				frappe.throw(
					f"End Date cannot be before Start Date for task row {row.idx}.",
					frappe.ValidationError,
				)
