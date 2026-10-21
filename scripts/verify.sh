#!/usr/bin/env bash
# Shared gates for local runs and CI, adapted from dee-pat/bond_management.
# Run from any directory; bench commands run from the bench root.
#
# Usage: scripts/verify.sh [lint|server|pre-push]
#   lint      pre-commit (includes the skills.lock check and kit Semgrep rules),
#             Frappe Semgrep rules and the repository rule tests
#   server    migrate the test site and run the full server suite
#   pre-push  lint, then server
#
# TEST_SITE overrides the default test site; SEMGREP_BIN the Semgrep binary.

set -euo pipefail

MODE="${1:-pre-push}"
TEST_SITE_NAME="${TEST_SITE:-task-list-test.localhost}"
APP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BENCH_ROOT="$(cd "${APP_ROOT}/../.." && pwd)"
# Dev tools installed by 'bench setup requirements --dev' live in the bench env;
# appended so tools already on PATH (as in CI) win.
PATH="${PATH}:${BENCH_ROOT}/env/bin"

# Keep in step with [tool.bench.dev-dependencies] in pyproject.toml and linter.yml.
SEMGREP_VERSION="1.172.0"
FRAPPE_SEMGREP_RULES_DIR="${APP_ROOT}/semgrep/frappe"

usage() {
	echo "Usage: scripts/verify.sh [lint|server|pre-push]" >&2
}

find_tool() {
	if ! command -v "$1"; then
		echo "$1 is unavailable; run 'bench setup requirements --dev' from ${BENCH_ROOT}." >&2
		return 1
	fi
}

semgrep_binary() {
	local binary="${SEMGREP_BIN:-}"
	if [[ -z "${binary}" ]]; then
		binary="$(find_tool semgrep)"
	fi

	local installed_version
	installed_version="$("${binary}" --version)"
	if [[ "${installed_version}" != "${SEMGREP_VERSION}" ]]; then
		echo "Expected Semgrep ${SEMGREP_VERSION}, found ${installed_version}." >&2
		return 1
	fi
	printf '%s\n' "${binary}"
}

run_semgrep() {
	local binary
	binary="$(semgrep_binary)"

	# semgrep/ holds rules and their fixtures, which contain deliberate findings.
	cd "${APP_ROOT}"
	echo "Running blocking Frappe Semgrep rules (ERROR severity)."
	"${binary}" scan --error --metrics=off --disable-version-check \
		--config "${FRAPPE_SEMGREP_RULES_DIR}" --severity ERROR --exclude semgrep

	echo "Running advisory Frappe Semgrep rules."
	local status=0
	"${binary}" scan --metrics=off --disable-version-check \
		--config "${FRAPPE_SEMGREP_RULES_DIR}" --exclude semgrep || status=$?
	if [[ "${status}" -gt 1 ]]; then
		echo "The advisory Semgrep scan failed with status ${status}." >&2
		exit "${status}"
	fi
}

run_lint() {
	cd "${APP_ROOT}"
	local pre_commit
	pre_commit="$(find_tool pre-commit)"
	"${pre_commit}" run --all-files --show-diff-on-failure
	run_semgrep
	node --test "${APP_ROOT}/scripts/test_objective_history_model.cjs"

	python3 "${APP_ROOT}/scripts/test_doc_links.py"
	python3 "${APP_ROOT}/scripts/test_app_doc_links.py"
	python3 "${APP_ROOT}/scripts/test_deny_rules.py"
	python3 "${APP_ROOT}/scripts/test_workflow_concurrency.py" \
		"${APP_ROOT}/.github/workflows/ci.yml" \
		"${APP_ROOT}/.github/workflows/linter.yml"
}

run_server_tests() {
	cd "${BENCH_ROOT}"
	bench --site "${TEST_SITE_NAME}" set-config allow_tests true
	bench --site "${TEST_SITE_NAME}" migrate
	bench --site "${TEST_SITE_NAME}" run-tests --app task_list
}

case "${MODE}" in
	lint)
		run_lint
		;;
	server)
		run_server_tests
		;;
	pre-push)
		run_lint
		run_server_tests
		;;
	*)
		usage
		exit 2
		;;
esac
