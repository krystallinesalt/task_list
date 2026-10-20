// Copyright (c) 2026, Deepak Patel and contributors
// For license information, please see license.txt
/* global task_list */

const STATUS_BACKGROUND_COLORS = {
	done: "var(--green-100)",
	overdue: "var(--pink-100)",
};

const PRIORITY_BACKGROUND_COLORS = {
	Mandatory: "var(--red-100)",
	High: "var(--orange-100)",
	Medium: "var(--green-100)",
	Low: "var(--blue-100)",
};

frappe.ui.form.on("Tasklist Objective", {
	setup(frm) {
		// Capture before Frappe selects a tab, including navigation to cached objectives.
		$(frm.wrapper).on("refresh-fields.task-list-activity", () => {
			frm.task_list_activity_anchor = window.location.hash;
		});
	},

	onload(frm) {
		$(frm.wrapper).on("grid-row-render.task-list-colors", (event, grid_row) => {
			set_task_row_backgrounds(grid_row);
		});
	},

	on_tab_change(frm) {
		return show_objective_changes(frm);
	},

	refresh(frm) {
		move_activity_to_tab(frm);
		restore_activity_anchor(frm);
		frm.fields_dict.tasks?.grid?.grid_rows?.forEach(set_task_row_backgrounds);
		return show_objective_changes(frm);
	},
});

frappe.ui.form.on("Tasklist Objective Task", {
	status(frm, cdt, cdn) {
		set_status_background_for_row(frm, cdn);
	},

	end_date(frm, cdt, cdn) {
		set_status_background_for_row(frm, cdn);
	},

	priority(frm, cdt, cdn) {
		set_priority_background_for_row(frm, cdn);
	},
});

function show_objective_changes(frm) {
	const token = (frm.task_list_changes_token || 0) + 1;
	frm.task_list_changes_token = token;
	const target = frm.fields_dict.changes_content?.$wrapper;
	if (!target?.length || frm.get_active_tab()?.df.fieldname !== "changes_tab") return;
	if (frm.is_new()) {
		target.empty().text(__("Save this objective to start recording changes."));
		return;
	}
	return frappe
		.require([
			"/assets/task_list/js/objective_history_model.js",
			"/assets/task_list/js/objective_changes.js",
			"/assets/task_list/css/objective_changes.css",
		])
		.then(() => {
			if (token !== frm.task_list_changes_token) return;
			const view = frm.task_list_changes_view;
			if (
				view?.docname === frm.docname &&
				view.modified === String(frm.doc.modified) &&
				!view.loading
			)
				return;
			frm.task_list_changes_view = new task_list.ObjectiveChanges(frm, target);
			return frm.task_list_changes_view.load(token);
		})
		.catch(() => {
			if (token !== frm.task_list_changes_token) return;
			target.empty().text(__("History components could not be loaded."));
			$("<button>")
				.addClass("btn btn-default btn-sm")
				.text(__("Retry"))
				.on("click", () => show_objective_changes(frm))
				.appendTo(target);
		});
}

function move_activity_to_tab(frm) {
	const target = frm.fields_dict.activity_content?.$wrapper;
	if (!target?.length || !frm.footer?.parent) return;

	// Move the live container so Frappe retains comment handlers and refresh ownership.
	frm.footer.parent.appendTo(target);
	target.find(".task-list-activity-hint").remove();
	if (frm.is_new()) {
		$("<p>")
			.addClass("task-list-activity-hint text-muted")
			.text(__("Save this objective to add comments and view its history."))
			.appendTo(target);
	}
}

function restore_activity_anchor(frm) {
	const anchor = frm.task_list_activity_anchor || window.location.hash;
	delete frm.task_list_activity_anchor;
	if (!/^#(comment|communication)-/.test(anchor) || !frm.footer) return;

	frm.layout.select_tab("activity_tab");
	const url = new URL(window.location.href);
	url.hash = anchor;
	history.replaceState(null, null, url);
	// The native post-render scroll handler now finds the visible timeline entry.
}

function set_task_row_backgrounds(grid_row) {
	set_status_background(grid_row);
	set_priority_background(grid_row);
}

function set_status_background(grid_row) {
	if (!grid_row || grid_row.parent_df?.fieldname !== "tasks") return;

	const status_column = grid_row.columns?.status;
	if (!status_column || !grid_row.doc) return;

	const is_overdue =
		grid_row.doc.status === "Not done" &&
		grid_row.doc.end_date &&
		frappe.datetime.get_diff(frappe.datetime.get_today(), grid_row.doc.end_date) > 0;

	let background_color = "";
	if (grid_row.doc.status === "Done") {
		background_color = STATUS_BACKGROUND_COLORS.done;
	} else if (is_overdue) {
		background_color = STATUS_BACKGROUND_COLORS.overdue;
	}

	status_column.css("background-color", background_color);
}

function set_priority_background(grid_row) {
	if (!grid_row || grid_row.parent_df?.fieldname !== "tasks") return;

	const priority_column = grid_row.columns?.priority;
	if (!priority_column || !grid_row.doc) return;

	priority_column.css(
		"background-color",
		PRIORITY_BACKGROUND_COLORS[grid_row.doc.priority] || ""
	);
}

function set_status_background_for_row(frm, cdn) {
	const grid_row = frm.fields_dict.tasks?.grid?.grid_rows_by_docname?.[cdn];
	set_status_background(grid_row);
}

function set_priority_background_for_row(frm, cdn) {
	const grid_row = frm.fields_dict.tasks?.grid?.grid_rows_by_docname?.[cdn];
	set_priority_background(grid_row);
}
