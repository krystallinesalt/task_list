// Copyright (c) 2026, Deepak Patel and contributors
// For license information, please see license.txt
/* global task_list */

frappe.provide("task_list");

task_list.ObjectiveHistoryModel = class ObjectiveHistoryModel {
	constructor(current, versions) {
		this.current = current;
		this.versions = versions; // Newest first, matching native Version query order.
	}

	view(index) {
		const target = this.versions.length - 1 - index;
		const revision = this.versions[target];
		if (!revision || !revision.available) return { revision, unavailable: true };
		const state = JSON.parse(JSON.stringify(this.current));
		try {
			for (const later of this.versions.slice(0, target)) this.reverse(state, later);
			for (const row of [...revision.added, ...revision.rows]) {
				if (!state.tasks.some((task) => task.id === row.id))
					throw new Error("Missing task");
			}
			if (revision.removed.some((row) => state.tasks.some((task) => task.id === row.id))) {
				throw new Error("Conflicting task history");
			}
			return { revision, state, unavailable: false };
		} catch {
			return { revision, unavailable: true };
		}
	}

	reverse(state, revision) {
		if (!revision.available) throw new Error("Unreadable history");
		for (const change of revision.changed) state.fields[change.field] = change.before;
		for (const added of revision.added) {
			const index = state.tasks.findIndex((task) => task.id === added.id);
			if (index < 0) throw new Error("Missing added task");
			state.tasks.splice(index, 1);
		}
		for (const removed of revision.removed) {
			if (state.tasks.some((task) => task.id === removed.id))
				throw new Error("Duplicate task");
			const index = removed.position
				? Math.max(0, removed.position - 1)
				: state.tasks.length;
			state.tasks.splice(index, 0, JSON.parse(JSON.stringify(removed)));
		}
		for (const row of revision.rows) {
			const task = state.tasks.find((task) => task.id === row.id);
			if (!task) throw new Error("Missing edited task");
			for (const change of row.changed) task.values[change.field] = change.before;
		}
	}
};
