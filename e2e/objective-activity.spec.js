const { test, expect } = require("@playwright/test");

const objectiveName = "_Test Task List Activity Browser";
const objectiveRoute = `/desk/tasklist-objective/${encodeURIComponent(objectiveName)}`;
const commentText = "Synthetic browser check: native activity comment.";

test.beforeEach(async ({ page }) => {
	if (!process.env.TASK_LIST_UI_PASSWORD) {
		throw new Error("Set TASK_LIST_UI_PASSWORD for the dedicated browser-test user.");
	}
	const login = await page.request.post("/api/method/login", {
		form: {
			usr: "task-list-browser@example.com",
			pwd: process.env.TASK_LIST_UI_PASSWORD,
		},
	});
	expect(login.ok()).toBeTruthy();
});

test("native activity anchor selects Activity on a fresh page", async ({ page }) => {
	const response = await page.request.get("/api/resource/Comment", {
		params: {
			filters: JSON.stringify({
				reference_doctype: "Tasklist Objective",
				reference_name: objectiveName,
				content: commentText,
			}),
			fields: JSON.stringify(["name"]),
		},
	});
	expect(response.ok()).toBeTruthy();
	const comments = (await response.json()).data;
	expect(comments).toHaveLength(1);
	// Timeline Copy link and comment notifications both use this native anchor.
	const anchor = `#comment-${comments[0].name}`;
	await page.goto(objectiveRoute + anchor);
	const activity = page.getByRole("tabpanel", { name: "Activity" });
	await expect(activity).toBeVisible();
	await expect(
		activity.locator(`${anchor} .content`).getByText(commentText, { exact: true })
	).toBeVisible();
	await expect(page).toHaveURL(new RegExp(`${anchor}$`));
	await expect(activity.locator(".form-footer")).toHaveCount(1);
	await page.reload();
	await expect(
		activity.locator(`${anchor} .content`).getByText(commentText, { exact: true })
	).toBeVisible();
	await expect(page).toHaveURL(new RegExp(`${anchor}$`));
	await page.getByRole("tab", { name: "Details", exact: true }).click();
	await expect(activity).toBeHidden();
	await page.getByRole("link", { name: "Home", exact: true }).click();
	await expect(page.getByRole("link", { name: "Objectives", exact: true })).toBeVisible();
	// Reproduce Frappe's native link/notification handler without reloading Desk.
	await page.evaluate(
		({ route, hash }) => {
			frappe.route_hash = hash;
			return frappe.set_route(route);
		},
		{ route: objectiveRoute, hash: anchor }
	);
	await expect(
		activity.locator(`${anchor} .content`).getByText(commentText, { exact: true })
	).toBeVisible();
	await expect(page).toHaveURL(new RegExp(`${anchor}$`));
});

test("native comments and history survive saves and repeated refreshes", async ({ page }) => {
	await page.goto(objectiveRoute);
	await page.getByRole("tab", { name: "Details", exact: true }).click();
	await page.locator('[data-fieldname="team"] input').fill("Browser QA Updated");
	await expect(page.getByText("Not Saved", { exact: true })).toBeVisible();
	await page.getByRole("button", { name: "Save", exact: true }).click();
	await expect(page.getByText("Not Saved", { exact: true })).toBeHidden();
	await page.getByRole("tab", { name: "Activity", exact: true }).click();
	const activity = page.getByRole("tabpanel", { name: "Activity" });
	await activity.locator(".show-all-activity input[type=checkbox]").check();
	await expect(activity.getByText(/changed the value of Team/)).toBeVisible();
	const editor = activity.locator(".comment-box .ql-editor");
	await editor.fill("Synthetic browser check after save.");
	await activity.getByRole("button", { name: "Comment", exact: true }).click();
	await expect(editor).toHaveText("");
	await page.reload();
	await expect(
		activity
			.locator(".timeline-message-box .content")
			.getByText("Synthetic browser check after save.", { exact: true })
	).toBeVisible();
	await expect(activity.locator(".form-footer")).toHaveCount(1);
	await page.getByRole("tab", { name: "Details", exact: true }).click();
	await expect(activity).toBeHidden();
});

test("new objectives show save-first guidance in Activity", async ({ page }) => {
	await page.goto("/desk/tasklist-objective");
	await page.getByRole("button", { name: "Add Tasklist Objective", exact: true }).click();
	await page.getByRole("tab", { name: "Activity", exact: true }).click();
	const activity = page.getByRole("tabpanel", { name: "Activity" });
	await expect(
		activity.getByText("Save this objective to add comments and view its history.")
	).toBeVisible();
	await expect(activity.locator(".comment-box")).toBeHidden();
});
