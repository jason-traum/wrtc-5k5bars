# DESIGN.md

Direction and its source: a race bib. Bibs are what these runners already read on the day: a navy band, one huge red number, a sponsor strip of the bars. The same look as the event one-pager, so the page people saw at the meeting and the app on race day feel like one event. It is not In.: no pale green, no Saira Condensed, no Hanken Grotesk.

## Tokens (light / dark), defined only in `:root` of index.html

| Role | Light | Dark | Use |
| --- | --- | --- | --- |
| --canvas | #E9EDF3 | #0E1628 | Page, html and body (Safari 26 tints its bars from it) |
| --surface | #FFFFFF | #172238 | Cards, sheets, tab bar |
| --surface-2 | #F3F5F9 | #1F2C46 | Your own leaderboard row, pressed rows |
| --ink | #0F1A2E | #E6ECF5 | Text |
| --ink-2 | #45506A | #A9B5CB | Secondary text, input borders. Secondary, never faint |
| --line | #C9D1DE | #34425F | Decorative hairlines only |
| --action | #C41E2A | #C81E2A | The one accent: the big button, focus, your current bar |
| --on-action | #FFFFFF | #FFFFFF | Label on the big button |
| --focus | #C41E2A | #FF6B74 | :focus-visible outline |
| --navy | #14244A | #1B2D5A | Bib band header |
| --bar | #A8680E | #F0A53A | Bar markers on the route strip (non-text) |
| --bar-soft / --bar-ink | #FDEFD6 / #6B4308 | #3A2C12 / #FFD99A | "At the bar" panel |
| --ok | #1F7A4D | #5FD39A | Saved, GPS-checked |
| --warn | #8A5A00 | #F2C46B | Not GPS-checked, saved on phone only |

Contrast (WCAG 2): ink on canvas 14.8 / 15.2; ink-2 on surface 8.1 / 7.7; label on action 5.9 / 5.7; action vs canvas 5.0 / 3.2; bar marker on surface 4.5 / 7.7; ok 5.3 / 8.5; warn 5.9 / 9.7. The big button always sits on canvas.

## Type
- Big Shoulders Display 800/900: bar names, the big button label, big numbers, the bib number. Reason: it is a bib face, narrow enough that "Independence Beer Garden" fits a 320px button.
- Instrument Sans 400/600/700: everything else. Body 17px, never below 14px.
- tabular-nums on every time, pace, rank and bib.

## Layout and components
- One job per screen. Race screen order: bib band, bar name, the big button, last split, route strip, schedule.
- The big button: full width, at least 104px tall, radius 20px, in the lower half of the screen where a thumb reaches.
- Secondary actions are outlined, 48px tall. Nothing tappable is plain text.
- Two tabs, Race and Leaderboard, fixed to the bottom, labeled.
- Radius roles: 20 big button, 14 cards, 999 chips. Shadows: none on canvas items; sheets get one soft shadow.
- Your leaderboard row: full-surface tint (--surface-2) plus "You" chip. No colored side borders.
- Progress strip (Jason's idea): six icons, a shoe for the start, a pint for each bar, a medal for the finish; the runs are the lines between them (red while you're on it). Outline = ahead, filled ink with the icon inverted = done, red ring = running to it now, amber fill = at this bar. Each has a spoken label. A ten-icon version (shoe per run) was tried and cut as too busy.

## Motion
120ms ease-out for state changes; press scale .97; sheets 220ms ease-out; no page-load reveals; reduced motion removes movement.

## Named anti-patterns for this project
Neon-on-black bar-night look; blinking live dot; tracked all-caps eyebrows; emoji; a map as decoration; any celebration other than the one finish moment.

## The finish moment
The one orchestrated animation, asked for by Jason: on the finish check-in, a navy screen, the medal pops in (560ms overshoot), one ring and one burst of 28 shoes and pints in red, medal amber and white, then "Finished / 6th of 15" and it closes itself after about 2.4 s. Tap or Escape skips. Plays again only from the medal on the finish card. Reduced motion: the medal and words, no burst, no movement. Phones that can vibrate get a short buzz.

## Reference screenshots
design/references/race-390-light.png, race-390-dark.png, atbar-390-light.png, board-390-dark.png, toofar-390-dark.png, finished-390-dark.png.
