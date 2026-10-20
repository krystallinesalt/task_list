# 0004: Visualize native objective history without restoration

- Status: Accepted
- Date: 2026-10-20

## Context

Users need to understand each save without scanning the activity feed. They
explicitly excluded rollback and requested a Details-style history slider.

## Decision

Use a fixed, permission-scoped projection of retained Frappe Versions, replayed
for display only. Highlight each save's objective edits, task edits, additions
and removals. Keep saved Details data and native Activity intact. Never write
snapshots or attempt restoration. State native-history and ordering limits.

## Consequences

Works with existing history, but cannot recover unrecorded changes or exact
past row order. Corrupt history must be visible rather than fabricated. See
[the spec](../specs/objective-changes.md) for paging and consistency rules.
