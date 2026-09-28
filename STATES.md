# STATES.md

## Join (bib + first name)
- Initial: two fields, one button "Join the race".
- Saving: button shows a spinner after 500ms and keeps its label.
- Bib taken by the same first name: moves the bib to this phone (Safari and the Home Screen app are separate).
- Bib taken by a different name: "Bib 23 is already Sam's. Check the number on your bib, or ask the organizer."
- Bib out of range: "Bibs run from 1 to 300."
- No signal: "Couldn't reach the race. Check your signal and try again." Fields keep their values.

## Race
- Before the start opens (no GO, before the scheduled time): bar name "Rittenhouse Square", a live "Start opens in 12:00" countdown (over an hour out it shows the clock time, and the date if another day), directions, the full schedule (the only place it shows). No big button. Past the start with no GO: "Any minute, waiting for the organizer's GO".
- Start is open (GO pressed or the scheduled time passed), runner not started: "Start line · open", "Go whenever you're ready", big button "Start / Tap as you set off", secondary "Already at PHS Garden?" for someone who forgot. After the tap: "Started at 2:14. Saved." and the screen moves to leg 1.
- En route to bar N: bar name, one line "1.0 km from PHS Garden", button "I'm at <bar N>", Directions. No clock or stats.
- Checking location: button shows "Checking location…" after 500ms; tap disabled until done.
- Checked in with location: button turns into a saved confirmation with the time, then the screen moves to "at bar". Line: "Checked in at 6:46."
- Too far (more than the bar's radius plus accuracy): "Your phone says 640 m from McGillin's. GPS is often off inside bars." Actions: "Try again", "Check in anyway". Anyway is saved as not GPS-checked (the organizer sees that; the runner sees "without location").
- Location off or denied: "Location is off for this site. You can still check in." Actions: "Try again", "Check in anyway". One small line says where to turn it on.
- At bar N: amber panel with a live countdown "Group leaves in 29:42 / at 7:04 PM", "finish up" added in the last 5 minutes, "Time to go" at zero. Button "Leaving <bar N>", secondary "Already at <bar N+1>?" for a forgotten leave tap. One line under the bar name: "Last leg 8:54/mi" (hidden if that leg is untimed).
- Offline: taps save on the phone with their real time and sync later. Line under the button: "Saved on this phone. Syncs when you have signal."
- Undo: the last tap can be undone for 2 minutes.
- Finish check-in: the finish moment (medal pops, one burst of shoes and pints, "Finished · 6th of 15"), about 2.4 s, tap to skip. The medal on the finish card replays it.
- Finished (the data screen): place, pace, running time; "Your night" bar (red running, amber at bars, grey for a missed tap) with running and bar totals; fastest leg and longest stop; every run and bar split.
- Failed load: "Couldn't load the race. Pull down or tap Retry." Never shown as an empty race.

## Leaderboard
- Loading: last list kept; nothing shown under 500ms.
- Empty (before anyone has a timed leg): everyone listed by bib with "No timed legs yet".
- Many: ranked by moving pace; row is rank, bib, name, where they are, pace. Your row tinted and reachable with "Jump to me".
- Row tapped: opens that runner's night bar and splits under the row. Tap again to close.
- Stale: "Last updated 3 min ago" when realtime has dropped.
- Failed: "Couldn't load the leaderboard. Retry." Never an empty list.

## Organizer
- Not signed in: email code sign-in (organizers only).
- GO: one button that opens the start (everyone then starts their own clock), then "Undo GO" for 60 seconds. Without GO, the start opens at the scheduled time.
- Stops: name, leave-by time, "Set to where I'm standing", radius.
- Runners: per runner, remove a tap or release a bib. Removing asks once with the consequence in the button label.
- After a practice run: "Clear all 23 check-ins", then "Tap again to delete 23 check-ins" (resets after 6 s). Clears taps and the GO, keeps bibs. Disabled with "Nothing to clear".
- Directions and "Check in Apple/Google": Apple Maps on iPhone, iPad and Mac; Google Maps everywhere else. Walking directions to the pin.
