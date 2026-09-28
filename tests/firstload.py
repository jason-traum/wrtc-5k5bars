"""First visit in cloud mode with a mocked Supabase: does the Race screen render right after joining?"""
import asyncio, base64, http.server, threading, functools, json, time
from playwright.async_api import async_playwright

PROJ = "/home/claude/wrtc-5k5bars"
HERE = PROJ
PORT = 8793
h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=PROJ + "/dist/site")
h.log_message = lambda *a, **k: None
srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), h)
threading.Thread(target=srv.serve_forever, daemon=True).start()
REF = "https://abcdefghijklmnopqrst.supabase.co"
b64 = lambda o: base64.urlsafe_b64encode(json.dumps(o).encode()).decode().rstrip("=")
TOKEN = b64({"alg": "HS256", "typ": "JWT"}) + "." + b64({"sub": "11111111-1111-4111-8111-111111111111", "role": "authenticated", "is_anonymous": True, "exp": int(time.time()) + 3600, "aud": "authenticated"}) + ".sig"
USER = {"id": "11111111-1111-4111-8111-111111111111", "aud": "authenticated", "role": "authenticated", "is_anonymous": True, "app_metadata": {}, "user_metadata": {}, "identities": [], "created_at": "2026-09-28T00:00:00Z"}
STOPS = [{"ord": i, "name": f"Bar {i}", "short": f"Bar {i}", "addr": "", "lat": 39.95, "lng": -75.16, "radius_m": 150, "km": 1.0 if i else 0, "leave_by": None} for i in range(6)]


async def api(route):
    req = route.request
    url, auth = req.url, req.headers.get("authorization", "")
    signed = TOKEN in auth
    if "/auth/v1/signup" in url:
        return await route.fulfill(status=200, content_type="application/json", body=json.dumps({"access_token": TOKEN, "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": USER}))
    if "/auth/v1/" in url:
        return await route.fulfill(status=200, content_type="application/json", body=json.dumps(USER))
    if "/rest/v1/" in url:
        public = "/rest/v1/event" in url or "/rest/v1/stops" in url  # the course and times are public
        if not signed and not public:
            return await route.fulfill(status=401, content_type="application/json", body=json.dumps({"code": "42501", "message": "permission denied for table event"}))
        if "rpc/claim_bib" in url:
            return await route.fulfill(status=200, content_type="application/json", body=json.dumps([{"id": "r1", "bib": 23, "name": "Jason"}]))
        body = {"event": [{"id": 1, "name": "x", "start_at": "2026-10-10T18:00:00Z", "go_at": None}], "stops": STOPS, "runners": [], "taps": []}
        for k, v in body.items():
            if f"/rest/v1/{k}" in url:
                if k == "event":
                    return await route.fulfill(status=200, content_type="application/vnd.pgrst.object+json", body=json.dumps(v[0]))
                return await route.fulfill(status=200, content_type="application/json", body=json.dumps(v))
        return await route.fulfill(status=200, content_type="application/json", body="null")
    await route.abort()


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page()
        errs, reqs = [], []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("request", lambda r: reqs.append((r.method, r.url.replace(REF, ""), "session" if TOKEN in r.headers.get("authorization", "") else "no session")) if REF in r.url else None)
        await pg.route("**/htm@3.1.1/preact/standalone.umd.js", lambda r: r.fulfill(path=f"{PROJ}/tests/vendor/htm-preact-standalone.js", content_type="application/javascript"))
        await pg.route("**/@supabase/supabase-js@2.117.2/dist/umd/supabase.js", lambda r: r.fulfill(path=f"{PROJ}/tests/vendor/supabase-2.117.2.js", content_type="application/javascript"))
        await pg.route("**/config.js", lambda r: r.fulfill(body=f"window.RACE_CONFIG={{supabaseUrl:'{REF}',supabaseKey:'sb_publishable_test'}};", content_type="application/javascript"))
        await pg.route("https://fonts.googleapis.com/**", lambda r: r.fulfill(body="", content_type="text/css"))
        await pg.route(f"{REF}/**", api)
        await pg.goto(f"http://127.0.0.1:{PORT}/index.html")
        await pg.wait_for_selector("#bib", timeout=15000)
        await pg.fill("#bib", "23"); await pg.fill("#nm", "Jason")
        await pg.click("button[type=submit]")
        await pg.wait_for_timeout(2500)
        screen = (await pg.inner_text("main")).replace("\n", " | ")
        before = [r for r in reqs if "/rest/v1/" in r[1] and r[2] == "no session" and "/rest/v1/event" not in r[1] and "/rest/v1/stops" not in r[1]]
        problems = []
        if errs: problems.append(f"page errors: {errs}")
        if "I'M AT" not in screen.upper() and "RITTENHOUSE" not in screen.upper() and "BAR 0" not in screen.upper(): problems.append(f"race screen not shown: {screen[:160]}")
        if before: problems.append(f"read runners or taps before signing in: {before}")
        print("FIRST LOAD PROBLEMS:", problems or "none")
        await b.close()
    srv.shutdown()

asyncio.run(main())
