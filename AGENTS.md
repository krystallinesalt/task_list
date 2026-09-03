# Task List agent guidance

The parent `../../AGENTS.md` contains shared Frappe bench and framework rules.
Read both files before changing this app; this file adds task-list-specific
conventions.

## Working agreement

- Inspect the current worktree and nearby implementation before editing. Keep
  unrelated user changes intact.
- Use the local skills under `.agents/skills/`: `frappe-app-dev`, `code-style`,
  `writing-for-agents`, `playwright`, and `caveman`.
- Keep changes small and focused. Put genuinely shared server logic in a
  deliberate utility module; keep DocType controllers focused.
- Use Frappe v16.31.0-compatible APIs and Python 3.14 conventions.

## App structure

- The outer Python package is `task_list/`.
- The Frappe module package is `task_list/task_list/`.
- DocTypes belong below `task_list/task_list/doctype/` and should be created
  through Frappe developer-mode workflows.
- The interactive site is `task_list.localhost`; use a separate test site for
  state-changing tests.

## Frappe workflow

- Run bare `bench` from the bench root and pass `--site task_list.localhost`
  for site-scoped commands.
- Use Frappe ORM or Query Builder for application data access. Keep raw SQL at
  justified framework or migration boundaries, with values bound through
  Frappe APIs.
- Keep durable state, validation, and permissions server-authoritative.
- After DocType metadata or patch changes, run
  `bench --site task_list.localhost migrate`. After Desk/client changes, clear
  the relevant cache and build assets when required.
- Data transformations must be idempotent patches under `task_list/patches/`,
  registered in `patches.txt`.

## Verification

- Python changes: run the focused Frappe test module, then the app suite when
  shared behavior is affected.
- DocType or migration changes: migrate the test site first, then run affected
  tests and the app suite.
- JavaScript changes: run configured ESLint/Prettier checks and `node --check`
  on changed plain JavaScript files. Validate JSON metadata.
- Browser changes: use the local Playwright guidance and run the focused flow,
  then the full suite when shared setup or navigation changes.
- Documentation or agent-guidance-only changes: run `git diff --check` and
  validate changed paths and links. Report commands that were not run.
