"""Runs supabase.sql against a local Postgres with a Supabase stand-in, then checks every rule as the
roles Supabase uses: anon (no sign-in), authenticated runners (anonymous sign-in), and an organizer.

Usage: python3 tests/test_db.py   (needs a Postgres at PGHOST/PGPORT; see the start command below)
  su postgres -c "/usr/lib/postgresql/16/bin/pg_ctl -D /var/tmp/pg5k/data -o '-p 5499 -k /var/tmp/pg5k' start"
"""
import json, os, sys, uuid
import psycopg2

HOST, PORT = os.environ.get("PGHOST", "/var/tmp/pg5k"), int(os.environ.get("PGPORT", "5499"))
HERE = os.path.dirname(os.path.abspath(__file__))
ADMIN = "Jason@Example.com"
fails, passes = [], 0


def connect(db):
    c = psycopg2.connect(host=HOST, port=PORT, user="postgres", dbname=db)
    c.autocommit = True
    return c


root = connect("postgres")
root.cursor().execute("drop database if exists race_test")
root.cursor().execute("create database race_test")
db = connect("race_test")
cur = db.cursor()
cur.execute(open(os.path.join(HERE, "supabase_stub.sql")).read())
schema = open(os.path.join(HERE, "..", "supabase.sql")).read().replace("YOUR_EMAIL_HERE", ADMIN)
cur.execute(schema)
cur.execute(schema)  # the file says it is safe to run again


def check(name, ok, detail=""):
    global passes
    if ok:
        passes += 1
    else:
        fails.append(f"{name} {detail}")


def users():
    ids = {k: str(uuid.uuid4()) for k in ["a", "b", "c", "d", "admin", "fake", "orgnobody", "pw", "unconfirmed"]}
    emails = {"admin": ADMIN, "pw": ADMIN.upper(), "unconfirmed": ADMIN, "orgnobody": "someone@example.com"}
    for k, v in ids.items():
        real = k in emails
        cur.execute("insert into auth.users (id, email, email_confirmed_at, is_anonymous) values (%s, %s, %s, %s)",
                    (v, emails.get(k), None if k == "unconfirmed" or not real else "2026-09-01", not real))
    return ids


U = users()


def claims(who):
    if who == "anon":
        return None
    otp = [{"method": "otp", "timestamp": 1790000000}]
    if who == "admin":
        return {"sub": U["admin"], "role": "authenticated", "email": ADMIN.lower(), "is_anonymous": False, "amr": otp}
    if who == "pw":  # a password account with the organizer's address (made where the address was free)
        return {"sub": U["pw"], "role": "authenticated", "email": ADMIN.lower(), "is_anonymous": False, "amr": [{"method": "password", "timestamp": 1}]}
    if who == "unconfirmed":  # organizer address never confirmed
        return {"sub": U["unconfirmed"], "role": "authenticated", "email": ADMIN.lower(), "is_anonymous": False, "amr": otp}
    if who == "fake":  # an anonymous phone that puts the organizer's email in its token
        return {"sub": U["fake"], "role": "authenticated", "email": ADMIN.lower(), "is_anonymous": True}
    if who == "orgnobody":  # a real email sign-in that is not on the organizer list
        return {"sub": U["orgnobody"], "role": "authenticated", "email": "someone@example.com", "is_anonymous": False, "amr": otp}
    return {"sub": U[who], "role": "authenticated", "is_anonymous": True}


def run(who, sql, args=()):
    """Run one statement as a Supabase role in its own transaction. Returns (rows, error message)."""
    c = psycopg2.connect(host=HOST, port=PORT, user="postgres", dbname="race_test")
    k = c.cursor()
    try:
        k.execute("set local role " + ("anon" if who == "anon" else "authenticated"))
        k.execute("select set_config('request.jwt.claims', %s, true)", (json.dumps(claims(who) or {}),))
        k.execute(sql, args)
        rows = k.fetchall() if k.description else []
        c.commit()
        return rows, None
    except Exception as e:
        c.rollback()
        return None, str(e).split("\n")[0]
    finally:
        c.close()


def expect_err(name, who, sql, args=(), contains=""):
    rows, err = run(who, sql, args)
    check(name, err is not None and contains.lower() in err.lower(), f"-> rows={rows} err={err}")


def expect_ok(name, who, sql, args=()):
    rows, err = run(who, sql, args)
    check(name, err is None, f"-> err={err}")
    return rows


def tap(who, stop, kind, at="now()", tid=None, verified=True, source="gps"):
    tid = tid or str(uuid.uuid4())
    return tid, run(who, f"select id, verified, source, at from add_tap(%s, %s, %s, {at}, %s, 40, 20, %s)", (tid, stop, kind, verified, source))


# --- Not signed in ---------------------------------------------------------------------------
for t in ["runners", "taps", "admins"]:
    expect_err(f"anon cannot read {t}", "anon", f"select * from public.{t}", contains="permission denied")
for t in ["stops", "event"]:
    expect_ok(f"anon can read the public {t}", "anon", f"select * from public.{t}")
expect_err("anon cannot write stops", "anon", "update public.stops set lat = 40", contains="permission denied")
expect_err("anon cannot claim a bib", "anon", "select * from claim_bib(5, 'Sam')", contains="permission denied")
cur.execute("""select p.proname from pg_proc p join pg_namespace n on n.oid = p.pronamespace
               where n.nspname = 'public' and has_function_privilege('anon', p.oid, 'execute')""")
check("anon can execute no public function", cur.fetchall() == [], "")
expect_err("anon cannot hide anyone", "anon", "select set_show(false)", contains="permission denied")

# --- Joining ---------------------------------------------------------------------------------
rows = expect_ok("A claims bib 12 as Dev", "a", "select * from claim_bib(12, 'Dev')")
dev_id = rows[0][0] if rows else None
check("my_runner is Dev on A", run("a", "select bib, name from my_runner()")[0] == [(12, "Dev")])
expect_err("B cannot take bib 12 with another name", "b", "select * from claim_bib(12, 'Alex')", contains="already Dev's")
expect_ok("B takes bib 12 with the same name (new phone)", "b", "select * from claim_bib(12, '  dev ')")
check("bib moved to B", run("b", "select id from my_runner()")[0] == [(dev_id,)] and run("a", "select id from my_runner()")[0] == [])
rows = expect_ok("A joins as Jason 23", "a", "select * from claim_bib(23, 'Jason')")
jason_id = rows[0][0] if rows else None
rows = expect_ok("A fixes a typo to 24", "a", "select * from claim_bib(24, 'Jason')")
check("typo fix keeps the same runner", rows and rows[0][0] == jason_id and rows[0][1] == 24, f"{rows}")
run("a", "select * from claim_bib(23, 'Jason')")
expect_err("bib 0 rejected", "c", "select * from claim_bib(0, 'Sam')", contains="1 to 300")
expect_err("bib 301 rejected", "c", "select * from claim_bib(301, 'Sam')", contains="1 to 300")
expect_err("blank name rejected", "c", "select * from claim_bib(7, '   ')", contains="first name")
rows = expect_ok("long name trimmed", "c", "select name from claim_bib(7, %s)", ("X" * 40,))
check("name cut to 24", rows and len(rows[0][0]) == 24, f"{rows}")
run("c", "select * from claim_bib(7, 'Priya')")  # C was Xxxx; rename by claiming again
check("C renamed to Priya via re-claim", run("c", "select name from my_runner()")[0] == [("Priya",)], str(run("c", "select name from my_runner()")))
expect_err("name over 60 characters refused before any work", "d", "select * from claim_bib(9, %s)", ("x" * 5000,), contains="first name")
expect_err("direction-flipping characters refused", "d", "select * from claim_bib(9, %s)", ("Sam\u202e",), contains="plain letters")
expect_err("zero-width characters refused", "d", "select * from claim_bib(9, %s)", ("S\u200bam",), contains="plain letters")
rows = expect_ok("accents are fine", "d", "select name from claim_bib(9, 'Inés')")
check("accented name kept", rows == [("Inés",)], f"{rows}")
run("d", "select * from claim_bib(10, 'Leo')")
cur.execute("select count(*) from runners where bib = 9")
check("switching bibs on one phone with no check-ins drops the old bib", cur.fetchone()[0] == 0)
cur.execute("delete from runners where bib = 10")

# --- Reading ---------------------------------------------------------------------------------
expect_err("runner cannot read auth_uid", "a", "select auth_uid from runners", contains="permission denied")
expect_err("runner cannot select * from runners", "a", "select * from runners", contains="permission denied")
rows = expect_ok("runner reads the public runner columns", "a", "select id, bib, name, created_at from runners")
check("sees all 3 runners", rows is not None and len(rows) == 3, f"{rows}")
expect_ok("runner reads stops", "a", "select * from stops")
expect_ok("runner reads event", "a", "select * from event")
expect_err("runner cannot read admins", "a", "select * from admins", contains="permission denied")
for col in ["dist_m", "acc_m"]:
    cur.execute(f"select has_column_privilege('authenticated', 'public.taps', '{col}', 'SELECT')")
    check(f"runners cannot read other people's {col}", cur.fetchone()[0] is False)
expect_err("select * from taps is refused", "a", "select * from taps", contains="permission denied")
expect_ok("tap columns the app uses are readable", "a", "select id, runner_id, stop, kind, at, verified, source, created_at from taps")
cur.execute("select has_column_privilege('authenticated', 'public.runners', 'auth_uid', 'SELECT')")
check("realtime cannot send auth_uid (no column privilege)", cur.fetchone()[0] is False)

# --- Direct writes are closed ----------------------------------------------------------------
expect_err("no direct tap insert", "a", "insert into taps (id, runner_id, stop, kind, at) values (gen_random_uuid(), %s, 1, 'arrive', now())", (jason_id,), contains="permission denied")
expect_err("no direct runner update", "a", "update runners set name = 'Hacked'", contains="permission denied")
expect_err("no direct runner delete", "a", "delete from runners", contains="permission denied")
expect_err("no direct stop update", "a", "update stops set lat = 40", contains="permission denied")
expect_err("no direct event update", "a", "update event set go_at = now()", contains="permission denied")
expect_err("no admin self-insert", "a", "insert into admins values ('me@x.com')", contains="permission denied")

# --- Taps ------------------------------------------------------------------------------------
t1, (rows, err) = tap("a", 1, "arrive")
check("A arrives at bar 1", err is None and rows and rows[0][1] is True and rows[0][2] == "gps", f"{rows} {err}")
expect_err("once checked in, the bib can't be taken with the leaderboard name", "d", "select * from claim_bib(23, 'jason')", contains="another phone")
check("A still has bib 23", run("a", "select bib from my_runner()")[0] == [(23,)])
_, (rows2, err2) = tap("a", 1, "arrive", tid=t1)
check("same tap sent twice (offline retry) is fine", err2 is None and rows2 and str(rows2[0][0]) == t1, f"{rows2} {err2}")
_, (rows, err) = tap("a", 1, "arrive")
check("second different arrive at bar 1 says already tapped", err and "already tapped" in err, f"{err}")
_, (rows, err) = tap("a", 0, "leave")
check("runner taps Start (leave stop 0)", err is None and rows, f"{rows} {err}")
for stop, kind, why in [(0, "arrive", "arrive at the start"), (-1, "leave", "before the start"), (5, "leave", "leave the finish"), (6, "arrive", "past the finish"), (1, "sit", "bad kind")]:
    _, (rows, err) = tap("a", stop, kind)
    check(f"tap rejected: {why}", err and "not on the course" in err, f"{rows} {err}")
_, (rows, err) = tap("a", 1, "leave", source="organizer")
check("runner cannot claim organizer source", err is None and rows[0][2] == "anyway" and rows[0][1] is False, f"{rows} {err}")
_, (rows, err) = tap("a", 2, "arrive", verified=True, source="anyway")
check("check in anyway is never verified", err is None and rows[0][1] is False, f"{rows} {err}")
_, (rows, err) = tap("a", 2, "leave", at="now() + interval '2 hours'")
cur.execute("select extract(epoch from (%s::timestamptz - now()))", (rows[0][3] if rows else None,))
check("future time clamped to a minute", err is None and cur.fetchone()[0] <= 61, f"{rows} {err}")
tp, (rows, err) = tap("b", 1, "arrive", at="now() - interval '2 days'")
check("practice-run tap days early is allowed (organizer clears later)", err is None, f"{err}")
run("b", "select undo_tap(%s)", (tp,))
_, (rows, err) = tap("fake", 1, "arrive")
check("phone with no bib cannot tap", err and "no runner" in err, f"{err}")

# --- Undo ------------------------------------------------------------------------------------
tb, _ = tap("b", 1, "arrive")
run("a", "select undo_tap(%s)", (tb,))
cur.execute("select count(*) from taps where id = %s", (tb,))
check("A cannot undo B's tap", cur.fetchone()[0] == 1)
run("b", "select undo_tap(%s)", (tb,))
cur.execute("select count(*) from taps where id = %s", (tb,))
check("B undoes own tap", cur.fetchone()[0] == 0)
cur.execute("update taps set created_at = now() - interval '11 minutes' where id = %s", (t1,))
run("a", "select undo_tap(%s)", (t1,))
cur.execute("select count(*) from taps where id = %s", (t1,))
check("undo closes after 10 minutes", cur.fetchone()[0] == 1)

# --- Organizer -------------------------------------------------------------------------------
check("runner is not admin", run("a", "select is_admin()")[0] == [(False,)])
check("anonymous phone with the organizer email is not admin", run("fake", "select is_admin()")[0] == [(False,)])
check("email not on the list is not admin", run("orgnobody", "select is_admin()")[0] == [(False,)])
check("organizer is admin (email case ignored)", run("admin", "select is_admin()")[0] == [(True,)])
check("password sign-in with the organizer address is not admin", run("pw", "select is_admin()")[0] == [(False,)])
check("unconfirmed organizer address is not admin", run("unconfirmed", "select is_admin()")[0] == [(False,)])
for who in ["a", "fake", "orgnobody", "pw"]:
    expect_err(f"{who} cannot GO", who, "select set_go(now())", contains="organizers only")
    expect_err(f"{who} cannot move the start", who, "select admin_save_event(now())", contains="organizers only")
    expect_err(f"{who} cannot delete taps", who, "select admin_delete_tap(%s)", (t1,), contains="organizers only")
    expect_err(f"{who} cannot remove runners", who, "select admin_remove_runner(%s)", (dev_id,), contains="organizers only")
    expect_err(f"{who} cannot edit the course", who, "select admin_save_route('[]'::jsonb)", contains="organizers only")
    expect_err(f"{who} cannot clear check-ins", who, "select admin_clear_taps()", contains="organizers only")
for who in ["a", "fake", "orgnobody", "pw"]:
    expect_err(f"{who} cannot unlock a bib", who, "select admin_unlock_runner(%s)", (jason_id,), contains="organizers only")
expect_ok("organizer unlocks bib 23", "admin", "select admin_unlock_runner(%s)", (jason_id,))
rows = expect_ok("new phone takes bib 23 after unlock", "d", "select id from claim_bib(23, 'Jason')")
check("same runner, taps kept", rows == [(jason_id,)] and run("d", "select count(*) from taps where runner_id = %s", (jason_id,))[0] != [(0,)], f"{rows}")
run("admin", "select admin_unlock_runner(%s)", (jason_id,)); run("a", "select * from claim_bib(23, 'Jason')")
check("bib 23 back on phone A", run("a", "select bib from my_runner()")[0] == [(23,)])
expect_ok("organizer GO", "admin", "select set_go(now())")
cur.execute("select go_at is not null from event")
check("GO saved", cur.fetchone()[0] is True)
expect_ok("organizer undo GO", "admin", "select set_go(null)")
expect_ok("organizer moves start", "admin", "select admin_save_event('2026-10-10 14:00-04')")


def route(n, lat_shift=0.0):
    cur.execute("select coalesce(json_agg(row_to_json(s) order by ord), '[]') from stops s")
    cur_stops = cur.fetchone()[0]
    out = []
    for i in range(n):
        s = dict(cur_stops[min(i, len(cur_stops) - 1)])
        s["ord"] = i
        s["lat"] = s["lat"] + lat_shift
        s["leave_by"] = "2026-10-10T15:00:00-04:00"
        out.append(s)
    return json.dumps(out)


run("admin", "select set_go(now())")
expect_err("adding a bar locked once the race is on", "admin", "select admin_save_route(%s::jsonb)", (route(7),), contains="locked")
expect_ok("moving pins allowed once taps exist", "admin", "select admin_save_route(%s::jsonb)", (route(6, 0.0001),))
cur.execute("select count(*), count(leave_by), max(ord) from stops")
check("6 stops, finish has no leave-by", cur.fetchone() == (6, 5, 5))
expect_err("pin outside Philly rejected", "admin", "select admin_save_route(%s::jsonb)", (route(6, 1.0),), contains="stops_lat_check")
expect_ok("organizer removes a tap", "admin", "select admin_delete_tap(%s)", (t1,))
expect_ok("organizer releases a bib", "admin", "select admin_remove_runner(%s)", (jason_id,))
cur.execute("select count(*) from taps where runner_id = %s", (jason_id,))
check("released bib's taps go with it", cur.fetchone()[0] == 0)
run("admin", "select set_go(now())")
expect_ok("organizer clears all check-ins", "admin", "select admin_clear_taps()")
cur.execute("select (select count(*) from taps), (select go_at from event), (select count(*) from runners)")
check("clear wipes taps and GO, keeps runners", cur.fetchone() == (0, None, 2))
expect_ok("with no taps, bars can be removed", "admin", "select admin_save_route(%s::jsonb)", (route(4),))
cur.execute("select count(*), max(ord) from stops")
check("course is now 4 stops", cur.fetchone() == (4, 3))
expect_err("a course needs 2+ stops", "admin", "select admin_save_route(%s::jsonb)", (route(1),), contains="start, a finish")

# --- Hiding from the leaderboard -----------------------------------------------------------------
dev = run("b", "select id from my_runner()")[0][0][0]
tb2, _ = tap("b", 1, "arrive")
expect_ok("B hides from the leaderboard", "b", "select set_show(false)")
check("my_runner reports hidden", run("b", "select hidden from my_runner()")[0] == [(True,)])
check("others can't see a hidden runner", run("c", "select count(*) from runners where id = %s", (dev,))[0] == [(0,)])
check("others can't see a hidden runner's taps", run("c", "select count(*) from taps where runner_id = %s", (dev,))[0] == [(0,)])
check("hidden runner still sees self", run("b", "select count(*) from runners where id = %s", (dev,))[0] == [(1,)])
check("hidden runner still sees own taps", run("b", "select count(*) from taps where runner_id = %s", (dev,))[0] == [(1,)])
check("organizer sees hidden runners", run("admin", "select count(*) from runners where id = %s", (dev,))[0] == [(1,)])
check("organizer sees hidden taps", run("admin", "select count(*) from taps where runner_id = %s", (dev,))[0] == [(1,)])
run("c", "select set_show(false)"); run("c", "select set_show(true)")
check("C's own toggle didn't touch B", run("b", "select hidden from my_runner()")[0] == [(True,)])
expect_ok("B shows again", "b", "select set_show(true)")
check("visible again to others", run("c", "select count(*) from runners where id = %s", (dev,))[0] == [(1,)])

# --- Practice runs ---------------------------------------------------------------------------------
cur.execute("update event set go_at = null, start_at = now() + interval '5 days'")
tap("b", 0, "leave"); tap("b", 1, "arrive"); tap("c", 0, "leave")
expect_ok("runner clears own practice check-ins before race day", "b", "select clear_my_practice()")
check("only B's taps went", run("admin", "select count(*) from taps where runner_id = %s", (dev,))[0] == [(0,)] and run("admin", "select count(*) from taps")[0] != [(0,)])
expect_err("anon cannot clear practice", "anon", "select clear_my_practice()", contains="permission denied")
cur.execute("update event set go_at = now()")
expect_err("no clearing once the race has opened", "c", "select clear_my_practice()", contains="race is on")
cur.execute("update event set go_at = null, start_at = now() + interval '1 hour'")
expect_err("no clearing within 2 hours of the start", "c", "select clear_my_practice()", contains="race is on")

# --- Setup -----------------------------------------------------------------------------------
cur.execute("select array_agg(tablename::text order by tablename) from pg_publication_tables where pubname = 'supabase_realtime'")
check("realtime on event, runners, stops, taps", cur.fetchone()[0] == ["event", "runners", "stops", "taps"])
cur.execute("select count(*) from admins")
check("running the file twice adds no duplicate organizer", cur.fetchone()[0] == 1)
cur.execute("""select p.proname from pg_proc p join pg_namespace n on n.oid = p.pronamespace
               where n.nspname = 'public' and p.prosecdef and not exists (select 1 from unnest(p.proconfig) c where c like 'search_path=%')""")
check("every definer function pins search_path", cur.fetchall() == [])

print(f"{passes} passed, {len(fails)} failed")
for f in fails:
    print("FAIL", f)
sys.exit(1 if fails else 0)
