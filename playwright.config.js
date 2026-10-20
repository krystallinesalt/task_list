const { defineConfig } = require("@playwright/test");

module.exports = defineConfig({
	testDir: "./e2e",
	workers: 1,
	forbidOnly: Boolean(process.env.CI),
	retries: 0,
	timeout: 60000,
	expect: { timeout: 15000 },
	use: {
		baseURL: process.env.BASE_URL || "http://task-list-test.localhost:8001",
		screenshot: "only-on-failure",
		trace: "retain-on-failure",
	},
});
