# Task List

Task List is a Frappe Framework v16 app for tracking objectives and the tasks
that deliver them. Each objective holds task rows with an owner, priority,
type, date range and status; the objective closes itself when every task is
done.

## What the app does

| Record | Purpose |
| --- | --- |
| Tasklist Objective | An objective with its team, department, type and task rows. Its status is `Open` until every task is `Done`, then `Closed`. |
| Tasklist Objective Task | A task row: priority (Mandatory, High, Medium, Low), type (Corrective, Preventive, ...), person responsible, start and end dates, action plan, remarks and status. An end date cannot precede the start date. |
| Staff | People who can be responsible for a task. |
| Objective Type | Categories for objectives. |

On the objective form, task status cells turn green when done and pink when
overdue, and priority cells are coloured by priority.

The workspace also provides **My Tasks** (your unfinished assignments across
objectives) and **Overdue Tasks** (all unfinished tasks due before today across
objectives you can read). To use My Tasks, set the optional **User** field on
your Staff record to your login account. Existing permissions still apply;
linking Staff to a User does not grant access. Open an objective from either
report to update its tasks.

Rules, validations and permissions are enforced on the server. See
[docs/domain-model.md](docs/domain-model.md) for relationships and derived
values, and [docs/decisions/](docs/decisions/README.md) for the business
decisions behind them.

## Installation

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch main
bench --site <site-name> install-app task_list
```

## Development

This app uses `pre-commit` (ruff, eslint, prettier and repository checks).
Enable it from the app directory:

```bash
pre-commit install
```

Objective forms separate operational **Details** from native comments/history in
**Activity**. Copied comment links and notifications open the Activity target.

Run the shared gates from the bench directory; GitHub Actions runs the same
stages:

```bash
apps/task_list/scripts/verify.sh pre-push
```

`lint` and `server` run the stages separately.
`apps/task_list/scripts/verify-ui.sh` runs the isolated Desk browser regressions;
see [browser setup](docs/verification.md#desk-browser-gate).
[docs/verification.md](docs/verification.md) maps each kind of change to its
required gates, and [docs/testing-matrix.md](docs/testing-matrix.md) maps each
rule to its tests.

### Agent skills and reviews

Contributor and agent rules are in [AGENTS.md](AGENTS.md) (`CLAUDE.md` is a
symlink to it). Skills live in `.agents/skills/`; upstream skills, the shared
Frappe rules block and the Semgrep rules are pinned in `skills.lock` and
vendored from [frappe-agent-kit](https://github.com/dee-pat/frappe-agent-kit):

```bash
scripts/sync-skills.sh check
```

Reviews follow the output contract in [docs/code-review.md](docs/code-review.md).
To list only the Semgrep findings a branch introduces:

```bash
scripts/semgrep-pr.sh main
```

## License

MIT. See [license.txt](license.txt).
