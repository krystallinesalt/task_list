// Copyright (c) 2026, Deepak Patel and contributors
// For license information, please see license.txt
/* global task_list */

frappe.provide("task_list");

task_list.ObjectiveChanges = class ObjectiveChanges {
	constructor(frm, target) {
		this.frm = frm;
		this.target = target;
		this.docname = frm.docname;
		this.modified = null;
		this.versions = [];
	}

	async load(token, older = false) {
		this.token = token;
		this.loading = true;
		if (!older) {
			this.clear_sheet();
			this.target.empty().text(__("Loading recorded changes…"));
		} else this.target.find(".history-older").prop("disabled", true);
		try {
			const response = await frappe.call({
				method: "task_list.task_list.doctype.tasklist_objective.tasklist_objective.get_changes",
				type: "GET",
				args: {
					objective: this.docname,
					offset: older ? this.offset : 0,
					...(older ? { modified: this.modified } : {}),
				},
			});
			if (!this.is_current(token)) return;
			const selection = this.model?.versions[this.versions.length - 1 - this.index]?.id;
			const data = response.message;
			this.modified = data.modified;
			this.offset = data.next_offset;
			this.has_more = data.has_more;
			this.current = older ? this.current : data.current;
			this.versions = older ? [...this.versions, ...data.versions] : data.versions;
			this.model = new task_list.ObjectiveHistoryModel(this.current, this.versions);
			const previous = this.versions.findIndex((version) => version.id === selection);
			this.index =
				older && previous >= 0
					? this.versions.length - 1 - previous
					: this.versions.length - 1;
			this.render();
		} catch {
			if (!this.is_current(token)) return;
			this.clear_sheet();
			this.target
				.empty()
				.append($("<p>").text(__("History could not be loaded. Reload to try again.")));
			$("<button>")
				.addClass("btn btn-default btn-sm")
				.text(__("Retry"))
				.on("click", () => this.load(++this.frm.task_list_changes_token))
				.appendTo(this.target);
		} finally {
			if (this.is_current(token)) this.loading = false;
		}
	}

	is_current(token) {
		return this.frm.docname === this.docname && token === this.frm.task_list_changes_token;
	}

	render() {
		this.clear_sheet();
		this.target.empty().addClass("objective-changes");
		this.target.append(`<div class="history-navigation">
			<div class="history-controls">
				<button class="btn btn-default btn-sm history-previous" aria-label="${__(
					"Earlier save"
				)}">←</button>
				<input class="history-slider" type="range" aria-label="${__(
					"Save history"
				)}" min="0" list="task-list-history-saves">
				<button class="btn btn-default btn-sm history-next" aria-label="${__("Later save")}">→</button>
				<button class="btn btn-default btn-xs history-reload" aria-label="${__(
					"Refresh history"
				)}" title="${__("Refresh history")}">↻</button>
			</div><div class="history-ends sr-only"><span>${__("Older")}</span><span>${__(
			"Newer"
		)}</span></div>
			<datalist id="task-list-history-saves"></datalist>
			<div class="history-save-label" aria-live="polite"></div>
			<div class="history-summary"></div>
			<button class="btn btn-default btn-sm history-older">${__("Load older saves")}</button>
		</div><div class="history-sheet"></div>
		<p class="history-notice">${__(
			"Read-only reconstruction from recorded history. Unrecorded changes and exact past task order cannot be recovered. Staff names use available titles."
		)}</p>`);
		const count = this.versions.length;
		this.target
			.find(".history-reload")
			.on("click", () => this.load(++this.frm.task_list_changes_token));
		if (count) {
			this.target
				.find(".history-ends span")
				.first()
				.text(frappe.datetime.str_to_user(this.versions[count - 1].at));
			this.target
				.find(".history-ends span")
				.last()
				.text(frappe.datetime.str_to_user(this.versions[0].at));
			this.versions.forEach((version, index) => {
				$("<option>")
					.val(count - 1 - index)
					.text(frappe.datetime.str_to_user(version.at))
					.appendTo(this.target.find("datalist"));
			});
		}
		this.target
			.find(".history-slider")
			.attr("max", Math.max(0, count - 1))
			.prop("disabled", count < 2)
			.val(Math.max(0, this.index))
			.on("input", (event) => this.select(Number(event.target.value)));
		this.target.find(".history-previous").on("click", () => this.select(this.index - 1));
		this.target.find(".history-next").on("click", () => this.select(this.index + 1));
		this.target
			.find(".history-older")
			.toggle(this.has_more)
			.on("click", () => this.load(++this.frm.task_list_changes_token, true));
		if (!count) {
			this.target.find(".history-previous,.history-next").prop("disabled", true);
			this.target
				.find(".history-sheet")
				.text(__("No recorded objective or task changes yet."));
			return;
		}
		this.select(this.index);
	}

	select(index) {
		if (index < 0 || index >= this.versions.length) return;
		this.index = index;
		const view = this.model.view(index);
		const revision = view.revision;
		const label = __("Save {0} of {1} · {2} · {3}", [
			index + 1,
			this.versions.length,
			frappe.datetime.str_to_user(revision.at),
			revision.by,
		]);
		this.target.find(".history-slider").val(index).attr("aria-valuetext", label);
		this.target.find(".history-save-label").text(label);
		this.target.find(".history-previous").prop("disabled", index === 0);
		this.target.find(".history-next").prop("disabled", index === this.versions.length - 1);
		this.target
			.find(".history-summary")
			.text(
				__("{0} fields · {1} tasks edited · {2} added · {3} removed", [
					revision.changed.length,
					revision.rows.length,
					revision.added.length,
					revision.removed.length,
				])
			);
		this.clear_sheet();
		const sheet = this.target.find(".history-sheet").empty();
		if (view.unavailable) {
			sheet.text(
				__(
					"This save cannot be reconstructed because the retained history is incomplete or unreadable."
				)
			);
			return;
		}
		this.sheet = new task_list.ObjectiveHistorySheet(this, sheet, view);
	}

	clear_sheet() {
		this.sheet?.destroy();
		this.sheet = null;
	}

	value_html(value, change) {
		if (!change) return `<span class="history-value">${this.escape(value) || "—"}</span>`;
		return `<span class="history-before"><span class="sr-only">${__("Before")}: </span><del>${
			this.escape(change.before) || "—"
		}</del></span>
			<span class="history-after"><span class="sr-only">${__("After")}: </span>${
			this.escape(change.after) || "—"
		}</span>`;
	}

	escape(value) {
		return frappe.utils.escape_html(String(value ?? ""));
	}
};
