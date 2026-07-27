const { chromium } = require("playwright");

(async () => {
	const browser = await chromium.launch({ headless: false });
	const context = await browser.newContext();
	const page = await context.newPage();

	// Navigate to dev.to
	console.log("Navigating to dev.to...");
	await page.goto("https://dev.to/new");

	// Wait for page to load
	await page.waitForLoadState("networkidle");

	// Take screenshot to see current state
	await page.screenshot({ path: "devto-login.png" });
	console.log("Screenshot saved as devto-login.png");

	// Check if we need to login
	const isLoggedIn = (await page.locator('a[href="/dashboard"]').count()) > 0;

	if (!isLoggedIn) {
		console.log(
			"Not logged in. Please login manually and press Enter to continue...",
		);
		// In a real automation, we'd handle login here
		// For now, we'll wait for manual intervention
		await page.waitForTimeout(30000); // Wait 30 seconds for manual login
	}

	console.log("Ready to post!");

	// Close browser
	await browser.close();
})();
