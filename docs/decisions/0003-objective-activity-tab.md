# 0003: Keep native objective activity in a dedicated tab

- Status: Accepted
- Date: 2026-10-20

## Context

The native footer puts discussion and history below the operational task grid.
Users approved Details and Activity tabs, with no Frappe core changes.
Recorded after approval of the initial implementation.

## Decision

Use structural DocType tabs and move the existing Frappe footer container into
an empty HTML mount under Activity. Reuse native comments, versions and scrolling.
Preserve comment and communication URL anchors across native tab selection.

## Consequences

There is no copied timeline implementation or new data API. The integration
depends on the installed Frappe v16 lifecycle and requires browser regressions
for upgrades. Empty HTML options prevent refresh from replacing live handlers.
See the [activity tabs spec](../specs/objective-activity-tabs.md).
