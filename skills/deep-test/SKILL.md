---
name: deep-test
description: Deep-test a plugin/module page for this NL2SQL course assignment — real browser, real DOM/network checks, protects against firing paid model calls unprotected. Use when asked to test, verify, or QA a plugin's page before submitting it.
---

# Deep-test a plugin page

Built while verifying three real plugins (CyberDome, FinOps, ReverSQL)
against this course's actual grading core. Every check in this method found
a real bug at least once — see `DEEP_TESTING_METHOD.md` (next to this file)
for the full reasoning, four real worked examples, the checklist, the paid-
call safety rule, and the bug report format. **That file is the actual
method — read it before testing anything.** This file is just the install
step and the pointer to it.

## How to actually install and use this

**If you're just looking to download and install this skill, see
`README.md` right next to this file — it has the download/copy steps.**
This section is the short version, for once it's already in place:

1. Once this whole `deep-test/` folder is copied into `.claude\skills\`
   (project-level or global — `README.md` covers both), open or restart
   Claude Code in your own plugin's project so it picks up the new skill.
2. Ask it to test your plugin — either type `/deep-test` directly, or just
   ask normally ("deep-test my plugin before I submit it") — Claude Code
   matches your request to the skill's own description automatically.
3. That's it — no dependency on the plugins this method was originally
   built from. It only needs Playwright in whatever venv you're testing
   (see "One-time setup" in `DEEP_TESTING_METHOD.md` if it's missing).

## What actually happens when you invoke it

Once triggered, this skill follows `DEEP_TESTING_METHOD.md` — Claude reads
that file (and uses `deep_test_kit.py`'s helpers) to run pytest first if one
exists, start your real app, drive it in a real headless browser, check the
actual DOM/network (not just a screenshot), and write up anything it finds
in the bug report format that file defines. You don't need to memorize any
of that yourself — it's what Claude does on your behalf once this skill is
in place.
