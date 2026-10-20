const { test, expect } = require("@playwright/test");

const objective = "_Test Task List Changes Browser";
const route = `/desk/tasklist-objective/${encodeURIComponent(objective)}#changes_tab`;
const method = "task_list.task_list.doctype.tasklist_objective.tasklist_objective.get_changes";

test.beforeEach(async ({ page }) => {
	if (!process.env.TASK_LIST_UI_PASSWORD) throw new Error("Browser-test password is required");
	const login = await page.request.post("/api/method/login", {
		form: { usr: "task-list-browser@example.com", pwd: process.env.TASK_LIST_UI_PASSWORD },
	});
	expect(login.ok()).toBeTruthy();
});

test("history slider highlights saves in a Details-style objective/task view without editing data", async ({
	page,
}, testInfo) => {
	const before = (
		await (
			await page.request.get(
				`/api/resource/Tasklist Objective/${encodeURIComponent(objective)}`
			)
		).json()
	).data;
	await page.goto(route);
	const changes = page.getByRole("tabpanel", { name: "Changes" });
	await expect(changes.locator(".history-save-label")).toContainText("Save 2 of 2");
	const team = changes.locator('.history-field[data-history-field="team"]');
	await expect(team.locator(".history-before")).toHaveText("Before: Previous Team");
	await expect(team.locator(".history-after")).toHaveText("After: Current Team");
	await expect(changes.locator(".history-row-removed")).toContainText("Temporary task");
	await expect(
		changes
			.locator('.history-tasks [data-history-field="task"]')
			.getByText("Inspect <b>belt</b>", { exact: true })
	).toBeVisible();
	await expect(changes.locator(".history-tasks b")).toHaveCount(0);
	await expect(
		changes.locator('.history-tasks [data-history-field="end_date"].history-edited')
	).toHaveCount(1);

	const taskDate = changes.locator(
		'.history-tasks td[data-history-field="end_date"].history-edited'
	);
	const parentColor = await team.evaluate(
		(element) => getComputedStyle(element).backgroundColor
	);
	await expect(taskDate).toHaveCSS("background-color", parentColor);
	await expect(changes.locator('[data-history-field="action_plan"].history-edited')).toHaveCSS(
		"background-color",
		parentColor
	);
	const removedCell = changes.locator(".history-row-removed td").first();
	await expect(removedCell).not.toHaveCSS("background-color", "rgba(0, 0, 0, 0)");
	await expect(removedCell).not.toHaveCSS("background-color", parentColor);
	const positions = await changes.locator(".history-field").evaluateAll((fields) =>
		Object.fromEntries(
			fields.map((field) => [
				field.dataset.historyField,
				{
					x: field.getBoundingClientRect().x,
					y: field.getBoundingClientRect().y,
				},
			])
		)
	);
	expect(positions.team.x).toBe(positions.objective_type.x);
	expect(positions.department.x).toBe(positions.status.x);
	expect(positions.team.y).toBe(positions.department.y);
	expect(positions.objective_type.y).toBe(positions.status.y);
	await page.screenshot({ path: testInfo.outputPath("changes-latest.png"), fullPage: true });
	await expect(taskDate).toHaveCSS("white-space", "normal");
	await changes.locator(".history-tasks").scrollIntoViewIfNeeded();
	await page.screenshot({ path: testInfo.outputPath("changes-tasks.png") });
	await expect(changes.locator(".history-task-details")).toHaveCount(0);
	await expect(changes.locator(".history-tasks th")).toHaveText([
		"Task",
		"Priority",
		"Type",
		"Person Responsible",
		"Start Date",
		"End Date",
		"Action Plan",
		"Remarks",
		"Status",
	]);
	const nativeWidths = await page.evaluate(() => {
		const grid = frappe.views.formview["Tasklist Objective"].frm.fields_dict.tasks.grid;
		return grid.docfields
			.filter((field) => field.in_list_view)
			.map((field) => grid.get_column_width(field));
	});
	const historyWidths = await changes
		.locator(".history-tasks col")
		.evaluateAll((columns) => columns.map((column) => parseFloat(column.style.width)));
	expect(historyWidths).toEqual(nativeWidths);
	const scroller = changes.locator(".history-task-scroll");
	expect(await scroller.evaluate((element) => element.scrollWidth > element.clientWidth)).toBe(
		true
	);
	const actionPlan = changes.locator('[data-history-field="action_plan"].history-edited');
	await actionPlan.scrollIntoViewIfNeeded();
	expect(await scroller.evaluate((element) => element.scrollLeft)).toBeGreaterThan(0);
	await expect(actionPlan).toBeInViewport();
	await page.screenshot({ path: testInfo.outputPath("changes-tasks-scrolled.png") });
	await expect(
		changes.locator('[data-history-field="action_plan"].history-edited .history-after')
	).toHaveText("After: Updated action plan\n<em>history</em>");
	await expect(changes.locator(".history-tasks em, .history-tasks br")).toHaveCount(0);
	await expect(actionPlan.locator(".history-after")).toHaveCSS("white-space", "pre-wrap");
	const slider = changes.getByRole("slider", { name: "Save history" });
	await slider.focus();
	await slider.press("Home");
	await expect(changes.locator(".history-save-label")).toContainText("Save 1 of 2");
	await expect(team.locator(".history-before")).toHaveText("Before: Initial Team");
	await expect(changes.locator(".history-row-added")).toContainText("Temporary task");
	await expect(changes.locator(".history-row-added td").first()).not.toHaveCSS(
		"background-color",
		"rgba(0, 0, 0, 0)"
	);
	await expect(
		changes.locator('.history-tasks [data-history-field="status"].history-edited')
	).toHaveCount(1);
	await expect(changes.getByRole("button", { name: "Earlier save" })).toBeDisabled();
	await changes.getByRole("button", { name: "Later save" }).click();
	await expect(changes.locator(".history-save-label")).toContainText("Save 2 of 2");
	await expect(changes.getByRole("button", { name: "Later save" })).toBeDisabled();
	await page.getByRole("tab", { name: "Details", exact: true }).click();
	await expect(page.locator('[data-fieldname="team"] input')).toHaveValue("Current Team");
	const after = (
		await (
			await page.request.get(
				`/api/resource/Tasklist Objective/${encodeURIComponent(objective)}`
			)
		).json()
	).data;
	expect(after).toEqual(before);
});

test("empty and new objective histories have clear guidance", async ({ page }) => {
	await page.goto(
		`/desk/tasklist-objective/${encodeURIComponent(
			"_Test Task List Empty Changes Browser"
		)}#changes_tab`
	);
	await expect(page.getByRole("tabpanel", { name: "Changes" })).toContainText(
		"No recorded objective or task changes yet."
	);
	await page.goto("/desk/tasklist-objective");
	await page.getByRole("button", { name: "Add Tasklist Objective", exact: true }).click();
	await page.getByRole("tab", { name: "Changes", exact: true }).click();
	await expect(page.getByRole("tabpanel", { name: "Changes" })).toContainText(
		"Save this objective to start recording changes."
	);
});

test("stale history responses cannot replace another objective and failed loads can retry", async ({
	page,
}) => {
	let held;
	let began;
	const requested = new Promise((resolve) => {
		began = resolve;
	});
	await page.route(`**/api/method/${method}**`, async (request) => {
		const response = await request.fetch();
		began();
		await new Promise((resolve) => {
			held = resolve;
		});
		await request.fulfill({ response });
	});
	await page.goto(route);
	await requested;
	await page.getByRole("link", { name: "Home", exact: true }).click();
	await expect(page).toHaveURL(/\/desk\/task-list$/);
	held();
	await expect(page.getByRole("link", { name: "Objectives", exact: true })).toBeVisible();
	await page.unroute(`**/api/method/${method}**`);
	await page.route(`**/api/method/${method}**`, (request) => request.abort());
	await page.goto(route);
	const changes = page.getByRole("tabpanel", { name: "Changes" });
	await expect(changes.getByRole("button", { name: "Retry", exact: true })).toBeVisible();
	await page.unroute(`**/api/method/${method}**`);
	await changes.getByRole("button", { name: "Retry", exact: true }).click();
	await expect(changes.locator(".history-save-label")).toContainText("Save 2 of 2");
});

test("loading older saves preserves the selected save and extends the slider", async ({
	page,
}) => {
	await page.route(`**/api/method/${method}**`, async (request) => {
		const url = new URL(request.request().url());
		const response = await request.fetch();
		if (url.searchParams.get("offset") === "0") {
			const body = await response.json();
			body.message.versions = body.message.versions.slice(0, 1);
			body.message.next_offset = 1;
			body.message.has_more = true;
			await request.fulfill({ response, json: body });
		} else {
			await request.fulfill({ response });
		}
	});
	await page.goto(route);
	const changes = page.getByRole("tabpanel", { name: "Changes" });
	await expect(changes.locator(".history-save-label")).toContainText("Save 1 of 1");
	await changes.getByRole("button", { name: "Load older saves", exact: true }).click();
	await expect(changes.locator(".history-save-label")).toContainText("Save 2 of 2");
	await expect(
		changes.locator('.history-field[data-history-field="team"] .history-after')
	).toHaveText("After: Current Team");
	await changes.getByRole("button", { name: "Earlier save" }).click();
	await expect(changes.locator(".history-row-added")).toContainText("Temporary task");
});
