# Task List rule-to-test index

Points from each business rule to its implementation and regression tests.
See [domain-model.md](domain-model.md) for relationships and
[verification.md](verification.md) for the commands. Server tests own business
rules and permissions; Desk browser tests cover the Activity integration.

## Rule index

Paths beginning with `doctype/`, `tests/` or `workspace/` are relative to
`task_list/task_list/`; `patches/`, `hooks.py` and `workspace.py` are relative
to `task_list/`.

| Rule | Implementation | Regression tests |
| --- | --- | --- |
| Objective status derived from tasks ([0001](decisions/0001-objective-status-derived-from-tasks.md)) | `doctype/tasklist_objective/tasklist_objective.py` | `doctype/tasklist_objective/test_tasklist_objective.py::test_status_opens_by_default_and_closes_only_when_all_tasks_are_done`, `::test_objective_without_tasks_is_open`, `::test_status_is_derived_on_the_server_not_taken_from_the_client` |
| Task end date not before start date (less, equal, greater) | `doctype/tasklist_objective/tasklist_objective.py` | `::test_end_date_cannot_be_before_start_date`, `::test_end_date_can_equal_start_date`, `::test_end_date_can_be_after_start_date` |
| Task row mandatory fields and defaults | `doctype/tasklist_objective_task/tasklist_objective_task.json` | `::test_task_rows_require_mandatory_fields_and_default_status`, `::test_action_plan_is_optional`, `::test_type_defaults_to_corrective`, `::test_type_includes_corrective_and_preventive` |
| Links: objective type, person responsible | `doctype/tasklist_objective/tasklist_objective.json`, `doctype/tasklist_objective_task/tasklist_objective_task.json` | `::test_objective_type_is_a_link`, `::test_person_responsible_links_to_staff` |
| Priority backfill patch is idempotent | `patches/add_priority_to_tasklist_objective_tasks.py` | `::test_priority_patch_backfills_blank_values` |
| Task List workspace is public; System Users without a default workspace get it, explicit choices are kept | `workspace.py`, `workspace/task_list/task_list.json`, `hooks.py`, `patches/set_default_task_list_workspace.py` | `tests/test_workspace.py::test_workspace_is_public_and_contains_task_list_shortcuts`, `::test_new_system_user_gets_task_list_as_default_workspace`, `::test_explicit_user_workspace_is_preserved` |
| Staff full name is derived and read-only | `doctype/staff/staff.py`, `doctype/staff/staff.js` | `doctype/staff/test_staff.py::test_full_name_is_derived_from_first_and_last_name`, `::test_full_name_is_read_only` |

Test records come from `tests/factories.py`, which gives each objective a
unique name so tests stay independent and rerunnable.

## Cross-objective task views

`tests/test_task_views.py` covers optional Staff User metadata, current-user
matching across objectives and multiple Staff, completed/other/unlinked task
exclusion, more than 20 rows, ignored user-override filters, overdue dates before/equal/after today, setup guidance, linked empty
results, Guest denial, real objective User Permission scoping and report entry
points. `tests/test_workspace.py` checks both report shortcuts.

## Repository rule tests

These run in `scripts/verify.sh lint`:

- `scripts/test_doc_links.py`: relative links and anchors in `AGENTS.md`,
  `README.md` and `docs/` resolve, and every skill in the _Read by task_ table
  exists.
- `scripts/test_deny_rules.py`: every Codex deny prefix has a Claude Code deny
  rule.
- `scripts/test_workflow_concurrency.py`: pull requests cancel superseded runs;
  push and manual runs never cancel.

## Objective form tabs

`doctype/tasklist_objective/test_tasklist_objective.py::IntegrationTestObjectiveTabs::test_details_and_activity_layout`
checks structural tabs, task placement and the empty HTML mount used to preserve
the native footer during field refresh. Browser lifecycle checks cover comments,
history, tab switching, new objectives and repeat refreshes.

`e2e/objective-activity.spec.js` owns real-browser checks for native comment and
notification anchors on fresh navigation/reload, comments and history after
save, tab visibility and a single footer after repeated refreshes. The isolated
`scripts/verify-ui.sh` gate supplies synthetic fixtures and an ephemeral account.
