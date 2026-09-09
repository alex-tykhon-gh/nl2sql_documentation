---
name: deep-test
description: Deep-test a plugin/module page for this NL2SQL course assignment — real browser, real DOM/network checks, protects against firing paid model calls unprotected. Use when asked to test, verify, or QA a plugin's page before submitting it.
---

# Deep-test a plugin page

Built while verifying three real plugins (CyberDome, FinOps, ReverSQL)
against this course's actual grading core. Every check below found a real
bug at least once — this is not a theoretical checklist.

## How to actually install and use this

This is a **Claude Code Skill** — a folder Claude Code recognizes and can
invoke by name, not just a document to read.

1. **Copy this whole `deep-test/` folder** (this file + `DEEP_TESTING_METHOD.md`
   + `deep_test_kit.py`) into a `skills` folder Claude Code already looks in:
   - **One project only:** `<your project root>\.claude\skills\deep-test\`
   - **Every project you open:** `%USERPROFILE%\.claude\skills\deep-test\`
     (create the `skills` folder if it doesn't exist yet)
2. Open Claude Code in your own plugin's project (a fresh session, or restart
   an open one so it picks up the new skill).
3. Ask it to test your plugin — either type `/deep-test` directly, or just ask
   normally ("deep-test my plugin before I submit it", "QA the CyberDome
   page") — Claude Code matches your request to the skill's own description
   automatically, you don't have to remember the exact command.
4. That's it — no setup specific to this repo, no dependency on the plugins
   this method was originally built from. It only needs Playwright in
   whatever venv you're testing (see "One-time setup" in
   `DEEP_TESTING_METHOD.md` if it's missing).

## Why this method, not just reading the code or looking at a screenshot

Every real bug found this way was found by **actually running the app in a
real browser and looking** — reading source and reasoning about it missed
all of them. And a screenshot alone is not enough either: a module's sidebar
icon looked like a plain emoji at a glance, at 16px — it was actually a
correctly-loading real `<img>`, confirmed only by querying the DOM node's
`src` and the network log's status, not by eyeballing pixels. Use a
screenshot as a **second**, confirming signal — never the only one.

See `DEEP_TESTING_METHOD.md` next to this file for the full reasoning and
four real worked examples. `deep_test_kit.py` (also next to this file) has
working Playwright helpers for everything below — copy it beside your own
test script and `from deep_test_kit import *`.

## The order that actually works

1. **Cheap layer first.** If the plugin has an existing `pytest` suite, run
   it before opening a browser at all — it's seconds, not minutes, and
   catches logic regressions the browser pass isn't built to find. Only
   spend the slower live-browser pass on what pytest structurally can't see:
   rendering, real DOM, real clicks, real network behavior.
2. **One-time setup**, if the venv you're testing against doesn't have
   Playwright yet:
   ```
   <venv>\Scripts\python.exe -m pip install playwright pillow
   <venv>\Scripts\python.exe -m playwright install chromium
   ```
   `pillow` is only needed for cropping/zooming screenshots — skip it if you
   never need a close-up.
3. **Start the real server** on a port you know isn't already in use (check
   with a plain `netstat`/`Get-NetTCPConnection` first — don't assume).
   `deep_test_kit.start_server` polls with a raw TCP connect, not an HTTP
   request: a proxy/system HTTP setting can make an HTTP readiness probe lie
   about a server that is genuinely up.
4. **Open a real browser page, logging wired up BEFORE navigating** —
   `deep_test_kit.new_logged_page` — console messages and page errors caught
   from the first paint, not just after something looks wrong.
5. **Drive the actual scenario**: navigate, click, wait for the specific
   thing that means "done" (not a fixed sleep — poll for the real signal).
6. **Collect evidence**: a full-page screenshot, the console/error log, and
   — for anything claiming to be a specific real image, value, or count —
   the actual DOM attribute or computed style (`deep_test_kit.img_check`),
   not just how it looks rendered.
7. **Tear the server down** — `deep_test_kit.stop_server`. Then verify it
   actually died: `deep_test_kit.port_free(host, port)` should return
   `True`. **A stalled or killed test script never reaches its own
   try/finally** — if you're running this from an agent or background
   process that might itself get killed by a timeout, that cleanup code
   never runs, and the server keeps listening. Check the port is actually
   free, don't just trust that the stop call happened.

## Never click a paid action unprotected

Any button that fires a real model call (Send / Ask / a Check/Run that calls
the LLM) costs real money and real time the moment a real click reaches it.
If the check is about layout, framing, copy, or a disabled state — not about
the model's actual answer — **intercept and abort that specific request
first** (`deep_test_kit.block_costly_calls`), then click freely. Only let a
paid call actually fire when the check is specifically about what comes back
from it, and say so plainly in whatever report you write.

## What to actually go look for (translate into a checklist per page)

For every page a plugin ships, and the shared shell around it:

- **Load it cold and read the whole screenshot.** Anything that isn't part
  of the intended UI (stray text, a leftover debug string, a block that
  reads like a code comment — `deep_test_kit.leaked_comment_check`) is a
  real bug, full stop.
- **For every "identity" element (icon, name, badge, count):** query the
  actual DOM node and, if it's an image, the network log's status for its
  `src` — don't decide from how it looks in a screenshot alone, especially
  at small sizes.
- **For every multi-step guided flow:** walk it via the path a rushed real
  user takes (the fastest way to "done"), not just the path the copy
  narrates.
- **For every visual grouping/frame around "the current action":** check it
  does not also enclose something that isn't actually actionable yet
  (disabled, waiting on a prior step).
- **For every element positioned relative to something else (a tooltip, a
  badge, a popover):** check its actual bounding box against the element(s)
  it might overlap, via `getBoundingClientRect()` — not just whether it
  looks fine in one screenshot. A badge that lands on top of the very
  control it's explaining, stealing the click, looks completely normal in a
  screenshot and is invisible until you check the geometry.
- **For every fallback/alternate rendering path:** find the actual runtime
  condition that switches between them and deliberately produce both states.

## If the automation stalls partway through

If a test script or agent stalls or gets killed before finishing, don't
automatically restart the whole pass from zero — check what evidence it
already saved (screenshots, a partial bug-report file) first. Often enough
has already been gathered to finish the review by hand from what's there,
which is faster and doesn't re-spend the paid-call budget on calls that
already happened.

## Bug report format

One entry per bug. `deep_test_kit.write_bug_report(...)` appends this exact
shape to a running markdown file:

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
