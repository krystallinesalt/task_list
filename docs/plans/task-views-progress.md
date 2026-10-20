# Task views progress

Approved: optional Staff User link, My Tasks = own unfinished assignments,
Overdue Tasks = all permitted unfinished assignments due before today, existing
permissions retained. See [spec](../specs/task-views.md).

Implemented: additive Staff field, permission-scoped Script Reports, workspace
shortcuts, empty-state guidance, documentation and server regression coverage.
Development and test sites migrated; interactive field and report wiring checked.
Release validation still requires fresh-install CI; commit, push and a PR are now authorized. Existing Staff account links are left for explicit administrator setup.

Review follow-up: preserve native activity deep links and maintain an isolated
Playwright regression gate. Final publication and exact-head CI are pending.
