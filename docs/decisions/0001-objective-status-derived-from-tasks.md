# 0001: Objective status is derived from its tasks

- Status: Accepted
- Date: 2026-10-19 (recorded after the fact)

## Context

A Tasklist Objective groups task rows. Users need to see which objectives are
finished without opening each one, and a manually set status drifts from the
rows it summarises.

## Decision

`TasklistObjective.before_validate` sets `status` on every save: `Closed` when
the objective has at least one task and every task's status is `Done`,
otherwise `Open`. An objective with no tasks is `Open`. Any status sent by a
client is overwritten.

## Consequences

- The status is always consistent with saved rows, and list views and reports
  can filter on it.
- Users cannot close an objective with unfinished tasks or reopen a finished
  one by hand; adding a manual override needs a superseding record.
- Changing a task row's status through `frappe.db.set_value` bypasses the
  controller and leaves the parent status stale; change rows through the
  parent document.

Tests: `test_tasklist_objective.py::test_status_opens_by_default_and_closes_only_when_all_tasks_are_done`,
`::test_objective_without_tasks_is_open` and
`::test_status_is_derived_on_the_server_not_taken_from_the_client`.
