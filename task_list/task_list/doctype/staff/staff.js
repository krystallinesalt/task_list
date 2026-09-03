frappe.ui.form.on("Staff", {
	first_name(frm) {
		return set_full_name(frm);
	},

	last_name(frm) {
		return set_full_name(frm);
	},
});

function set_full_name(frm) {
	return frm.set_value("full_name", [frm.doc.first_name, frm.doc.last_name].filter(Boolean).join(" "));
}
