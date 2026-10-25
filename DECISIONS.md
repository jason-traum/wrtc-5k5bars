# DECISIONS.md

2026-09-28. Two taps per bar ("I'm at", "Leaving"), chosen by Jason. Rejected: one tap with group starts at each leave time. Reopen if many legs come back untimed on race day.

2026-09-28. Layout: one big button (next bar + giant check-in), leaderboard on a second tab. Rejected: scorecard of all five stops; leaderboard-first with a fixed bottom button. Why: one job per glance in a loud bar.

2026-09-28. Ranking by moving pace; bar time never counts; untimed legs left out, never estimated. Why: rushing drinks should not win, and a guessed number would be a fake number.

2026-09-28. Leg 1 starts at the organizer's GO for everyone (falls back to the scheduled start). SUPERSEDED same day, below.

2026-09-28. Everyone starts on their own (Jason: "not everyone has to start at the same time"). GO (or the scheduled time) opens the start; each runner taps Start when they set off, and leg 1 counts from that tap. Forgot to tap Start: "Already at PHS Garden?" checks them in with leg 1 untimed, the same as a forgotten Leaving tap. Never falls back to the GO time, since that would make a late starter look slow.

2026-09-28. Sign-in: bib number + first name through Supabase anonymous sign-in. Rejected: roster pick, email code. Organizers sign in by email code.

2026-09-28. Backend: a new Supabase project, not In.'s. Why: anonymous users get the authenticated role, which In.'s rules let read runner cards and friendships.

2026-09-28. Look: race bib (navy band, bib red, amber for bars; Big Shoulders Display + Instrument Sans), matching the event one-pager.

2026-09-28. Location: read only on a check-in tap; store distance and accuracy, never coordinates. A far or failed reading can still check in, marked not GPS-checked.

2026-09-28. During the race the Race tab shows only the next bar, the button, and (at a bar) the leave-by time. No leg times, pace, place or schedule mid-race. Why: Jason, "people will be at a bar drinking and socializing, don't overwhelm them." The numbers moved to after: the finish screen (place, pace, running time, a run-vs-bar bar for the whole night, fastest leg, longest stop, every split) and a tap on any leaderboard row. The leaderboard row itself is rank, bib, name, where they are, pace.

2026-09-28. At a bar, the leave time is a live countdown (Jason). Over an hour out it shows the clock time instead of a long timer.

2026-09-28. Directions open Apple Maps on Apple devices and Google Maps on everything else (Jason). Walking, to the coordinates, not the address, so Bar 4 and the start work before they have real addresses.

2026-09-28. Taps from any date are accepted, so a practice run works before race day. The organizer clears them with one two-step button (taps and GO go, bibs stay). Rejected: refusing taps more than 3 hours before the start, which blocked testing. Accepted risk: a runner who calls the database directly can send a false earlier time; this is a club fun run, and the organizer sees each tap and can remove it.

2026-09-28. Same phone re-claiming its own bib with a different name renames it. A different phone needs the same first name to take a bib over (Safari vs Home Screen app). Accepted risk: someone who knows a bib and its first name can move it to their phone.

2026-09-28. Security review before launch (fresh reviewer, then checked against a local Supabase stand-in, 121 checks). Changed: organizer means a confirmed, non-anonymous account on the admins list that signed in with an email code, checked against auth.users rather than trusting the token's email; once a bib has checked in, it can only move to a new phone through the organizer ("Let bib 12 move to a new phone"), because bib and first name are both public on the leaderboard; other runners can no longer read each tap's GPS distance and accuracy; names over 60 characters or with invisible or direction-flipping characters are refused; a burst of realtime changes refetches once. Also fixed: a brand-new phone got stuck on "Joining…" because it couldn't read the race before signing in.

2026-09-28. Progress strip shows shoe / pint icons that invert when done (Jason), with a medal for the finish since that's where medals are handed out.

2026-09-28. Strip cut from ten icons to six (Jason: "too busy?"). Finish moment added (Jason: "an explosion or just a cool UI thing"): one burst on the finish check-in, about 2 seconds, then calm. Replaces the earlier "no confetti" rule for that one moment only.

2026-09-28. Two small numbers back on the race screen (Jason): the leg distance while running, and your last leg's pace at the bar. One quiet line each, pace only (no time or place) so it stays one glance.

2026-09-28. Event name shown on the join screen band, the finish card, the Home Screen app name and the event name (Jason). Superseded 2026-10-19.

2026-09-28. Real street map (Jason: "the map is kinda shit"). MapLibre with OpenFreeMap vector tiles (free, no key) in a custom quiet style built from the app's tokens, light and dark: canvas blocks, white streets, river, street names only. Rejected: raster OSM/CARTO tiles (can't match the palette), the hand-drawn grid (not a real map). Map tab for runners; tap a bar for address, leave time, Apple and Google Maps. Limited to a few km around the course; the service worker caches tiles you've seen.

2026-09-28. Organizers never drag pins (Jason: "I would only ever import the locations"). Bars are placed by OpenStreetMap search (name or address), pasted coordinates, or standing there.

2026-09-28. "Show my results on the leaderboard", pre-checked on the join screen and at the bottom of the leaderboard (Jason). Opting out hides the runner and their taps from everyone but themselves and organizers, enforced by the database rules, not just the screen.

2026-09-28. Location can't be "always on" for a website, and doesn't need to be: it's read only on a check-in tap. Instead: "Test my location" before the start (says whether the reading is good and flags Precise Location being off), and "Test a check-in at <bar>" for organizers walking the course.

2026-09-28. About page on the site (about.html), a copy of the event overview: the bib, the numbers, the route, the day, drinks options and fine print, with links to the pitch doc and the bars plan. The only way in is tapping the 5K5BARS wordmark at the top (Jason: "hidden is perfect at the top"). The example photos stay off the public site.

2026-09-28. Bibs run 1 to 9999 (Jason). The header chip shortens long names so a 4-digit bib fits a 320 px phone.

2026-09-29. Removed the Event overview, Pitch doc and Bars and outreach plan links (organizer screen and about page). They pointed to private Claude artifacts that visitors can't open (Jason: there shouldn't be any Claude artifacts).

2026-09-29. About page made plainer (Jason: "make that site less ai-y. It looks good tho"). Kept the bib, colors, route strip and schedule. Cut the tracked all-caps eyebrows, the four-number stat tiles, the pill links with arrows, the drawn card and ticket icons, the +/- lists, the tiled fine print and the checkbox chips. Headings now say what the section is (Route, Schedule, Drinks), the numbers are one plain sentence under the bib, and nothing is under 14px. The event overview artifact is made from the same template, with the photos; the site version links only back to the app.

2026-09-29. The ?demo link starts from the beginning so Jason can send it to anyone (Jason: "make it seamless for me to send it to someone"). Join is pre-filled (no sign-in beyond one tap), the start opens 15 seconds after joining, and each tap skips ahead in time so the leaderboard shows real-looking paces instead of 10-second legs. The no-config preview still opens mid-race.

2026-09-29. A tap that is still sending no longer shows the "No signal" banner or the saved-on-this-phone line for its first 3 seconds. Found while checking the demo: the banner flashed on every tap while the request was in flight.

2026-09-29. Demo countdown cut from 15 to 8 seconds (Jason).

2026-10-19. WRTC only, renamed 5 Bar 5K (Jason). The name is "5 Bar 5K" on the title, Home Screen name, join band ("WRTC · date"), finish card ("WRTC 5 Bar 5K") and the wordmark (5BAR5K, 5K in red, like the flyer).

2026-10-19. Route set for Sun Oct 25 (Jason): Rittenhouse, PHS Pop Up Garden, McGillin's, Independence Beer Garden, The Plough & the Stars (Bar 4), Morgan's Pier. About 5.0 km on the grid, no leg under 0.7 km. 30 minutes per stop instead of 40, so the group leaves at 2:00, 2:30, 3:00, 3:30 and 4:00 and reaches the finish about 4:05. Independence Beer Garden's pin moved about 120 m north to the garden itself (it was south of Chestnut). Mac's Tavern was ruled out: it closed in 2025 and its reopening isn't confirmed.

2026-10-19. Rain plan and call script on the organizer screen (Jason). One button per outdoor stop swaps in an indoor backup (Misconduct Tavern for PHS Garden, Red Owl Tavern for Independence Beer Garden) and back; leave times stay. "Calling the bars" shows each bar's first-runner arrival time and copies Jason's script with it. Race-day card on the join screen: bring a light layer (the river at 4 PM is cooler than the forecast) and getting home (the El from 2nd St, or a rideshare); getting home is on the finish screen too.

2026-10-19. Finish moved indoors (Jason: "I don't need river view. Agree it will get cold if outside"). Paddy's (228 Race St) replaces The Plough & the Stars as Bar 4 and Yards Brewing (500 Spring Garden St) replaces Morgan's Pier as the finish. Morgan's was outdoors on the river at about 4 PM with no rain backup; Yards is a big indoor taproom with room for the group and the medals. Legs 1.14, 1.00, 1.12, 0.99 and 1.13 km, 5.38 km in all, about 0.4 km longer. Getting home is now Spring Garden station on the El, about 6 minutes' walk. The last leg crosses Vine St instead of Columbus Blvd. Only PHS Garden and Independence Beer Garden are outdoors now, and both have backups.

2026-10-21. Bibs run from 0 to 99999 (Jason added bib 0, and bib 42069 couldn't join under the old 1 to 9999 limit). Bib columns are integer now. The printed set is 40 bibs: 0, 1, 8, 13, 67, 69, 212, 420, 42069 and 31 mixed numbers instead of 101 up.

2026-10-25. Race day, finish back at Morgan's Pier (Jason: "I feel like ending at morgan pier will be fun"). About 11 runners, sunny and about 67°F with no rain, and Morgan's has DJs 2 to 6 PM, so the river finish beats Yards today. Route: PHS Pop Up Garden, McGillin's, Independence Beer Garden, The Plough & the Stars, Morgan's Pier; legs 1.14, 1.00, 1.12, 0.70 and 1.07 km. Morgan's pin moved to Google's location. Getting home is the El from 2nd St again.

2026-10-25. Backup route page at /route (Jason: a separate page with just the bars in case the app goes wrong). Static HTML, no database or scripts: each stop with address, leave time, Google and Apple Maps links, a whole-route walking link, getting home, and a link back to the app.

2026-10-25, mid-race. Group started at 2:11, so leave times moved 15 minutes later (2:45, 3:15, 3:45, 4:15). Finish moved from Morgan's Pier to Craftsman Row Saloon, 112 S 8th St, 0.98 km from the Plough (Jason: people wanted to end closer to Rittenhouse). Then moved again, further west on Walnut, to Moriarty's Irish Pub, 1116 Walnut St, 1.55 km from the Plough (Jason: "It can be a bit further too? Direct towards rittenhouse"). Getting home: walk west on Walnut to Rittenhouse, or the El from 11th St.

2026-10-25, 3:14 PM. Last three stops swapped to loop back west instead of Old City (Jason: "Perfect. Lets do that."): McGillin's, Con Murphy's Irish Pub (17th & Parkway, leave 3:45), Bonner's Irish Pub (23rd & Sansom, leave 4:15), finish at Walnut Garden (1708 Walnut, one block from Rittenhouse). Legs 1.08, 1.36, 0.90 km; about 5.5 km in all.

Prior apps (to avoid repeating):
- In.: pale green #EAF2EE, deep green #1E5F55, Saira Condensed + Hanken Grotesk, green dot wordmark.
- WRTC 5K 5 Bars one-pager: this app's own source look.
