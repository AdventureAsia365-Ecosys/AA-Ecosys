// AA-818 S239: sign in to the Booking staff admin on booking.lumiguides.it.com and screenshot the Cases list.
// Credentials come from env U / P (read from Secrets Manager by the caller); never printed or saved.
import { chromium } from "/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/node_modules/playwright/index.mjs";

const out = new URL(".", import.meta.url).pathname;
const browser = await chromium.launch();
const result = {};
for (const [name, viewport] of [["1440", { width: 1440, height: 900 }], ["390", { width: 390, height: 844 }]]) {
  const page = await browser.newPage({ viewport });
  await page.goto("https://booking.lumiguides.it.com/login", { waitUntil: "networkidle" });
  await page.fill('input[name="username"], input[autocomplete="username"], input[type="text"]', process.env.U);
  await page.fill('input[type="password"]', process.env.P);
  await Promise.all([page.waitForURL((u) => !u.pathname.startsWith("/login"), { timeout: 30000 }), page.keyboard.press("Enter")]);
  await page.goto("https://booking.lumiguides.it.com/cases", { waitUntil: "networkidle" });
  await page.waitForTimeout(1500);
  const text = await page.locator("body").innerText();
  result[name] = {
    url: page.url(),
    case_refs_visible: [...new Set(text.match(/TC-\d{6}/g) || [])],
    no_h_scroll: await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth),
  };
  await page.screenshot({ path: `${out}booking-cases-${name}.png`, fullPage: false });
  await page.close();
}
await browser.close();
console.log(JSON.stringify(result, null, 1));
