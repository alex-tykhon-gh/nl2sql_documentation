# NL2SQL Platform — Task 3 Project Overview

Three independent plugins, submitted as three separate repositories, extending
the NL2SQL platform without modifying its core.

## What was required, and what was built

| | Required | Delivered |
|---|---|---|
| Security | A security/PII plugin — guardrail checks, penetration testing, PII-exposure reporting | **🔐 Security CyberGuard** — Scan for PII, Full compliance report, Probe live injection, Audit recorded queries |
| FinOps | A cost-tracking plugin — token/cost reporting, recommendations for reducing spend | **💰 FinOps** — usage & cost dashboard, full activity log, cost-saving recommendations backed by real per-setting cost/accuracy comparisons |
| — | Not required | **🪞 ReverSQL** — a third plugin, built beyond the assignment: translates generated SQL back into plain English so a user can verify a query's meaning survived the round trip. Confirmed with the instructor as worth submitting. |

Each plugin connects to the core through its published contract only —
`ctx.query()`/`ctx.tables()`/`ctx.columns()`/`ctx.data_dir()` and the
`Module`/`Action`/`Result` shapes it defines. None of the three ever modifies
the core's own code.

## The core-compatibility discovery

The single most consequential finding of the project. The instructor's actual
grading environment (`nl2sql-app-closed-core`, built around `nl2sql-core`)
turned out to be a **separate implementation** from the one this project was
developed and tested against (`nl2sql-engine`) — same contract shapes by
design, but its own independent version history, frozen at `API_VERSION 1.0`.
That core's `Context` object does not expose `ctx.ask()`/`ctx.nl2sql()` —
methods that only exist from version 1.1 onward on the engine this project
was built against.

Verified directly, in an isolated sandbox, before assuming anything: running
plugin discovery against the real grading core rejected all three plugins
outright —

```
cyberdome -> needs core API >=1.1,<2.0, this core is 1.0.
finops    -> needs core API >=1.1,<2.0, this core is 1.0.
reverseql -> needs core API >=1.1,<2.0, this core is 1.0.
```

Not a defect in the grading core — the version gate doing exactly its job.
But it meant that installing these plugins the way they would actually be
installed, unmodified, would have produced an app with none of them working.

**Resolution:** FinOps and CyberDome's PII scan never actually depended on the
1.1-only methods — their version floor was corrected to `>=1.0,<2.0`.
ReverSQL's core feature (turning a question into SQL, and reading SQL back)
has no reduced version that avoids the model entirely — for that, both
ReverSQL and CyberDome's injection probe now call the sanctioned method when
a core exposes it, and fall back to the identical internal function it wraps
when it doesn't. All three plugins run unchanged, not degraded, on either
core.

## Verification

Confirmed working end to end against the actual grading core, not just
reasoned about:

- A dedicated regression suite added to CyberDome and ReverSQL, covering this
  exact compatibility fallback.
- A local clone of `nl2sql-app-closed-core`, installed and run exactly as the
  instructor's own process describes — all three plugins loaded and produced
  real, live results (including genuine model calls) inside that environment.
- **62/62 tests passing** across the three plugins (20 CyberDome, 24 FinOps,
  18 ReverSQL).
- Two independent, adversarial QA passes: the first immediately after the two
  required plugins were built, the second after a later UI pass across all
  three. Together they found and fixed 16 real defects — logic bugs, crash
  conditions on malformed input, and UI issues — none cosmetic.
- A final pass, run the same way twice — once against the development
  environment, once against a faithful local copy of the actual grading
  environment — confirmed all three plugins still install cleanly, run
  without console errors, and behave identically in both places.

## Project timeline

- **32 days**, first commit to submission (4 August – 5 September 2026).
- **121 commits** across the four repositories involved (the main
  application plus the three plugins).
- **3 independent, one-click-installable repositories**, each containing its
  own plugin, tests, and documentation — matching the submission format
  confirmed directly with the instructor.

## What's included in this submission

1. `nl2sql_cyberdome` — Security CyberGuard
2. `nl2sql_finops` — FinOps
3. `nl2sql_reverseql` — ReverSQL
4. This repository — project documentation, plus a testing method
   (`deep-test`, see `skills/`) built while verifying the above.

## A free contribution, for anyone in the class

`skills/deep-test/` isn't part of any of the three plugins — it's the actual
method used to find and fix real bugs in all three before submitting, packaged
as a standalone Claude Code skill: real browser checks, DOM/network
verification instead of judging a screenshot alone, and guardrails against
firing a paid model call by accident. Shared here **free of charge**, for
anyone else in the class to drop into their own plugin project and use as-is.

