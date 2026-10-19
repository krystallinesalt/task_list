# Task List agent guidance

`CLAUDE.md` is a symlink to this file. The _Shared Frappe rules_ block below
is generated from [frappe-agent-kit](https://github.com/dee-pat/frappe-agent-kit)
by `scripts/sync-skills.sh`; never edit it here. Change the kit, bump the pin
in `skills.lock`, and run `scripts/sync-skills.sh sync`.

## Working agreement

- Inspect the current worktree and nearby implementation before editing. Keep
  unrelated user changes intact.
- Use the local skills under `.agents/skills/`. Those named in `skills.lock`
  are vendored unmodified, as are `semgrep/frappe/`, `semgrep/kit/` and the
  kit copies in `scripts/`; put adaptations in this file. `writing-for-agents`,
  `playwright` and `caveman` are the app's own.
- `.claude/settings.json` and `.codex/rules/task_list.rules` deny reading site
  config and destroying or reconfiguring `task_list.localhost` and
  `task-list-test.localhost`. Change both together;
  `scripts/test_deny_rules.py` checks they match.
- Keep changes small and focused. Put genuinely shared server logic in a
  deliberate utility module; keep DocType controllers focused.
- Use Frappe v16.31.0-compatible APIs and Python 3.14 conventions.

<!-- BEGIN synced-rules: dee-pat/frappe-agent-kit/rules/frappe.md@cdd586c8de2461d3b6f0660021de52164ddddf16 -->
## Shared Frappe rules

Frappe v16 rules shared across apps; the app's own rules win on conflict. Use
`frappe-app-dev` for Frappe work, `code-style` when writing code,
`frappe-migration` for patches, indexes, DocPerms and schema changes,
`frappe-code-review` as the review checklist, and `frappe-pr-review` to review a
PR, branch or diff, including your own before opening a PR. Review is read-only
unless the user asks for fixes.
These rules and the app's own rules win over examples and checklists in the
pinned upstream skills, some of which read records with `get_all`/`get_list`.

- The installed framework at `<bench>/apps/frappe` is the authority on Frappe
  behaviour: when correctness depends on a lifecycle, permission, transaction or
  hook detail, search it and read the relevant function rather than relying on
  memory or upstream `develop`.
- Use v16 APIs and supported hooks; never monkey-patch core.
- User-facing multi-record reads use `frappe.qb.get_query` with
  `ignore_permissions=False`. Use `ignore_permissions=True` only in reports,
  migrations, admin invariant checks whose caller's permission is verified
  separately and documented, permission-boundary internals that establish the
  boundary rather than sit behind it (for example, reads of role or
  user-permission rows the caller cannot see), and deterministic test or seed
  setup. Each use names the check or boundary it relies on in a comment, and an
  externally invocable helper still needs an administrative boundary.
- At every whitelisted boundary, check runtime types with `isinstance` before
  any read, existence or permission check; reject lists and dicts where a string
  is expected.
- Permission-query hooks build SQL only from fixed identifiers and values
  escaped with Frappe's database API.
- No `frappe.db.commit()` or `rollback()` in controllers, hooks, request
  handlers or shared services.
- Normalize dates with `frappe.utils.getdate`; never compare date strings with
  date objects.
- Async form handlers return their Promise and carry a per-form request token so
  a stale response cannot overwrite newer state.
- When a backend field or permission reaches the UI, update the client and one
  browser assertion in the same change; server tests own the full matrix.
- Background jobs and patches are idempotent and safe to rerun.
- For `>`, `>=`, `<`, `<=` rules, test greater, less and equal.
- Never restore a production backup, or use real customer files or passwords, on
  a local site; seed test data instead.
- A new function over ruff complexity 15 (C901) needs a split or a
  `# noqa: C901 -- <reason>` the reviewer accepts.
- A gate passes only when run on the current change with an observed zero exit
  status. Report an unavailable gate as a blocker, and never weaken an assertion
  to make CI pass.
- Specs, plans and progress notes state intent, invariants and current status,
  and link the PR for finished work. Test results, gate output and other run
  evidence go in the PR and CI, never in those docs.
- Commits and pull requests carry no AI attribution: no `Co-Authored-By`
  trailer for an AI agent and no "Generated with ..." line.
<!-- END synced-rules: dee-pat/frappe-agent-kit/rules/frappe.md -->

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

Read [docs/verification.md](docs/verification.md) for the definition of done,
required gates and the evidence to record before committing or reporting
completion.

- Python changes: run the focused Frappe test module, then the app suite when
  shared behavior is affected.
- DocType or migration changes: migrate the test site first, then run affected
  tests and the app suite.
- JavaScript changes: run configured ESLint/Prettier checks and `node --check`
  on changed plain JavaScript files. Validate JSON metadata.
- Browser changes: use the local Playwright guidance and run the focused flow,
  then the full suite when shared setup or navigation changes.
- Documentation or agent-guidance-only changes: run `git diff --check`,
  `scripts/sync-skills.sh check`, and validate changed paths and links. Report
  commands that were not run.
