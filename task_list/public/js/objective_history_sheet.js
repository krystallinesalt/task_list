// Copyright (c) 2026, Deepak Patel and contributors
// For license information, please see license.txt
/* global task_list */

frappe.provide("task_list");

task_list.ObjectiveHistorySheet = class ObjectiveHistorySheet {
	constructor(view, parent, snapshot) {
		this.view = view;
		this.frm = view.frm;
		this.snapshot = snapshot;
		this.rows = [
			...snapshot.state.tasks.map((row) => ({ ...row, removed: false })),
			...snapshot.revision.removed.map((row) => ({ ...row, removed: true })),
		];
		this.layout = new frappe.ui.form.Layout({
			parent,
			fields: this.fields(),
			card_layout: true,
		});
		this.layout.make();
		this.grid = this.layout.fields_dict.tasks.grid;
		this.grid.static_rows = true;
		this.grid.editable_fields = this.frm.fields_dict.tasks.grid.visible_columns.map(
			([df]) => ({ fieldname: df.fieldname })
		);
		this.layout.refresh(snapshot.state.fields);
		// Standalone grids have no form row-render hook; observe native redraws.
		this.observer = new MutationObserver(() => this.decorate_rendered());
		this.decorate_rendered();
		this.source_grid = this.frm.fields_dict.tasks.grid;
		this.on_columns_changed = () => this.view.select(this.view.index);
		this.source_grid.wrapper.on("change.history-columns", this.on_columns_changed);
	}

	destroy() {
		this.observer.disconnect();
		this.source_grid.wrapper.off("change.history-columns", this.on_columns_changed);
		for (const row of this.grid.grid_rows || []) {
			if (row?.wrapper.hasClass("grid-row-open")) row.toggle_view(false);
		}
		this.grid.grid_sortable?.destroy();
		this.layout.wrapper.remove();
	}

	decorate_rendered() {
		this.observer.disconnect();
		this.decorate();
		for (const row of this.grid.grid_rows || []) this.decorate_open_row(row);
		this.observer.observe(this.grid.wrapper[0], { childList: true, subtree: true });
	}

	fields() {
		const fields = [];
		for (const original of this.frm.meta.fields) {
			if (original.fieldname === "changes_tab") break;
			if (original.fieldtype === "Tab Break") continue;
			if (["Section Break", "Column Break"].includes(original.fieldtype)) {
				fields.push({ ...original });
			} else if (original.fieldname === "tasks") {
				fields.push(this.table_field(original));
			} else if (Object.hasOwn(this.snapshot.state.fields, original.fieldname)) {
				const control = this.frm.fields_dict[original.fieldname];
				fields.push({
					fieldname: original.fieldname,
					label: original.label,
					fieldtype: "Data",
					reqd: original.reqd,
					hidden: control.get_status() === "None",
					read_only: 1,
				});
			}
		}
		return fields;
	}

	table_field(original) {
		const source = this.frm.fields_dict.tasks.grid;
		const visible = new Map(
			source.visible_columns.map(([df, width]) => [
				df.fieldname,
				{ width, sticky: df.sticky },
			])
		);

		const fields = source.docfields.map((df) => ({
			fieldname: df.fieldname,
			label: df.label,
			fieldtype: "Data",
			reqd: df.reqd,
			read_only: 1,
			in_list_view: visible.has(df.fieldname) ? 1 : 0,
			width: visible.get(df.fieldname)?.width,
			sticky: visible.get(df.fieldname)?.sticky,
		}));
		return {
			fieldname: "tasks",
			label: original.label,
			fieldtype: "Table",
			options: original.options,
			fields,
			read_only: 1,
			cannot_add_rows: 1,
			cannot_delete_rows: 1,
			cannot_delete_all_rows: 1,
			data: this.rows.map((row, index) => ({
				...row.values,
				// Keep native row metadata separate from the editable Details rows.
				name: `history:${row.id}`,
				idx: index + 1,
			})),
		};
	}

	edits(row) {
		return this.snapshot.revision.rows.find((item) => item.id === row.id)?.changed || [];
	}

	decorate_open_row(gridRow) {
		if (!gridRow?.wrapper.hasClass("grid-row-open") || !gridRow.grid_form?.layout) return;
		const row = this.rows.find((item) => `history:${item.id}` === gridRow.doc.name);
		const form = gridRow.grid_form.wrapper;
		form.find(".grid-collapse-row").appendTo(form.find(".grid-header-toolbar"));
		form.find(".panel-title").text(__("Task {0}", [gridRow.doc.idx]));
		for (const [field, control] of Object.entries(gridRow.grid_form.layout.fields_dict)) {
			if (!Object.hasOwn(row.values, field)) continue;
			const change = this.edits(row).find((item) => item.field === field);
			control.$wrapper.attr("data-history-field", field);
			control.$wrapper
				.find(".control-value")
				.toggleClass("history-edited", !!change)
				.html(this.view.value_html(row.values[field], change));
		}
	}

	decorate() {
		this.configure_columns();
		for (const [field, control] of Object.entries(this.layout.fields_dict)) {
			if (!Object.hasOwn(this.snapshot.state.fields, field)) continue;
			control.$wrapper.addClass("history-field").attr("data-history-field", field);
			const change = this.snapshot.revision.changed.some((item) => item.field === field);
			control.$wrapper
				.find(".control-value")
				.addClass("history-control-value")
				.toggleClass("history-edited", change)
				.html(
					this.view.value_html(
						this.snapshot.state.fields[field],
						this.snapshot.revision.changed.find((item) => item.field === field)
					)
				);
		}
		this.grid.wrapper.addClass("history-tasks");
		this.grid.form_grid.addClass("history-task-scroll");
		this.grid.toggle_checkboxes(false);
		for (const row of this.rows) {
			const gridRow = this.grid.grid_rows_by_docname[`history:${row.id}`];
			if (!gridRow) continue;
			const kind = row.removed
				? "removed"
				: this.snapshot.revision.added.some((item) => item.id === row.id)
				? "added"
				: this.edits(row).length
				? "edited"
				: "unchanged";
			gridRow.wrapper.addClass(`history-row-${kind}`).attr("data-history-row", row.id);
			const label = {
				added: __("Added"),
				removed: __("Removed"),
				edited: __("Edited"),
				unchanged: __("Unchanged"),
			}[kind];
			gridRow.row_index.find(".history-row-kind").remove();
			$("<span>")
				.addClass("sr-only history-row-kind")
				.text(label)
				.appendTo(gridRow.row_index);
			for (const [field, column] of Object.entries(gridRow.columns)) {
				column.attr("data-history-field", field);
				column.static_area.html(
					this.view.value_html(
						row.values[field],
						this.edits(row).find((item) => item.field === field)
					)
				);
				column.toggleClass(
					"history-edited",
					this.edits(row).some((item) => item.field === field)
				);
			}
		}
	}

	configure_columns() {
		const cell = this.grid.header_row?.configure_columns_button;
		if (!cell || cell.find("button").length) return;
		// Use the real form's dialog so Frappe owns persistence and column options.
		$("<button type='button' class='btn btn-link p-0'>")
			.attr("aria-label", __("Configure Columns"))
			.attr("title", __("Configure Columns"))
			.html(frappe.utils.icon("settings", "sm", "", "filter: opacity(0.5)"))
			.on("click", () =>
				this.frm.fields_dict.tasks.grid.header_row.configure_dialog_for_columns_selector()
			)
			.appendTo(cell);
	}
};
