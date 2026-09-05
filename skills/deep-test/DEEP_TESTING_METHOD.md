# Deep testing method — for an NL2SQL plugin, before you submit it

## Why this exists

Every real bug found and fixed while building three plugins for this
assignment was found by **actually running the app in a real browser and
looking**, not by reading source and reasoning about it. Four concrete
examples, because they're the whole argument for this method:

1. A dropped `<!--` in a hand-edited HTML page turned ~20 lines of developer
   comment into literal visible page text, on every page, in production.
   Reading the file top-to-bottom would eventually have caught it; a
   screenshot caught it in one look.
2. A module's sidebar icon looked like a plain emoji at a glance, in a
   screenshot, at 16px. It was actually a correctly-loading real `<img>` —
   confirmed only by querying the DOM node's `src` and the network log's
   status code, not by eyeballing pixels. The *opposite* mistake (assuming
   "looks fine" when it's actually the wrong element) is just as easy to
   make the other way — this method checks the DOM/network, and uses a
   screenshot only as a **second**, confirming signal, never the only one.
3. A guided-tour step's code "looked" correct reading it in isolation — the
   bug (a disabled button co-highlighted with the live one, and a dead-end
   two steps later) only became obvious by actually starting the tour and
   progressing through it as a real user would, including the *unexpected*
   order (clicking the primary action immediately, not filling every field
   first).
4. A hover-hint tooltip badge looked completely fine in every screenshot
   taken of it — it only became a real bug once its actual bounding box was
   checked against the button it was meant to be explaining, which it was
   silently overlapping and stealing clicks from.

None of these four are hypothetical near-misses — they were real bugs found
this way. The method below is how.

## Ground rule: this method never edits code it doesn't own

If you're testing your own plugin against your own copy of the core, fixing
what you find is exactly right. But if you're testing against a shared
grading harness, an instructor's own app, or anything that isn't yours to
change, this method has exactly one job there: **find and document**. Never
hand-edit code you don't own to "just fix it locally" — a local edit is
invisible to anyone who later re-pulls the real thing, and gives false
confidence that something is fixed when only a local copy was touched. Write
a bug report instead (format below), every time.

## One-time setup (per venv)

A typical assignment venv won't ship Playwright — add it once:

```powershell
cd <app folder>
.\.venv\Scripts\python.exe -m pip install playwright pillow
.\.venv\Scripts\python.exe -m playwright install chromium
```

`pillow` is only needed for cropping/zooming screenshots (see below); skip
it if you never need a close-up.

## The basic recipe

0. **Cheap layer first.** If the plugin already has a `pytest` suite, run it
   before opening a browser at all. It's seconds, not minutes, and catches
   logic regressions the browser pass isn't built to find — spend the
   slower live-browser pass only on what pytest structurally can't see.
1. Start the real app on a port you've checked isn't already in use.
2. Wait for it to actually accept connections — a raw TCP connect, not an
   HTTP request. A proxy/system HTTP setting can make an HTTP readiness
   probe lie about a server that's genuinely up.
3. Open a real (headless is fine) browser page against it, wired to capture
   console messages, page errors, and network responses **before**
   navigating — logs started after the fact miss the first paint.
4. Drive the actual scenario: navigate, click, wait for the specific thing
   that means "done" (not a fixed sleep — poll for the real signal).
5. Collect evidence: a full-page screenshot, the console/error log, the
   network log, and — for anything claiming to be a specific real image,
   value, or count — the actual DOM attribute or computed style, not just
   how it looks rendered.
6. Tear the server down when done, then **verify it's actually gone** — the
   port should stop accepting connections. A script or agent that stalls or
   gets killed partway through never reaches its own cleanup code, and a
   server can be left running silently. Don't just trust that a stop call
   happened; check.

`deep_test_kit.py` (next to this file) has working helpers for all of this —
copy the whole `deep-test/` folder into (or beside) the project you're
testing and import it.

## Never click a paid action unprotected

Any button that fires a real model call (Send / Ask / a "Check"/"Run" that
calls the LLM) costs real money and real time the moment a real click
reaches it. If the check is about layout, framing, copy, or a disabled
state — not about the model's actual answer — **intercept and abort that
specific request first** (`deep_test_kit.block_costly_calls`), then click
freely. Only let a paid call actually fire when the check is specifically
about what comes back from it, and say so plainly in the report.

## What to actually go look for (translate into a checklist per page)

For every page a plugin ships and the shared shell around it:

- **Load it cold and read the whole screenshot.** Anything on the page
  that isn't part of the intended UI (stray text, a leftover debug string,
  a block that reads like a code comment) is a real bug, full stop.
- **For every "identity" element (icon, name, badge, count):** query the
  actual DOM node and, if it's an image, the network log's status for its
  `src` — don't decide from how it looks in a screenshot alone, especially
  at small sizes.
- **For every multi-step guided flow:** walk it via the path a rushed real
  user takes (the fastest way to "done"), not just the path the copy
  narrates — a bug that only exists on the fast path is still a real bug.
- **For every visual grouping/frame around "the current action":** check
  it does not also enclose something that isn't actually actionable yet
  (disabled, waiting on a prior step) — a technically-correct gate can
  still *look* like it's offering two choices when only one is live.
- **For every element positioned relative to another (a tooltip, a badge, a
  popover):** check its real bounding box against whatever it might
  overlap, via `getBoundingClientRect()` — a badge that lands on top of the
  control it's explaining looks completely normal in a screenshot.
- **For every fallback/alternate rendering path:** find the actual runtime
  condition that switches between them (a count comparison, a feature
  flag, a missing field) and deliberately produce both states rather than
  assuming whichever one you saw first is the only one that exists.
- **Cross-check any generated description/label text against its raw
  source** (the API response, not just the styled page) — text that reads
  fine styled can still be repeating verbatim boilerplate across every
  instance, which only shows up by diffing the raw strings.

## If the automation stalls partway through

Don't automatically restart the whole pass from zero. Check what evidence
was already saved first — screenshots, a partial bug-report file. Often
enough is already there to finish the review by hand, faster than
re-running everything and re-spending any paid-call budget on calls that
already happened.

## Bug report format

One entry per bug, appended to a single running `BUGS_FOUND.md` (a
`deep_test_kit.write_bug_report(...)` helper does this for you). Keep every
field — a report missing "expected vs. actual" or repro steps sends the fix
back here with a round of questions instead of a fix.

```markdown
### <short title>

- **Where:** <plugin/page name> — <specific screen/step/element>
- **Repro:** <exact steps, in order, from a fresh page load>
- **Expected:** <what should happen/show>
- **Actual:** <what actually happens/shows>
- **Evidence:** <screenshot path, and/or the exact DOM/network detail that
  proves it — not just "it looked wrong">
- **Suspected cause:** <if you have one from reading the source; "unknown"
  is fine too>
- **Confidence:** <confirmed reproducible / seen once, unconfirmed>
```

## A related but separate warning

If you ever embed something like a base64-encoded image directly into a
page, never paste a long generated string by hand through an editor or chat
interface — it can get silently truncated with no visible error. Script the
generation *and* a decode-and-compare check against the original bytes
before committing it. Not testing a running app, exactly, but the same
"verify, don't assume" instinct this whole method is built on.
