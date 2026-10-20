# Copyright (c) 2026, Deepak Patel and contributors
# For license information, please see license.txt

import os

import frappe
from frappe.desk.page.setup_wizard.setup_wizard import enable_setup_wizard_complete

from task_list.task_list.tests.factories import make_objective

BROWSER_USER = "task-list-browser@example.com"
OBJECTIVE = "_Test Task List Activity Browser"


def setup():
	check_test_site()
	cleanup()
	# Fresh CI sites otherwise redirect every Desk route to the setup wizard.
	enable_setup_wizard_complete("frappe")
	frappe.clear_cache()
	# Administrator owns synthetic setup, not an application permission bypass.
	frappe.get_doc(
		{
			"doctype": "User",
			"email": BROWSER_USER,
			"first_name": "_Test Task List Browser",
			"send_welcome_email": 0,
			"new_password": os.environ["TASK_LIST_UI_PASSWORD"],
			"roles": [{"role": "System Manager"}],
		}
	).insert()
	objective = make_objective(objective=OBJECTIVE, team="Browser QA", department="Browser QA")
	objective.add_comment("Comment", "Synthetic browser check: native activity comment.")


def cleanup():
	check_test_site()
	if frappe.db.exists("Tasklist Objective", OBJECTIVE):
		objective = frappe.get_doc("Tasklist Objective", OBJECTIVE)
		if objective.department != "Browser QA":
			frappe.throw("Refusing to remove an objective not owned by browser setup")
		frappe.delete_doc("Tasklist Objective", OBJECTIVE)
	if frappe.db.exists("User", BROWSER_USER):
		user = frappe.get_doc("User", BROWSER_USER)
		if user.first_name != "_Test Task List Browser":
			frappe.throw("Refusing to remove a user not owned by browser setup")
		frappe.delete_doc("User", BROWSER_USER)


def check_test_site():
	frappe.only_for("Administrator")
	if frappe.local.site != "task-list-test.localhost" or not frappe.conf.allow_tests:
		frappe.throw("Browser fixtures require task-list-test.localhost with tests enabled")
