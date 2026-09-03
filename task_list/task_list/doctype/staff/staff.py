# Copyright (c) 2026, Deepak Patel and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class Staff(Document):
	def validate(self):
		self.full_name = " ".join(filter(None, [self.first_name, self.last_name]))
