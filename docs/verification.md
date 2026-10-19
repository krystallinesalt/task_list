# Verification

Read this file for changes, verification, CI failures and completion
evidence. It started from frappe-agent-kit `templates/verification.md` and is
owned by this app.

## Definition of done

A change is done when its own acceptance criteria are met and every applicable
item below holds. Record any item that does not apply, with the reason, in the
evidence.

- **Proven:** new or changed behaviour has a test that fails without the change
  and passes with it; a bug fix adds its regression test first.
- **Conventions held:** app rules in `AGENTS.md` still hold, or changed
  only with an explicit decision and boundary tests.
- **Install and migrate:** a data patch is idempotent and registered; an
  invariant it creates is also bootstrapped in `after_install`; the
  fresh-install gate passed.
- **Docs in step:** specs, the testing matrix and agent guidance describe the
  new behaviour, or their review is recorded.
- **Clean diff:** nothing outside the task's scope; no debug output, dead code
  or commented-out blocks; no secrets or site credentials.
- **Verified:** every required gate below exited zero on the final commit, and
  required CI checks passed on it.

## Verification evidence

Before committing or pushing, record local verification evidence in the PR
description (or the handoff message when there is no PR), never in specs,
plans or progress notes. Before reporting completion, include final CI results
for any required remote checks. Record:

- Risk classification:
- Required gates:
- Commands executed:
- Exit statuses:
- Tests passed:
- Tests failed:
- Tests not run:
- Blockers:
- Unverified local/CI differences:

For workflow, fresh-site bootstrap, browser-test or other
environment-sensitive changes, list the remaining local-vs-CI differences in
the last field.

## Required gates

Match verification to the risk of the change. Commands run from the bench
directory unless stated otherwise.

| Change                                                        | Required gates                                    | Command                                                                                                                  |
| ------------------------------------------------------------- | ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| Docs, agent guidance or tests only                            | Diff check, pre-commit (includes `sync-skills.sh check`) | `git diff --check` and `pre-commit run --all-files` (app directory)                                                |
| Server logic, permissions, hooks or shared utilities          | Lint, focused module, then app suite              | `bench --site task-list-test.localhost run-tests --module <module>`, then `--app task_list`                              |
| Patches, schema, dependencies or installation (fresh install) | Lint, migrate test site, app suite, fresh install | `bench --site task-list-test.localhost migrate`, then `run-tests --app task_list`; CI `Server` job for the fresh install |
| Client, Desk metadata, reports or workspaces                  | Lint, JSON validation, migrate, affected tests    | `pre-commit run --all-files`, `bench --site task-list-test.localhost migrate`, affected test modules                    |
| Workflows or CI bootstrap                                     | Lint, concurrency test, CI run on the PR          | `python3 scripts/test_workflow_concurrency.py .github/workflows/ci.yml .github/workflows/linter.yml`, then PR checks     |

## Completion and failure handling

- If a required command cannot run because a service, browser, dependency,
  site or credential is unavailable, report the exact command, the blocking
  condition and the remaining verification. Do not substitute an unrelated
  check.
- When CI fails, read the traceback and reproduce the failing test alone and
  in the full suite before changing implementation or assertions.
- CI pins Frappe to the exact tag in `FRAPPE_VERSION`; bump every workflow
  together, deliberately, after checking the release.
