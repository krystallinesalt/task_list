# Task List domain model

A source-derived map of the app: three standalone DocTypes and one child
table, all in the `Task List` module. Update it in the same change as any new
DocType, `Link` or `Table` field, or server-derived value.

## DocType relationships

Edge labels are the fields that create the relationship.

```mermaid
flowchart LR
    TO["Tasklist Objective<br/>name = objective"]
    TOT[["Tasklist Objective Task<br/>child table"]]
    OT["Objective Type<br/>name = objective_type"]
    S["Staff<br/>name = autoincrement"]

    TO -->|"tasks"| TOT
    TO -->|"objective_type"| OT
    TOT -->|"person_responsible"| S
    S -->|"user (optional)"| U["Frappe User"]
```

## Derived values

| Field | Set by | Rule |
| --- | --- | --- |
| `Tasklist Objective.status` | `TasklistObjective.before_validate` | `Closed` when there is at least one task and every task is `Done`; otherwise `Open`. A client-sent value is overwritten. See [decision 0001](decisions/0001-objective-status-derived-from-tasks.md). |
| `Staff.full_name` | `Staff.validate`, mirrored by `staff.js` for display | First and last name joined by a space. |

## Validation

- A task row's `end_date` may equal but not precede its `start_date`; dates are
  compared with `getdate`.
- Task `priority` defaults to `Low`, `type` to `Corrective` and `status` to
  `Not done`. `action_plan` and `remarks` are optional.

## Permissions

Every standalone DocType grants full access to `System Manager` only. There are
no permission-query hooks. The whitelisted objective history reader checks
objective read permission and native Version read permission before querying.

## Desk presentation

The public **Task List** workspace links the three standalone DocTypes and the
My Tasks and Overdue Tasks reports. Install,
the `set_default_task_list_workspace` patch and a `User.after_insert` hook make
it the default workspace of System Users who have none; an explicit choice is
kept.

`tasklist_objective.js` colours the task grid: the status cell is green when
`Done` and pink when `Not done` past its end date; the priority cell is coloured
by priority. It is display only and changes no data.

## Cross-objective task reports

Staff has an optional `user` Link to User. It grants no permissions and need not
be unique: My Tasks includes unfinished rows for every Staff linked to the
session user. No link yields empty results with setup guidance. Overdue Tasks
includes all permitted unfinished rows whose end date is before the site date.
Both standard Script Reports join child rows from permission-scoped objectives
using `frappe.qb.get_query(ignore_permissions=False)`, preserving existing
System Manager report access and User Permissions. Prepared reports are off.
The workspace links both reports; objective links open the existing editor.

Objective forms use Details, Changes and Activity tabs. Details contains all objective
fields and tasks. Activity hosts the original Frappe footer container (comments
and timeline), moved by the objective client script without replacing its
handlers or history data. New objectives show save-first guidance.


## Objective change history

The read-only Changes tab calls the objective controller's `get_changes` method.
It returns a fixed projection of saved fields, task rows and permission-scoped
native Version diffs, in pages of 50. Further pages require the same objective
modified timestamp. No unsaved form values, snapshots or write methods are used.
The client reverses newer diffs for display, keyed by stable child-row names,
and highlights the selected save in a Details-like layout with a history slider.
Removed rows are shown explicitly; malformed/gapped task history is unavailable.
Native history cannot recover unrecorded changes or exact past task order.

The history preview uses isolated native Frappe Layout and child-grid controls.
Historical row identities and metadata are separate from editable Details rows;
native redraws reapply escaped diff markup without changing stored data.
