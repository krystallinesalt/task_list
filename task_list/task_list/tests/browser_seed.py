# Copyright (c) 2026, Deepak Patel and contributors
# For license information, please see license.txt

import os

import frappe
from frappe.desk.page.setup_wizard.setup_wizard import enable_setup_wizard_complete
from frappe.model.delete_doc import delete_dynamic_links
from frappe.tests.utils import toggle_test_mode

from task_list.task_list.tests.factories import make_objective, make_staff, task_row

BROWSER_USER = "task-list-browser@example.com"
OBJECTIVE = "_Test Task List Activity Browser"
HISTORY_OBJECTIVE = "_Test Task List Changes Browser"
HISTORY_STAFF = "_Test Task Changes Browser"
EMPTY_OBJECTIVE = "_Test Task List Empty Changes Browser"


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
	make_objective(objective=EMPTY_OBJECTIVE, department="Browser QA")
	staff = make_staff(first_name=HISTORY_STAFF, last_name="QA")
	history = make_objective(
		objective=HISTORY_OBJECTIVE,
		team="Initial Team",
		department="Browser QA",
		tasks=[task_row(staff.name, task="Inspect <b>belt</b>")],
	)
	history.team = "Previous Team"
	history.tasks[0].status = "Done"
	history.append("tasks", task_row(staff.name, task="Temporary task"))
	history.save(ignore_version=False)
	history.team = "Current Team"
	history.tasks[0].end_date = "2026-09-15"
	history.tasks[0].action_plan = "Updated action plan\n<em>history</em>"
	history.remove(history.tasks[1])
	history.save(ignore_version=False)


def cleanup():
	check_test_site()
	previous = frappe.in_test
	try:
		# Fixed fixture names are reused; linked history must disappear before reseeding.
		toggle_test_mode(True)
		cleanup_records()
	finally:
		toggle_test_mode(previous)


def cleanup_records():
	check_test_site()
	for name in (OBJECTIVE, HISTORY_OBJECTIVE, EMPTY_OBJECTIVE):
		if frappe.db.exists("Tasklist Objective", name):
			objective = frappe.get_doc("Tasklist Objective", name)
			if objective.department != "Browser QA":
				frappe.throw("Refusing to remove an objective not owned by browser setup")
			frappe.delete_doc("Tasklist Objective", name)
		else:
			# Recover linked artifacts left by earlier asynchronous fixture cleanup.
			delete_dynamic_links("Tasklist Objective", name)
	staff = frappe.qb.get_query(
		"Staff",
		fields=["name"],
		filters={"first_name": HISTORY_STAFF, "last_name": "QA"},
		ignore_permissions=False,
	).run(pluck=True)
	for name in staff:
		frappe.delete_doc("Staff", name)
	if frappe.db.exists("User", BROWSER_USER):
		user = frappe.get_doc("User", BROWSER_USER)
		if user.first_name != "_Test Task List Browser":
			frappe.throw("Refusing to remove a user not owned by browser setup")
		frappe.delete_doc("User", BROWSER_USER)


def check_test_site():
	frappe.only_for("Administrator")
	if frappe.local.site != "task-list-test.localhost" or not frappe.conf.allow_tests:
		frappe.throw("Browser fixtures require task-list-test.localhost with tests enabled")
