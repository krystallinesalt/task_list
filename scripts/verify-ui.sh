#!/usr/bin/env bash
# Isolated browser gate: synthetic data and an ephemeral login on the test site only.
set -euo pipefail

APP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BENCH_ROOT="$(cd "${APP_ROOT}/../.." && pwd)"
TEST_SITE_NAME="task-list-test.localhost"
UI_PORT="${TASK_LIST_UI_PORT:-8001}"
UI_WORK="$(mktemp -d)"
SERVER_PID=""
export TASK_LIST_UI_PASSWORD
TASK_LIST_UI_PASSWORD="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export BASE_URL="http://127.0.0.1:${UI_PORT}"

cleanup() {
	local result=$?
	trap - EXIT
	if [[ -n "${SERVER_PID}" ]]; then
		kill "${SERVER_PID}" 2>/dev/null || true
		wait "${SERVER_PID}" 2>/dev/null || true
	fi
	cd "${BENCH_ROOT}"
	if ! bench --site "${TEST_SITE_NAME}" execute task_list.task_list.tests.browser_seed.cleanup; then
		echo "Browser fixture cleanup failed." >&2
		result=1
	fi
	rm -rf "${UI_WORK}"
	exit "${result}"
}
trap cleanup EXIT

cd "${BENCH_ROOT}"
bench --site "${TEST_SITE_NAME}" clear-cache
bench --site "${TEST_SITE_NAME}" execute task_list.task_list.tests.browser_seed.setup
bench --site "${TEST_SITE_NAME}" serve --port "${UI_PORT}" --noreload > "${UI_WORK}/server.log" 2>&1 &
SERVER_PID=$!
ready=0
for _attempt in {1..30}; do
	if ! kill -0 "${SERVER_PID}" 2>/dev/null; then
		cat "${UI_WORK}/server.log" >&2
		exit 1
	fi
	if curl --silent --fail "${BASE_URL}/login" > /dev/null; then
		ready=1
		break
	fi
	sleep 1
done
if [[ "${ready}" != 1 ]]; then
	cat "${UI_WORK}/server.log" >&2
	exit 1
fi
yarn --cwd "${APP_ROOT}" test:e2e
