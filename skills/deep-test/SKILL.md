---
name: deep-test
description: Deep-test a plugin/module page for this NL2SQL course assignment — real browser, real DOM/network checks, protects against firing paid model calls unprotected. Use when asked to test, verify, or QA a plugin's page before submitting it.
---

# Deep-test a plugin page

Built while verifying three real plugins (CyberDome, FinOps, ReverSQL)
against this course's actual grading core. Every check below found a real
bug at least once — this is not a theoretical checklist.

## How to actually install and use this

**If you're just looking to download and install this skill, see
`README.md` right next to this file — it has the download/copy steps.**
Short version, for once it's already in place:

1. Copy this whole `deep-test/` folder into `.claude\skills\deep-test\`
   (project-level or global — `README.md` covers both).
2. Open or restart Claude Code in your own plugin's project so it picks up
   the new skill.
3. Ask it to test your plugin — either type `/deep-test` directly, or just
   ask normally ("deep-test my plugin before I submit it") — Claude Code
   matches your request to the skill's own description automatically.
4. That's it — no dependency on the plugins this method was originally
   built from. It only needs Playwright in whatever venv you're testing
   ("One-time setup" below covers that if it's missing).

## Why this method, not just reading the code or looking at a screenshot

Every real bug found this way was found by **actually running the app in a
real browser and looking** — reading source and reasoning about it missed
all of them. Four concrete examples, because they're the whole argument:

1. A dropped `<!--` in a hand-edited HTML page turned ~20 lines of developer
   comment into literal visible page text, on every page, in production.
   Reading the file top-to-bottom would eventually have caught it; a
   screenshot caught it in one look.
2. A module's sidebar icon looked like a plain emoji at a glance, in a
   screenshot, at 16px. It was actually a correctly-loading real `<img>` —
   confirmed only by querying the DOM node's `src` and the network log's
   status, not by eyeballing pixels. The *opposite* mistake (assuming
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
this way.

## Ground rule: this method never edits code it doesn't own

If you're testing your own plugin against your own copy of the core, fixing
what you find is exactly right. But if you're testing against a shared
grading harness, an instructor's own app, or anything that isn't yours to
change, this method has exactly one job there: **find and document**. Never
hand-edit code you don't own to "just fix it locally" — a local edit is
invisible to anyone who later re-pulls the real thing, and gives false
confidence that something is fixed when only a local copy was touched. Write
a bug report instead (format below), every time.

## The order that actually works

0. **Cheap layer first.** If the plugin has an existing `pytest` suite, run
   it before opening a browser at all — it's seconds, not minutes, and
   catches logic regressions the browser pass isn't built to find. Only
   spend the slower live-browser pass on what pytest structurally can't see:
   rendering, real DOM, real clicks, real network behavior.
1. **One-time setup**, if the venv you're testing against doesn't have
   Playwright yet:
   ```
   <venv>\Scripts\python.exe -m pip install playwright pillow
   <venv>\Scripts\python.exe -m playwright install chromium
   ```
   `pillow` is only needed for cropping/zooming screenshots — skip it if you
   never need a close-up.
2. **Start the real server** on a port you know isn't already in use (check
   with a plain `netstat`/`Get-NetTCPConnection` first — don't assume).
   `deep_test_kit.start_server` polls with a raw TCP connect, not an HTTP
   request: a proxy/system HTTP setting can make an HTTP readiness probe lie
   about a server that is genuinely up.
3. **Open a real browser page, logging wired up BEFORE navigating** —
   `deep_test_kit.new_logged_page` — console messages and page errors caught
   from the first paint, not just after something looks wrong.
4. **Drive the actual scenario**: navigate, click, wait for the specific
   thing that means "done" (not a fixed sleep — poll for the real signal).
5. **Collect evidence**: a full-page screenshot, the console/error log, and
   — for anything claiming to be a specific real image, value, or count —
   the actual DOM attribute or computed style (`deep_test_kit.img_check`),
   not just how it looks rendered.
6. **Tear the server down** — `deep_test_kit.stop_server`. Then verify it
   actually died: `deep_test_kit.port_free(host, port)` should return
   `True`. **A stalled or killed test script never reaches its own
   try/finally** — if you're running this from an agent or background
   process that might itself get killed by a timeout, that cleanup code
   never runs, and the server keeps listening. Check the port is actually
   free, don't just trust that the stop call happened.

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
  a block that reads like a code comment — `deep_test_kit.leaked_comment_check`)
  is a real bug, full stop.
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

## A related but separate warning: don't hand-copy large generated content

If you ever need to embed something like a base64-encoded image directly
into a page (not what this method is for, but comes up in the same kind of
work), never paste a long generated string by hand through an editor or a
chat interface — it can get silently truncated with no visible error. Have
a script generate it *and* decode-and-compare it against the original bytes
before you ever commit it.
