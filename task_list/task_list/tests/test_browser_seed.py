# Copyright (c) 2026, Deepak Patel and contributors
# For license information, please see license.txt

import os
import secrets
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from task_list.task_list.tests import browser_seed


class IntegrationTestBrowserSeed(IntegrationTestCase):
	def test_browser_setup_prepares_desk_on_a_fresh_site(self):
		# The designated test site is exclusive to this app; the transaction restores this flag.
		frappe.db.set_value("Installed Application", {"app_name": "frappe"}, "is_setup_complete", 0)
		with patch.dict(os.environ, {"TASK_LIST_UI_PASSWORD": secrets.token_urlsafe(32)}):
			browser_seed.setup()
		self.addCleanup(browser_seed.cleanup)
		self.assertEqual(
			frappe.db.get_value("Installed Application", {"app_name": "frappe"}, "is_setup_complete"), 1
		)
