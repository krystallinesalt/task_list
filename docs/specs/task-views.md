# Cross-objective task views

## Goal and contract

Give existing Task List users two workspace reports across objectives they can
read. My Tasks shows unfinished task rows assigned to Staff records whose
optional `user` Link matches the session user. Multiple Staff records may link
to the same User; all matching assignments count. No name-based guessing.
Overdue Tasks shows unfinished rows with end dates strictly before the site's
current date, regardless of assignee. Today and future dates are not overdue.

Rows show objective (link), task, responsible Staff (link), priority, start/end
dates, status, team and department, ordered by end date, objective and row index.
Open the objective to edit tasks; these reports do not mutate records.

## Permissions and compatibility

Keep existing System Manager permissions and standard report authorization.
Read parent objectives through permission-aware Query Builder joins so child
rows cannot bypass parent access. Matching a Staff account grants no access.
No user filter can impersonate another account. Prepared reports are disabled
because My Tasks depends on the current session. The optional Staff field is
additive, has no default or uniqueness constraint, and requires no data patch.
Existing Staff and assignments continue to work without an account link.

## Empty states and recovery

No linked Staff yields an empty My Tasks report with setup guidance. A linked
Staff with no unfinished assignments yields an ordinary empty report. Missing
permissions deny access. Database/request errors use standard Desk retry/error
handling; no fallback to unscoped reads.

## Tests and acceptance

Cover current-user matching, multiple objectives and Staff links, exclusion of
completed/other/unlinked tasks, overdue date boundaries, parent restrictions,
unauthorized users, field metadata and workspace/report wiring. Verify the
visible reports and setup guidance in a browser. Run lint, focused tests and
the server suite; fresh-install CI is required before release.

## Scope and rollout

Migrate test and development sites, then use workspace shortcuts. Link Staff
accounts explicitly as needed. No new roles, reminders, dashboard, task editing
surface or change to objective completion rules in this slice. Follow-ups:
role design, dashboard and a maintained browser suite.
