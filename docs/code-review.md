# Code reviews

The review output contract shared by Codex and Claude Code reviews of PRs,
commits and uncommitted changes. For a local agent review, the
`frappe-pr-review` skill owns the procedure, including untrusted PR content and
`scripts/semgrep-pr.sh`. Resolving GitHub review conversations is owned by the
`pr-review-threads` skill.

## Review output contract

### Summary, score and blocking

The vendored
[`frappe-pr-review` report format](../.agents/skills/frappe-pr-review/references/report.md)
owns the merge-readiness score (0/5 to 5/5), confirmed-only scoring and the
rule for when a finding blocks merge. This app adds:

- Start the summary with the score, then the reviewed head commit and base
  revision. For uncommitted changes, name the staged or unstaged scope.
- Required verification comes from [verification.md](verification.md).
- A finding blocks merge only inside the changed component's documented
  guarantee: a [decision record](decisions/README.md), the
  [domain model](domain-model.md), or the rules in `AGENTS.md`.

### Priority examples for this app

- **P0**: data loss or exposure of records to users without a role that grants
  them, or a broken install or migrate.
- **P1**: a derived value (objective status, full name) or validation rule
  that silently stores a wrong result.
- **P2**: a correctness or regression defect that requires changes before
  merge.
- **P3**: other actionable defect.

### Findings

Use the finding format of `frappe-pr-review`'s report and prefix each heading
with a review-local ID (`F1`, `F2`, ...). Each finding names the affected user
or data, and its fix includes a regression check. Keep questions and optional
suggestions separate from findings.

### Ready-to-copy fix prompt

When actionable findings exist, end with one fenced text block labelled
**Fix prompt** that works unchanged in a fresh Codex or Claude Code chat:
every `CLAUDE.md` here is a symlink to `AGENTS.md`, so the prompt names
repository files and steps only, never one agent's tools. Include every
finding's full details; leave no placeholders.

```text
In [repository/PR], resolve findings [IDs] from the review of [revision and base/scope].
Read AGENTS.md and docs/verification.md first.
Verify each finding against the current revision, then implement the smallest
root-cause fix for each in priority order, preserving unrelated changes. Add a
regression test for each defect. Update docs/domain-model.md and
docs/testing-matrix.md if relationships or rule-to-test mappings change. Run
the applicable gates (scripts/verify.sh) and report each finding as fixed, not
applicable with evidence, or blocked, with commands and observed results.
Do not commit, push, or merge without explicit user authorization.

Findings:
[Full details for every actionable finding: priority, location, trigger, impact, fix, regression check.]
```

With no actionable findings, state `No actionable findings; no fix prompt
needed.` and report outstanding verification separately.

### Publishing

Post a GitHub summary only when the user has authorized posting. Start it with
a marker naming the agent and the full reviewed head SHA, for example
`<!-- task-list-review-summary agent=claude-code rev=<head SHA> -->`, and
update an existing comment only when its account, agent and revision all
match.
