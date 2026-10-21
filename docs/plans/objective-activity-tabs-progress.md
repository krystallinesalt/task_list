# Objective Activity tabs progress

Approved: Details for objective/tasks; Activity for native comments and history.
See [spec](../specs/objective-activity-tabs.md).

Implemented: structural tabs, empty HTML mount, form-scoped move of the existing
footer and save-first guidance for new objectives. Existing task view work is
preserved. Development and test sites migrated; local lifecycle verification
is complete.

Implemented and submitted in [PR #5](https://github.com/krystallinesalt/task_list/pull/5).
Review follow-up includes preserved native activity deep links and the isolated
Playwright regression gate. Release remains subject to required PR checks.

Activity header correction implemented locally on `codex/activity-header-controls`:
the HTML field mount makes native timeline buttons inherit Frappe's absolute
field-action positioning, collapsing New Email's container even on desktop. A
form-scoped stylesheet preserves intrinsic control widths and allows the
header to wrap at narrow widths. Keep Frappe's toggle, email action and handlers.
No core, data or permission changes. Browser regression measures the toggle and
button container at desktop, tablet and phone widths and captures the layout.
