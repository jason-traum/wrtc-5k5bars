# 5K 5 Bars

The race-day app for the Beer Club × WRTC (Wharton Run & Tri Club) bar crawl: about 1 km runs between five bars, from Rittenhouse Square to Morgan's Pier. Runners join with their bib and first name. They tap Start, tap "I'm at <bar>" when they walk in (checked against the phone's location), and tap "Leaving <bar>" when they walk out. The leaderboard ranks everyone by running pace, and time at the bars never counts.

One HTML file, no build step. Hosted on GitHub Pages, with data in its own Supabase project.

Live: https://jason-traum.github.io/wrtc-5k5bars/ (organizers: add `?organizer` or `#organizer`). Supabase project: `wrtc-5k5bars` (ref `gbvovnaxcgcvtevzskyv`).

## Files

| File | What it is |
| --- | --- |
| `index.html` | The whole app. Loads `config.js`; without it the app runs in demo mode with sample runners. |
| `config.example.js` | Copy to `config.js` and fill in the Supabase URL and **publishable** key. Never a secret key. |
| `supabase.sql` | The database: tables, access rules, and every write as a checked function. Safe to run again. |
| `sw.js`, `manifest.json`, icons | Home Screen app and offline support. |
| `PRODUCT.md`, `DESIGN.md`, `STATES.md`, `DECISIONS.md` | Who it's for, the look, every screen state, and why things are the way they are. Read before changing the UI. |
| `build.py` | Makes `dist/site/` (what Pages serves) and `dist/preview.html` (the demo preview). |
| `tests/` | `live.py` (smoke test against the live site: join, database rules, tap and undo; leaves bib 299 to release), `shots.py` (screens at 320 to 390 px, light and dark, iPhone and Android), `test_db.py` (the database rules as anonymous runners and organizers), `firstload.py` (a brand-new phone joining against a mocked Supabase). |

## Run the tests

```
python3 build.py
python3 -m http.server 8765 &          # from this folder
python3 tests/shots.py                 # expects "PROBLEMS: none"
python3 tests/firstload.py             # expects "FIRST LOAD PROBLEMS: none"
# database: a throwaway Postgres 16 at /var/tmp/pg5k, port 5499
su postgres -c "/usr/lib/postgresql/16/bin/pg_ctl -D /var/tmp/pg5k/data -o '-p 5499 -k /var/tmp/pg5k' start"
python3 tests/test_db.py               # expects "0 failed"
```

## Go live

Supabase (a new project, not In.'s):

1. Create the project (region: East US). Save the database password in a password manager; the app never needs it.
2. **Authentication > Sign In / Providers**: turn on **Allow anonymous sign-ins**. Leave Email on with **Confirm email** on.
3. **Authentication > Rate Limits**: raise anonymous sign-ins per hour to about 300. Phones on the same Wi-Fi or carrier share an IP, and the default of 30 per hour could lock people out at the start line.
4. **Authentication > Users > Add user > Create new user**: add each organizer's email with **Auto Confirm** on and a long random password you throw away. Organizers sign in with an emailed code, and the app never creates accounts itself.
5. Organizers get a sign-in link by email (Supabase's built-in email can't be edited). With custom SMTP you can add the code to the Magic Link template (`{{ .Token }}`); the app accepts either.
6. Supabase's built-in email only sends to members of the project's team. Either invite the other organizers to the Supabase team, or set up custom SMTP (the way In. uses Gmail SMTP).
7. **SQL Editor > New query**: paste `supabase.sql`, put the organizer email where it says `YOUR_EMAIL_HERE`, and click Run.
8. **Project Settings > API Keys**: copy the project URL and the publishable key into `config.js`.
9. **Authentication > URL Configuration**: set Site URL to the GitHub Pages address.

GitHub:

10. Create a new repository, push this folder, and turn on **Settings > Pages** from the `main` branch root. `config.js` is committed; it holds only the publishable key, which is meant to be public, and the database rules are what protect the data.

Testing location (do this on your own phone):

- Open the app, join with a spare bib, and tap **Test my location** on the start screen. It should say "Location works" with an accuracy under about 50 m. If it says blocked or blurry, follow the steps it shows.
- To test the real check-in: sign in at `?organizer`, pick a bar, walk there, and tap **Test a check-in at <bar>**. It says whether a check-in would count and how far off the circle is. Adjust the radius if needed.
- For a dry run on your own, tap **Start a practice run** on the start screen (shown until 6 hours before the start). It opens the start on that phone only; **End practice** clears that phone's check-ins.
- For a full group dry run: press GO, tap Start, check in and out, then **After a practice run > Clear all check-ins** and release the spare bibs.
- To show someone the app without touching real data, send `?demo`: https://jason-traum.github.io/wrtc-5k5bars/?demo (sample runners, simulated location, nothing saved).

Before race day:

11. Open the site on your phone, join with your bib, sign in at `#organizer`, set the date, start time, Bar 4 and the leave-by times, and walk to a bar to check "Use my location" and the check-in radius.
12. Do a practice run with a few friends, then use **After a practice run > Clear all check-ins**.
