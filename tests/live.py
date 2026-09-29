"""Smoke test against the LIVE site and Supabase project. Joins as a test bib, reads the race, taps Start
through the database, undoes it, and checks organizer-only calls are refused. Leaves one runner row
(bib 299 "Smoketest") for an organizer to release afterwards.

Usage: python3 tests/live.py [site-url]
"""
import asyncio, sys
from playwright.async_api import async_playwright

SITE = sys.argv[1] if len(sys.argv) > 1 else "https://jason-traum.github.io/wrtc-5k5bars/"
BIB, NAME = "299", "Smoketest"


async def main():
    problems = []
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True,
                                  timezone_id="America/New_York", geolocation={"latitude": 39.9437, "longitude": -75.1662},
                                  permissions=["geolocation"])
        pg = await ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        await pg.goto(SITE)
        await pg.wait_for_selector("#bib", timeout=20000)
        band = await pg.inner_text(".hero .band")
        print("join band:", band)
        await pg.fill("#bib", BIB); await pg.fill("#nm", NAME)
        await pg.click("button[type=submit]")
        await pg.wait_for_selector(".strip", timeout=20000)
        main_txt = (await pg.inner_text("main")).replace("\n", " | ")
        print("race screen:", main_txt[:200])
        if "RITTENHOUSE" not in main_txt.upper(): problems.append("race screen not at the start")
        chip = await pg.inner_text(".bibchip")
        if BIB not in chip: problems.append(f"bib chip wrong: {chip}")

        # talk to the database as this phone, the same way the app does
        res = await pg.evaluate("""async () => {
          const sb = window.supabase.createClient(window.RACE_CONFIG.supabaseUrl, window.RACE_CONFIG.supabaseKey);
          const out = {};
          const me = await sb.rpc('my_runner'); out.me = me.data;
          out.isAdmin = (await sb.rpc('is_admin')).data;
          out.go = (await sb.rpc('set_go', { p_at: new Date().toISOString() })).error?.message;
          out.clear = (await sb.rpc('admin_clear_taps')).error?.message;
          out.stops = (await sb.from('stops').select('ord,short').order('ord')).data?.map(s => s.short).join(' > ');
          out.readDist = (await sb.from('taps').select('dist_m')).error?.message;
          out.readUid = (await sb.from('runners').select('auth_uid')).error?.message;
          out.directInsert = (await sb.from('taps').insert({ id: crypto.randomUUID(), runner_id: me.data?.[0]?.id, stop: 1, kind: 'arrive', at: new Date().toISOString() })).error?.message;
          const id = crypto.randomUUID();
          const t = await sb.rpc('add_tap', { p_id: id, p_stop: 0, p_kind: 'leave', p_at: new Date().toISOString(), p_verified: true, p_dist: 0, p_acc: 10, p_source: 'gps' });
          out.tap = t.error ? t.error.message : 'ok';
          out.undo = (await sb.rpc('undo_tap', { p_id: id })).error?.message || 'ok';
          out.left = (await sb.from('taps').select('id').eq('id', id)).data?.length;
          out.hide = (await sb.rpc('set_show', { p_show: false })).error?.message || 'ok';
          out.hiddenNow = (await sb.rpc('my_runner')).data?.[0]?.hidden;
          out.show = (await sb.rpc('set_show', { p_show: true })).error?.message || 'ok';
          const anon = window.supabase.createClient(window.RACE_CONFIG.supabaseUrl, window.RACE_CONFIG.supabaseKey, { auth: { persistSession: false, storageKey: 'probe-anon' } });
          out.anonStops = (await anon.from('stops').select('ord')).data?.length;
          out.anonRunners = (await anon.from('runners').select('id')).error?.message;
          return out;
        }""")
        print("database:", res)
        if not res.get("me"): problems.append("my_runner empty after join")
        if res.get("isAdmin") is not False: problems.append("runner is admin?!")
        for k in ["go", "clear"]:
            if not res.get(k) or "organizers only" not in res[k]: problems.append(f"{k} not refused: {res.get(k)}")
        for k in ["readDist", "readUid", "directInsert"]:
            if not res.get(k) or "permission denied" not in res[k].lower(): problems.append(f"{k} not refused: {res.get(k)}")
        if res.get("tap") != "ok" or res.get("undo") != "ok" or res.get("left") != 0: problems.append("tap/undo failed")
        if res.get("hide") != "ok" or res.get("hiddenNow") is not True or res.get("show") != "ok": problems.append("hide/show failed")
        if not res.get("anonStops"): problems.append("course isn't public before joining")
        if not res.get("anonRunners") or "permission denied" not in res["anonRunners"].lower(): problems.append(f"anon read runners: {res.get('anonRunners')}")
        await pg.click(".tabs >> text=Map"); await pg.wait_for_selector(".pin", timeout=20000); await pg.wait_for_timeout(4000)
        await pg.screenshot(path="tests/out/live-map.png")

        await pg.click(".tabs >> text=Leaderboard"); await pg.wait_for_timeout(800)
        board = await pg.inner_text("main")
        if NAME not in board: problems.append("not on the leaderboard")
        if errs: problems.append(f"console/page errors: {errs[:3]}")
        await b.close()
    print("LIVE PROBLEMS:", problems or "none")


asyncio.run(main())
