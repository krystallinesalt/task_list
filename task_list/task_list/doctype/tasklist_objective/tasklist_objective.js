// Copyright (c) 2026, Deepak Patel and contributors
// For license information, please see license.txt

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
	onload(frm) {
		$(frm.wrapper).on("grid-row-render.task-list-colors", (event, grid_row) => {
			set_task_row_backgrounds(grid_row);
		});
	},

	refresh(frm) {
		frm.fields_dict.tasks?.grid?.grid_rows?.forEach(set_task_row_backgrounds);
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
