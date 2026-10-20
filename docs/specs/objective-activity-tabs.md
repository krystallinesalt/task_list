# Objective Details and Activity tabs

## Outcome and design

Keep objective fields and the task grid in Details, and comments plus the native
Frappe history/timeline in Activity. The current footer below the form makes
operational work and discussion compete for space.

Add structural Tab Breaks and an empty HTML mount field. On form refresh move
`frm.footer.parent` into that mount using the existing instance, preserving
comment handlers, timeline updates and standard permission behavior. Leave HTML
options empty so Frappe field refresh cannot replace the live footer. New
objectives display save-first guidance; the native footer retains control of
its own visibility. No duplicated activity records or custom activity API.

## Scope, consistency and recovery

Objective form only. No core edits, monkey patches, global CSS, new runtime dependencies,
permission changes or changes to saved task data. Playwright is a development-only
dependency for browser lifecycle regressions. Standard saves, comments,
version history, navigation and refresh continue using Frappe's components.
Repeated refreshes must keep exactly one footer. If the footer is unavailable,
leave the standard layout untouched rather than creating another instance.

## Acceptance and rollout

Native comment/communication anchors must open Activity and retain their
original target for native scrolling, including fresh-page navigation.

Metadata regression checks assert the two tabs and field placement. Browser
checks cover tab visibility, existing activity, return to Details, repeated
refresh, new objectives and comments/save using synthetic test records only.
Run lint, server suite and plain JS syntax checks; migrate test and dev sites.

This customization depends on the installed v16 footer container, so recheck
browser behavior when upgrading Frappe. No data migration or rollback patch is
needed: reverting layout/script changes and migrating restores the native footer.
