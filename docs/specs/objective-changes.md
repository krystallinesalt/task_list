# Objective Changes tab

## Outcome

Show what each recorded save changed in an objective and its tasks, in a
read-only layout resembling Details. A history slider runs from the oldest
loaded save to the newest, with earlier/later buttons and author/date labels.
Changed cells show before and after; task additions/removals are distinguished
by text and color. The native child grid follows Details column visibility,
order and widths, with horizontal scrolling and read-only row details for all
readable task fields. No custom expandable content is embedded in task cells. Task rows have no separate
Change column; cell/row colours and accessible row labels identify change kind. Match Details field visibility,
Team/Objective Type in the left column and Department/Status in the right.
Use native control/grid spacing; edited child cells use the same background as
edited parent fields, while added and removed rows colour every cell. Browser
assertions check computed colours and field positions, not only CSS classes.
Activity remains the native comments/timeline surface.

## Data contract and consistency

Use retained Frappe Version records only: no snapshots, rollback or writes.
Read the saved objective, not unsaved form values. The controller endpoint
validates runtime types, checks objective read access and Version read access,
and returns a metadata-driven projection of readable objective/task fields and normalized diffs.
Versions are ordered by creation/name descending in pages of 50; Older saves
extends the slider. Additional pages require the same saved modified timestamp;
a concurrent save requests a reload rather than mixing two histories.

Client replay starts at the saved current projection and reverses later diffs
using stable child-row identities. A selected save shows its after-values plus
before-values and removed-row outlines for that save. Unchanged fields supply
context. Pure row reorderings are not recorded by Frappe; row order is best
available, not an exact historical ordering. Dates and Link titles in older
versions may already be display strings; never parse them back into stored IDs.
Missing/corrupt supported history blocks reconstruction across that point and
shows an explicit unavailable message. Older retained history may be incomplete.
All historical text is escaped, including task descriptions and removed rows.
Native Small Text diffs encode line breaks as `<br>`; normalize these into
newlines for display. Native history cannot distinguish a literal `<br>` from a
formatter-generated line break. No other historical markup is interpreted.

## Permissions and failure handling

Existing roles/permissions remain unchanged. Check the parent document on every
request before reading its versions; Version reads are permission-aware too.
Ignore unrelated fields and nested data in Version payloads. No generic Version
browser or mutations. Form request tokens discard stale responses on save,
tab/document changes or overlapping loads. Errors show Retry; new objectives
and objectives without recorded changes have clear empty states.

## Verification and rollout

Build the schema/API/slider tracer slice first, then add complete replay and
Details-like presentation. Server tests cover types, parent permissions,
field discovery and exclusions, paging/stale state, row diffs and corrupt history. Pure client tests
cover replay, stable IDs and missing rows. Browser tests cover slider/keyboard
navigation, highlighted objective/task changes, task addition/removal, empty
states, escaped content, and unchanged live Details data. Run required lint,
server and browser gates and migrate the interactive site.

No new dependency or data patch. Existing saved data and APIs stay compatible.
Fresh-install CI remains a release gate when publication is authorized. Future
work may add date/task filtering; rollback is explicitly excluded.

Implementation: [PR #6](https://github.com/krystallinesalt/task_list/pull/6).

## Native Details presentation refinement

Render the historical sheet with an isolated Frappe Layout and native child grid.
Use Details field visibility, section/column arrangement, column widths and visible
columns. Keep native labels, required markers, row numbering, borders, truncation
and horizontal scrolling. Highlight saved changes inside native value areas.
Historical row data and metadata use distinct identities and copies so preview
rendering cannot change live Details values, editability or shared metadata.
No history API, permissions or stored data changes. Verify native structure,
field visibility, grid sizing, safe content and unchanged live document data.

Keep history navigation compact (slider, save label and counts) and put the
read-only reconstruction explanation below the preview.

Reapply safe diff markup after native grid refresh, task collapse, pagination and
keyboard row navigation. Disconnect rendering observation during decoration and
on preview disposal so the component neither loops nor retains detached grids.

Native presentation refinement: [PR #7](https://github.com/krystallinesalt/task_list/pull/7).

## Automatic field discovery

Derive scalar parent fields before the Changes tab and existing tasks-table fields
from current DocType metadata, including custom fields. Preserve saved-history replay and add `current.task_fields` to describe readable
task columns even when no rows exist; exclude layout, virtual, password and unreadable
permission-level fields and fields masked for the reader on the server. Only projected child fields become preview
controls. Format new Date and multiline text fields by type. No new child tables,
schema snapshots, writes, dependencies or data migrations. Current metadata owns
labels and layout; deleted fields and their retained diffs are omitted. Historical
schema and values never recorded cannot be recovered.
Acceptance: new parent/task fields appear with saved diffs without code lists,
restricted fields never leave the endpoint, and existing replay/layout still work.
Cover discovery and exclusion on the server and new field rendering in the browser.
Roll out through ordinary app deployment; reload forms after metadata changes.

Automatic field discovery: [PR #11](https://github.com/krystallinesalt/task_list/pull/11).
