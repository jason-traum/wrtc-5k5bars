# CLAUDE.md

Race-day app for WRTC 5K 5 Bars. People use it at a bar, a few drinks in, one thumb, loud room. Read PRODUCT.md, DESIGN.md, STATES.md and DECISIONS.md before any UI change, and add a dated line to DECISIONS.md for any product call.

## Rules that don't bend
- During the race the Race tab is the next place, one big button, and at a bar the leave countdown. No stats, no schedule. Numbers belong on the finish screen and behind a tap on the leaderboard.
- One accent (bib red) for the big button; amber only for "at the bar". Tokens only, in `:root` of index.html, light and dark.
- Big Shoulders Display for bar names, the button label and big numbers; Instrument Sans for everything else; tabular-nums on every time, pace, rank and bib. Nothing under 14px.
- Never show a guessed number: a leg with a missing tap is untimed and left out of pace.
- Location is read only on a check-in tap, and only distance and accuracy are stored. Never coordinates.
- `config.js` holds only the publishable key. Never a secret or service_role key anywhere in this repo.
- Every write goes through a function in supabase.sql that checks who is asking. No table write grants to anon or authenticated.
- Ask Jason before changing anything on his accounts (GitHub, Supabase). He types passwords and sign-in codes himself.
- No em dashes in copy.

## Before calling a change done
`python3 build.py`, then `tests/shots.py` (PROBLEMS: none), `tests/firstload.py`, and `tests/test_db.py` if supabase.sql changed. Look at the changed screens in tests/out once.
