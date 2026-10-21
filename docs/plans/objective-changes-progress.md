# Objective Changes progress

Approved: read-only Changes tab using native Frappe history, a Details-style
objective/task preview and a chronological history slider. No rollback.
See [spec](../specs/objective-changes.md).

Status: implemented locally on `codex/objective-changes`. The Changes tab uses a
permission-scoped history projection, a read-only replay model and a chronological
slider. Objective fields and all nine task columns show changes inline. Older history loads without moving
the selected save, and unavailable history has explicit guidance.

Presentation correction complete: all task columns appear in Details order
using native grid widths with horizontal scrolling. The compact table and
expandable secondary fields are removed. Child-cell colours remain consistent
with parent fields; browser assertions cover columns, widths, scrolling and colours.

Implementation and review fixes are complete, including native multiline-note
formatting and removal of the redundant Change column. Published as [PR #6](https://github.com/krystallinesalt/task_list/pull/6);
Verification evidence is maintained in the PR. No rollback, snapshot
storage or Frappe core changes were introduced.

Native Details presentation refinement is complete locally on
`codex/changes-details-layout`: the custom sheet/table is replaced with isolated
native Layout/control/grid rendering. The history toolbar is compact and the
reconstruction note sits below the preview. Column settings stay synchronized
with Details, with read-only row expansion and isolated historical metadata.
Publication is authorized. Review found a native re-rendering issue; the fix
keeps task diffs visible after collapse, pagination and keyboard navigation.
Published as [PR #7](https://github.com/krystallinesalt/task_list/pull/7),
which holds review and verification evidence.

Column configuration refinement: add the native Configure Columns dialog to the
last header cell in Changes. Details and Changes share the current user's column
selection, order, widths and sticky settings; changing these must preserve the
selected save, diff colours and read-only historical values. Reuse the Details
grid's dialog and refresh the isolated preview after its settings update, without
changing core, permissions or stored objective/task data. Browser coverage checks
Update, reset, tab synchronization and persistence. Implementation complete locally
on `codex/changes-configure-columns`, published as [PR #8](https://github.com/krystallinesalt/task_list/pull/8).

Automatic field discovery is published as [PR #11](https://github.com/krystallinesalt/task_list/pull/11)
from `codex/metadata-history-fields`.
The API derives readable scalar fields from current metadata and preserves
the existing tasks-only response contract. See the automatic discovery section
in the linked spec. Historical schema reconstruction remains out of scope.

Readable task column names accompany the projection so empty tables retain their
layout. Browser fixture cleanup runs synchronously and clears orphaned links for
its reserved objective names before reuse; this avoids queued deletion racing
with a later test run when no worker is available.
