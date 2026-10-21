# Task List agent guidance

`CLAUDE.md` is a symlink to this file. The _Shared Frappe rules_ block below
is generated from [frappe-agent-kit](https://github.com/dee-pat/frappe-agent-kit)
by `scripts/sync-skills.sh`; never edit it here. Change the kit, bump the pin
in `skills.lock`, and run `scripts/sync-skills.sh sync`.

## Read by task

Read the row for your task; the rules below always apply. Code spans are skills.

| Task | Read first | Then, only if |
| --- | --- | --- |
| Any code change | [Definition of done](docs/verification.md#definition-of-done) | Locating tests: [rule index](docs/testing-matrix.md#rule-index); a relationship or derived value changes: [domain model](docs/domain-model.md#doctype-relationships) |
| Business rule (status, dates, defaults) | [Derived values](docs/domain-model.md#derived-values); [decision index](docs/decisions/README.md#index) | Changing a rule: [when to write a record](docs/decisions/README.md#when-to-write-one) |
| DocType, field or patch change | `frappe-migration`; [DocType relationships](docs/domain-model.md#doctype-relationships) | Patch or install hook: [required gates](docs/verification.md#required-gates) |
| Failing test or CI job | `frappe-debugging`; [failure handling](docs/verification.md#completion-and-failure-handling) | |
| Running gates and reporting done | [Required gates](docs/verification.md#required-gates); [evidence](docs/verification.md#verification-evidence) | |
| Reviewing a PR or diff | `frappe-pr-review`; [review output contract](docs/code-review.md#review-output-contract) | Review threads: `pr-review-threads` |
| Unsettled plan or business rule | `grilling` | |

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
- Use APIs of the Frappe tag pinned as `FRAPPE_VERSION` in
  `.github/workflows/ci.yml`, and Python 3.14 conventions.

<!-- BEGIN synced-rules: dee-pat/frappe-agent-kit/rules/frappe.md@8ca864c970682324dceb01a6d8bb1713c9c260b7 -->
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
- When preparing or updating a PR, read `docs/pull-requests.md` when present
  and use the repository PR template; app verification and review rules win.
- Commits and pull requests carry no AI attribution: no `Co-Authored-By`
  trailer for an AI agent and no "Generated with ..." line.
<!-- END synced-rules: dee-pat/frappe-agent-kit/rules/frappe.md -->

## App structure

- The outer Python package is `task_list/`.
- The Frappe module package is `task_list/task_list/`.
- DocTypes belong below `task_list/task_list/doctype/` and should be created
  through Frappe developer-mode workflows.
- Shared test record builders live in `task_list/task_list/tests/factories.py`;
  build objectives, staff and task rows through them.
- Keep [docs/domain-model.md](docs/domain-model.md) and
  [docs/testing-matrix.md](docs/testing-matrix.md) in step with any change to a
  DocType, `Link`/`Table` field, derived value or rule-to-test mapping.

## Sites

- `task_list.localhost` is for interactive work and `task-list-test.localhost`
  for automated tests. Reuse the test site for gates; never recreate, drop or
  restore either without approval.

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

## Commands

Run from the bench root. `TEST_SITE` overrides the default test site.

```bash
apps/task_list/scripts/verify.sh lint      # pre-commit, Frappe Semgrep, repository rule tests
apps/task_list/scripts/verify.sh server    # migrate test site + full server suite
apps/task_list/scripts/verify.sh pre-push  # lint + server
bench --site task-list-test.localhost run-tests --module task_list.task_list.doctype.tasklist_objective.test_tasklist_objective
```

CI runs the same `lint` and `server` stages. [docs/verification.md](docs/verification.md)
maps each kind of change to its required gates and the evidence to record.

## Review guidelines

- Every review follows the
  [review output contract](docs/code-review.md#review-output-contract): a
  merge-readiness score from 0/5 to 5/5, the reviewed revision, verification
  evidence and one ready-to-copy fix prompt for the actionable findings. The
  contract wins over the `frappe-pr-review` procedure on conflict.
- Review changed controllers, metadata, patches, hooks and Desk scripts
  together, and check them against the
  [domain model](docs/domain-model.md) and
  [decision records](docs/decisions/README.md).
