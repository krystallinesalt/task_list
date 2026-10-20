# 0002: Cross-objective task views use explicit Staff accounts

- Status: Accepted
- Date: 2026-10-20

## Context

Tasks belong to objectives and reference Staff, which previously had no login
identity. Users need their own unfinished work and all permitted overdue work
across objectives. Recorded after user approval of the initial implementation.

## Decision

An optional Staff User link maps assignments to the current session user.
Multiple Staff records may map to one User. My Tasks shows unfinished rows for
those Staff; missing linkage yields setup guidance, never name-based matching.
Overdue Tasks shows all permitted unfinished rows with an end date strictly
before today's site date. Existing objective permissions remain authoritative.
Both are standard Script Reports with prepared-report automation disabled.

## Consequences

No existing assignment is changed and no account link grants permissions.
Administrators must link accounts explicitly. See the
[task views spec](../specs/task-views.md) for rollout and acceptance criteria.
