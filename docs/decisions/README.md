# Decision records

Each file here records one business or architecture decision the app depends
on: what was decided, why, and what it costs. Plans in `docs/plans/` describe
work in progress; a decision record stays current for as long as the code
follows it.

## When to write one

Write a record in the same change when a change:

- adopts or changes a business rule, such as how a status is derived or what a
  date range allows;
- changes how data is shared, scoped or derived across DocTypes;
- picks one approach over a credible alternative that a future change might
  revisit.

Changing a recorded rule needs the user's approval and a new or superseding
record.

## Lifecycle

Status is `Accepted`, `Superseded by NNNN` or `Deprecated`. Never rewrite an
accepted record's decision: supersede it with a new number and link both ways.
Recording a decision the code already follows uses status `Accepted` and notes
that it was recorded after the fact.

## Template

```markdown
# NNNN: Title

- Status: Accepted
- Date: YYYY-MM-DD

## Context

The problem and forces at play, with links to code and specs.

## Decision

What the app does, stated so a test could check it.

## Consequences

What follows, including costs and what would have to change to reverse it.
```

## Index

- [0001: Objective status is derived from its tasks](0001-objective-status-derived-from-tasks.md)

- [0002: Cross-objective task views use explicit Staff accounts](0002-cross-objective-task-views.md)
- [0003: Keep native objective activity in a dedicated tab](0003-objective-activity-tab.md)
- [0004: Visualize native objective history without restoration](0004-objective-history-view.md)
