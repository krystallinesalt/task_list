# Adopt kit documentation checks

Goal: pin frappe-agent-kit to `8ca864c970682324dceb01a6d8bb1713c9c260b7`
and remove Task List's duplicated documentation-link parser. The kit owns
parsing and shared checks; a small app test retains README and recursive docs
coverage and requires a Read by task table containing skills.

No application data, API, permissions, runtime dependencies or site changes.
Keep upstream tools byte-identical and exclude the new copy from formatting.
Keep the existing lint entry point, adding the app checks beside the shared
checks. Missing files, anchors or required skill guidance must fail lint.

Acceptance: all previous guidance files remain covered; fixtures prove broken
README/nested links and absent skill guidance fail; the shared copy matches its
pin; lint and baseline-aware review pass. CI must pass before handoff. Recovery
is a normal revert; no migration is needed.

Status: implementation complete on `codex/bump-agent-kit-8ca864c`,
published as [PR #9](https://github.com/krystallinesalt/task_list/pull/9).
