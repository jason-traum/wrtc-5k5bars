import asyncio, sys
from playwright.async_api import async_playwright
URL = "http://localhost:8765/index.html"
OUT = "tests/out/"
import os; os.makedirs(OUT, exist_ok=True)
async def scene(pg, name):
    await pg.click("text=Preview"); await pg.click(f"dialog >> text={name}")
    await pg.wait_for_timeout(250)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        problems = []
        IPHONE = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Mobile/15E148 Safari/604.1"
        ANDROID = "Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36"
        for scheme, w, ua in [("light",390,IPHONE),("dark",390,ANDROID),("dark",320,IPHONE),("light",375,ANDROID)]:
            ctx = await b.new_context(viewport={"width":w,"height":844}, device_scale_factor=2, color_scheme=scheme, is_mobile=True, has_touch=True, timezone_id="America/New_York", user_agent=ua)
            pg = await ctx.new_page()
            errs = []
            pg.on("pageerror", lambda e: errs.append("pageerror: "+str(e)))
            pg.on("console", lambda m: errs.append("console: "+m.text) if m.type=="error" and "manifest" not in m.text and "apple-touch" not in m.text and "favicon" not in m.text else None)
            await pg.route("**/htm@3.1.1/preact/standalone.umd.js", lambda r: r.fulfill(path="tests/vendor/htm-preact-standalone.js", content_type="application/javascript"))
            await pg.route("**/config.js", lambda r: r.fulfill(body="/* no config: demo mode */", content_type="application/javascript"))
            await pg.route("**/maplibre-gl/5.7.0/maplibre-gl.min.js", lambda r: r.fulfill(path="tests/vendor/maplibre-gl-5.7.0.js", content_type="application/javascript"))
            await pg.goto(URL); await pg.wait_for_selector(".big")
            tag = f"{scheme}-{w}"
            async def shot(n):
                ov = await pg.evaluate("document.documentElement.scrollWidth > window.innerWidth")
                if ov: problems.append(f"overflow {tag} {n}")
                await pg.screenshot(path=f"{OUT}{n}-{tag}.png", full_page=True)
            await shot("race")
            href = await pg.get_attribute("a:has-text('Directions')", "href")
            want = "maps.apple.com/?daddr=" if ua == IPHONE else "google.com/maps/dir/?api=1&destination="
            if want not in href or not ("dirflg=w" in href or "travelmode=walking" in href): problems.append(f"directions {tag}: {href}")
            if w == 390:
                # far flow
                await pg.click("text=Preview"); await pg.click("dialog >> text=640 m away"); await pg.click("dialog >> text=Done")
                await pg.click(".big"); await pg.wait_for_selector(".alert"); await shot("far")
                # location off
                await pg.click("text=Preview"); await pg.click("dialog >> text=Location off"); await pg.click("dialog >> text=Done")
                await pg.click("text=Try again"); await pg.wait_for_timeout(900); await shot("off")
                # at the bar -> check in
                await pg.click("text=Preview"); await pg.click("dialog >> text=At the bar"); await pg.click("dialog >> text=Done")
                await pg.click("text=Try again"); await pg.wait_for_timeout(1400); await shot("atbar-after")
                await scene(pg, "At a bar"); await shot("atbar")
                await pg.click("text=Already at"); await pg.wait_for_timeout(200); await shot("already")
                await pg.click(".stripbtn"); await pg.wait_for_timeout(300); await pg.screenshot(path=f"{OUT}legs-{tag}.png")
                if not await pg.is_visible("dialog[aria-labelledby=mlh] >> text=Your legs"): problems.append(f"tracker did not open {tag}")
                await pg.click("dialog[aria-labelledby=mlh] >> text=Done"); await pg.wait_for_timeout(200)
                await scene(pg, "Running to a bar")
                await pg.click("text=Preview"); await pg.click("dialog >> text=No signal"); await pg.click("dialog >> text=Done")
                await pg.click(".big"); await pg.wait_for_timeout(1400); await shot("offline")
                await pg.click("text=Preview"); await pg.click("dialog >> button:has-text('Signal') >> nth=0"); await pg.click("dialog >> text=Done"); await pg.wait_for_timeout(600)
                await pg.click(".tabs >> text=Leaderboard"); await pg.wait_for_timeout(200); await shot("board")
                await pg.click(".lbrow >> nth=1"); await pg.wait_for_timeout(200); await shot("board-open")
                await pg.click(".tabs >> text=Race")
                await scene(pg, "Finished"); await pg.wait_for_timeout(450); await pg.screenshot(path=f"{OUT}celebrate-{tag}.png")
                if not await pg.is_visible(".cele"): problems.append(f"no finish moment {tag}")
                await pg.wait_for_timeout(2600)
                if await pg.is_visible(".cele"): problems.append(f"finish moment did not close {tag}")
                await shot("finished")
                await pg.click(".medalbtn"); await pg.wait_for_timeout(300)
                if not await pg.is_visible(".cele"): problems.append(f"medal replay failed {tag}")
                await pg.click(".cele"); await pg.wait_for_timeout(400)
                if await pg.is_visible(".cele"): problems.append(f"tap to skip failed {tag}")
                await scene(pg, "Before the start"); await shot("pre")
                await scene(pg, "Start is open"); await shot("ready")
                await pg.click(".big"); await pg.wait_for_timeout(1400); await shot("ready-after")
                txt = (await pg.inner_text("main")).upper()
                if "I'M AT PHS GARDEN" not in txt: problems.append(f"start tap did not move on {tag}: {txt[:120]}")
                # the map tab: real streets, tap a bar for details
                await pg.click(".tabs >> text=Map"); await pg.wait_for_selector(".pin", timeout=15000); await pg.wait_for_timeout(3500); await shot("map")
                await pg.click(".pin >> nth=2"); await pg.wait_for_timeout(500)
                pop = await pg.inner_text(".maplibregl-popup") if await pg.is_visible(".maplibregl-popup") else ""
                if "Apple Maps" not in pop or "Google Maps" not in pop: problems.append(f"bar popup missing links {tag}: {pop[:80]}")
                await shot("map-pop")
                await pg.click("text=Where am I"); await pg.wait_for_timeout(1500)
                if not await pg.is_visible(".medot"): problems.append(f"where am I dot missing {tag}")
                await pg.click(".tabs >> text=Race")
                await pg.click("text=Preview"); await pg.click("dialog >> text=Open the organizer view"); await pg.wait_for_selector(".pin", timeout=15000); await pg.wait_for_timeout(3000); await shot("organizer")
                await pg.click(".opts >> text=Bar 4"); await pg.fill("#gq", "Khyber Pass Pub"); await pg.click("form >> text=Search"); await pg.wait_for_timeout(3500)
                await shot("org-search")
                if await pg.locator(".geo-results button").count():
                    await pg.click(".geo-results button >> nth=0"); await pg.wait_for_timeout(600)
                    t = await pg.inner_text(".toast")
                    if "Moved" not in t: problems.append(f"search pick didn't move the bar {tag}: {t}")
                else: problems.append(f"no search results {tag}")
                await pg.click("text=Back to the race")
                await scene(pg, "Join screen"); await pg.wait_for_selector(".pin", timeout=15000); await pg.wait_for_timeout(3000); await shot("join")
                await pg.fill("#bib","12"); await pg.fill("#nm","Alex"); await pg.click("text=Join the race"); await pg.wait_for_timeout(700); await shot("join-taken")
            if errs: problems.append(f"{tag}: {errs[:5]}")
            await ctx.close()
        await b.close()
        print("PROBLEMS:", problems if problems else "none")
asyncio.run(main())
