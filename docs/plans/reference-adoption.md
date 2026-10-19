# Adopt patterns from bond_management

Status: implemented in the pull request from branch
`chore/adopt-bond-management-patterns`.

## Goal

Bring the agent guidance, tooling, tests, CI and docs of this app up to the
level of [dee-pat/bond_management](https://github.com/dee-pat/bond_management),
scaled to an app with four DocTypes and no SPA, so a contributor or agent can
find the rule, the gate and the test for any change from `AGENTS.md`.

## Non-goals

- No investor SPA, Playwright suite, opt-in lifecycle or share-race suites,
  temporary-site policy or browser-credential loading. Add them when the app
  has a frontend or a multi-step migration that needs them.
- No change to DocType schema, permissions or stored data.
- The default-workspace feature (`task_list/workspace.py`, its patch and hook)
  belongs to its own change; this work only fixed its tests for Frappe
  v16.51, which has no `Workspace.app` field.

## What is adopted

| Area | Adopted from bond_management | Left out |
| --- | --- | --- |
| Agent instructions | _Read by task_ table, sites, commands, review guidelines and doc-sync rules in `AGENTS.md` | Nested `AGENTS.md` for `frontend/` and `e2e/` |
| Tooling | `scripts/verify.sh` with `lint`, `server` and `pre-push` stages; `scripts/test_doc_links.py` | `agent_policy.py`, `test_verify_helpers.py`, `test_verify_semgrep.py` |
| Tests | `tests/factories.py` with unique names; boundary tests for the date rule and status derivation | Contract and concurrency helpers |
| CI | Both workflows call `verify.sh`, so local and CI gates match | UI job, opt-in workflow |
| Docs | `domain-model.md`, `testing-matrix.md`, `code-review.md`, `decisions/` | Security review, specs |
| Readability | Ruff `F401` enforced outside `__init__.py` | Ruff complexity 12 (kept at 15) |
| App code | Translated validation messages | |

## Acceptance criteria

- `scripts/verify.sh pre-push` exits zero from the bench root.
- Every relative link and anchor in `AGENTS.md` and `docs/*.md` resolves and
  every skill named in _Read by task_ exists (`scripts/test_doc_links.py`).
- `test_tasklist_objective.py` builds records through factories and covers
  end date less than, equal to and greater than start date.

## Follow-ups

- Playwright smoke test for the Tasklist Objective row colours once a UI suite
  is wanted.
- An app-owned `task-list-*` skill if app-specific procedures grow beyond
  `AGENTS.md`.
