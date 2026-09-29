"""The shareable demo (?demo): opens on the join screen with a sample bib and name, a short countdown after
joining, then every tap skips ahead in time so the whole race can be tapped through in about a minute.
Checks that the leaderboard ends up with a believable pace and rank.

Usage: python3 tests/demo.py   (with python3 -m http.server 8765 running in this folder)
"""
import asyncio, re
from playwright.async_api import async_playwright

URL = "http://localhost:8765/index.html?demo"
OUT = "tests/out/"


async def main():
    problems = []
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True, timezone_id="America/New_York")
        pg = await ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.route("**/htm@3.1.1/preact/standalone.umd.js", lambda r: r.fulfill(path="tests/vendor/htm-preact-standalone.js", content_type="application/javascript"))
        await pg.route("**/config.js", lambda r: r.fulfill(body="/* no config: demo mode */", content_type="application/javascript"))
        await pg.route("**/maplibre-gl/5.7.0/maplibre-gl.min.js", lambda r: r.fulfill(path="tests/vendor/maplibre-gl-5.7.0.js", content_type="application/javascript"))
        await pg.goto(URL)
        await pg.wait_for_selector("#bib", timeout=15000)
        if await pg.input_value("#bib") != "23" or not await pg.input_value("#nm"):
            problems.append("join screen isn't pre-filled")
        await pg.screenshot(path=f"{OUT}demo-join.png")

        await pg.click("text=Join the race")
        await pg.wait_for_selector("text=Start opens in", timeout=5000)
        await pg.screenshot(path=f"{OUT}demo-pre.png")
        await pg.wait_for_selector(".big >> text=Start", timeout=20000)

        await pg.click(".big")
        await pg.wait_for_selector(".big >> text=I'm at", timeout=5000)
        for i in range(1, 5):
            await pg.click(".big")
            await pg.wait_for_selector("text=Group leaves in", timeout=6000)
            if i == 1:
                toast = await pg.inner_text(".toast")
                if "skipped ahead" not in toast: problems.append(f"no skip-ahead note: {toast!r}")
                await pg.screenshot(path=f"{OUT}demo-atbar.png")
            await pg.wait_for_selector(".big >> text=Leaving", timeout=5000)
            await pg.click(".big")
            await pg.wait_for_selector(".big >> text=I'm at", timeout=6000)
        await pg.click(".big")
        await pg.wait_for_timeout(1800)
        await pg.screenshot(path=f"{OUT}demo-celebrate.png")
        await pg.wait_for_timeout(4000)
        fin = (await pg.inner_text("main")).replace("\n", " | ")
        await pg.screenshot(path=f"{OUT}demo-finished.png", full_page=True)
        m = re.search(r"(\d+)(st|nd|rd|th)[\s|]*of (\d+)", fin)
        if not m: problems.append(f"no rank on the finish screen: {fin[:200]}")
        else:
            rank, of = int(m.group(1)), int(m.group(3))
            if of < 10 or not (2 <= rank <= of - 2): problems.append(f"rank looks off: {m.group(0)}")

        await pg.click(".tabs >> text=Leaderboard"); await pg.wait_for_timeout(600)
        board = await pg.inner_text("main")
        paces = [int(a) * 60 + int(s) for a, s in re.findall(r"\b(\d{1,2}):(\d\d)\s*/mi", board)]
        if len(paces) < 10: problems.append(f"leaderboard has {len(paces)} paces")
        if any(x < 6 * 60 for x in paces): problems.append(f"an impossible pace on the board: {min(paces)}s/mi")
        await pg.screenshot(path=f"{OUT}demo-board.png", full_page=True)
        if errs: problems.append(f"page errors: {errs[:3]}")
        await b.close()
    print("DEMO PROBLEMS:", problems or "none")


asyncio.run(main())
