"""CalTraX PRO smoke tests (headless Chromium).

Setup:   pip install playwright && playwright install chromium
Run:     python3 tests/smoke_test.py            (tests ../index.html)
         python3 tests/smoke_test.py path/to/index.html
Exit code 0 = all passed. Offline-safe: external CDNs are blocked on purpose.
"""
import asyncio, pathlib, sys
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
TARGET = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "index.html"
results = []

def check(name, ok, detail=""):
    results.append((name, bool(ok)))
    print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail and not ok else ""))

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--no-sandbox"])
        page = await browser.new_page(viewport={"width": 390, "height": 844})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        await page.route("**/*", lambda r: r.continue_() if r.request.url.startswith("file://") else r.abort())
        await page.goto(TARGET.as_uri()); await page.wait_for_timeout(800)

        # 1. Boot
        check("app boots with food database", await page.evaluate("typeof FOOD_DATABASE !== 'undefined' && FOOD_DATABASE.length > 200"))
        check("config loaded", await page.evaluate("!!window.CALTRAX_CONFIG"))

        # 2. Onboarding wizard
        overlay_visible = lambda: page.evaluate("getComputedStyle(document.getElementById('onboarding-overlay')).display !== 'none'")
        check("wizard shows on fresh install", await overlay_visible())
        await page.click("#btn-wz-next-1"); await page.fill("#wz-input-name", "Tester")
        await page.click("#btn-wz-next-2"); await page.click("#btn-wz-next-3"); await page.click("#btn-wz-finish")
        await page.wait_for_timeout(300)
        check("wizard closes on finish", not await overlay_visible())

        # 3. Food search: one whole-egg entry, no duplicates
        await page.click('nav button[data-tab="add"]'); await page.fill("#food-input-name", "egg"); await page.wait_for_timeout(200)
        names = await page.locator("#search-suggestions li p.font-bold").all_inner_texts()
        check("egg search returns results", len(names) > 0)
        check("whole boiled egg listed once", names.count("Whole Boiled Egg") == 1, str(names))

        # 4. One-tap favorite logs a food
        await page.click("#search-suggestions li >> nth=0") if False else None
        await page.evaluate("document.getElementById('search-suggestions').classList.add('hidden')")
        await page.locator("#quick-food-chips > div button").first.click(); await page.wait_for_timeout(200)
        check("one-tap favorite logs food", await page.locator("#tab-meals li.group").count() >= 1)

        # 5. Custom target: save a calorie goal and see it on the dashboard
        await page.click('nav button[data-tab="profile"]'); await page.wait_for_timeout(200)
        await page.fill("#tgt-cal", "1800")
        await page.click("#profile-form button[type=submit]"); await page.wait_for_timeout(300)
        await page.click('nav button[data-tab="home"]'); await page.wait_for_timeout(200)
        goal = (await page.inner_text("#stat-goal-cal")).replace(",", "")
        check("custom calorie target is used on dashboard", goal == "1800", f"goal={goal}")

        # 6. Out-of-range value is rejected, previous target kept
        await page.click('nav button[data-tab="profile"]'); await page.wait_for_timeout(200)
        await page.fill("#tgt-cal", "99999")
        await page.click("#profile-form button[type=submit]"); await page.wait_for_timeout(300)
        await page.click('nav button[data-tab="home"]'); await page.wait_for_timeout(200)
        goal = (await page.inner_text("#stat-goal-cal")).replace(",", "")
        check("out-of-range target rejected (kept 1800)", goal == "1800", f"goal={goal}")

        # 7. Reset returns to suggested target
        await page.click('nav button[data-tab="profile"]'); await page.wait_for_timeout(200)
        await page.click("#tgt-reset"); await page.wait_for_timeout(300)
        await page.click('nav button[data-tab="home"]'); await page.wait_for_timeout(200)
        goal = (await page.inner_text("#stat-goal-cal")).replace(",", "")
        check("reset restores suggested target", goal != "1800" and goal.isdigit(), f"goal={goal}")

        # 8. Sound engine present and mute toggle works
        check("sound engine loaded", await page.evaluate("!!window.Sound"))
        before = await page.evaluate("Sound.isEnabled()")
        await page.click("#sound-toggle-btn"); await page.wait_for_timeout(100)
        after = await page.evaluate("Sound.isEnabled()")
        check("sound mute toggle works", before != after)
        await page.click("#sound-toggle-btn")

        # 9. Language switch (3 languages)
        for code in ["bn", "hi", "en"]:
            await page.evaluate(f"setLanguage('{code}')")
        check("language switching runs for bn/hi/en", True)

        check("no uncaught page errors", not errors, "; ".join(errors[:3]))
        await browser.close()

asyncio.run(run())
passed = sum(ok for _, ok in results)
print(f"\n{passed}/{len(results)} passed")
sys.exit(0 if passed == len(results) else 1)
