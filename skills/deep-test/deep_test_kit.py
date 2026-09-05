r"""Reusable Playwright-based verification helpers for NL2SQL module pages.

Built directly from the checks that found real bugs on 2026-09-04 (a leaked
HTML comment, a co-framed disabled button, a silently-emoji-instead-of-icon
element, a fallback-panel condition) -- see DEEP_TESTING_METHOD.md next to
this file for the reasoning and the checklist. This module only ever reads
and reports; it never edits app or plugin source.

Requires (one-time, in the venv you're testing against):
    python -m pip install playwright pillow
    python -m playwright install chromium

Typical use (async -- Playwright's Python API is async-first):

    import asyncio
    from deep_test_kit import *

    async def main():
        proc = start_server(
            r"C:\...\nl2sql-app-closed-core\.venv\Scripts\python.exe",
            ["-m", "uvicorn", "api.main:app", "--port", "8030"],
            cwd=r"C:\...\nl2sql-app-closed-core",
            port=8030,
        )
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page, logs = await new_logged_page(browser)
                await page.goto("http://localhost:8030/page/reverseql/?db=financial")
                await page.wait_for_timeout(1500)

                # about to click things -- protect against a real paid call
                await block_costly_calls(page, ["/modules/run", "/ask", "nl2sql"])

                assert not await leaked_comment_check(page), "leaked dev comment!"
                await shot(page, "reverseql_loaded.png")

                await browser.close()
        finally:
            stop_server(proc)

    asyncio.run(main())
"""
from __future__ import annotations

import socket
import subprocess
import time
from pathlib import Path


# ── starting/stopping the real server ───────────────────────────────────────

def _port_open(host: str, port: int, timeout_s: float = 0.3) -> bool:
    # Raw TCP connect, not an HTTP request -- this project's own run.ps1
    # explains why: a proxy/system HTTP setting can make an HTTP readiness
    # probe lie about a server that is genuinely up and listening.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout_s)
        try:
            return s.connect_ex((host, port)) == 0
        except OSError:
            return False


def start_server(python_exe: str, args: list[str], cwd: str, port: int,
                  host: str = "127.0.0.1", timeout: float = 30) -> subprocess.Popen:
    """Launch `python_exe *args` in `cwd`, poll `port` until it accepts
    connections, then return the live Popen handle. Raises TimeoutError if
    the server never comes up -- that itself is worth a bug report, not a
    silent retry loop."""
    proc = subprocess.Popen([python_exe, *args], cwd=cwd)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"server process exited early (code {proc.returncode})")
        if _port_open(host, port):
            return proc
        time.sleep(0.25)
    proc.kill()
    raise TimeoutError(f"server never opened {host}:{port} within {timeout}s")


def stop_server(proc: subprocess.Popen) -> None:
    """Always call this when done -- in a try/finally, not just at the end
    of a happy path, or a failed assertion leaves the server running."""
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def port_free(host: str, port: int, timeout_s: float = 2.0,
              poll_interval: float = 0.2) -> bool:
    """Confirms a port has actually stopped accepting connections, after
    `stop_server`. Worth calling explicitly rather than trusting the stop
    call alone: if the script or agent that owned this server gets killed
    (a stall timeout, a crash) before reaching its own try/finally, that
    cleanup code never runs and the server keeps listening -- found live,
    once, as a genuinely orphaned server from a stalled background agent
    that nothing had torn down. Polls briefly (termination isn't always
    instant) rather than checking only once."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if not _port_open(host, port):
            return True
        time.sleep(poll_interval)
    return not _port_open(host, port)


# ── a page wired for evidence from the first paint ──────────────────────────

async def new_logged_page(browser, viewport: tuple[int, int] = (1400, 1000)):
    """Returns (page, logs). `logs` is a plain list that fills up live with
    "[console:TYPE] text" and "[pageerror] exc" strings -- read it after any
    action; a silent JS exception is as real a bug as a wrong pixel."""
    page = await browser.new_page(viewport={"width": viewport[0], "height": viewport[1]})
    logs: list[str] = []
    page.on("console", lambda msg: logs.append(f"[console:{msg.type}] {msg.text}"))
    page.on("pageerror", lambda exc: logs.append(f"[pageerror] {exc}"))
    return page, logs


async def new_network_log(page) -> list[str]:
    """Returns a list that fills up live with "STATUS URL" for every
    response -- pass a page BEFORE navigating, same reasoning as logs."""
    reqs: list[str] = []
    page.on("response", lambda r: reqs.append(f"{r.status} {r.url}"))
    return reqs


async def block_costly_calls(page, url_substrings: list[str]) -> None:
    """Aborts any request whose URL contains one of `url_substrings`. Call
    this BEFORE clicking anything that might fire a real, billed model call
    -- Send/Ask/Run/Check-style buttons -- whenever the check is about
    layout, copy, or a disabled/enabled state and NOT about what the model
    actually returns. Never click one of those buttons unprotected "just to
    look around."""
    def _maybe_abort(route):
        url = route.request.url
        if any(s in url for s in url_substrings):
            return route.abort()
        return route.continue_()
    await page.route("**/api/**", _maybe_abort)


# ── evidence collection ──────────────────────────────────────────────────────

async def shot(page, out_path: str, full_page: bool = True) -> None:
    await page.screenshot(path=out_path, full_page=full_page)


def crop(in_path: str, out_path: str, box: tuple[int, int, int, int],
         scale: tuple[int, int] | None = None) -> None:
    """box = (left, top, right, bottom) in the ORIGINAL screenshot's pixels.
    scale, if given, upsizes the crop -- a real icon and a generic emoji can
    look identical at 16-22px; a 3-4x blow-up is often the difference
    between "looks like an emoji" and "is clearly the real image" (this is
    exactly the mistake made, twice, before switching to DOM-level checks
    instead of judging screenshots alone -- use both, don't rely on either)."""
    from PIL import Image
    im = Image.open(in_path)
    im = im.crop(box)
    if scale:
        im = im.resize(scale)
    im.save(out_path)


async def leaked_comment_check(page, extra_phrases: list[str] | None = None) -> bool:
    """True if the rendered page's visible text contains phrases that
    should only ever exist inside an HTML/JS comment. Catches exactly the
    "-- dropped a <!-- opener, a whole comment block becomes real text"
    class of bug. Add project-specific phrases (distinctive words this
    codebase's OWN comments use) via extra_phrases for a tighter check."""
    phrases = ["explicit request", "explicit follow-up", "explicit bug report",
               "found live", "real bug report"] + (extra_phrases or [])
    text = await page.evaluate("document.body.innerText")
    return any(p in text for p in phrases)


async def img_check(page, selector: str) -> list[dict]:
    """For every element matching `selector`: is it actually an <img> with
    a real src, or something else (emoji text, a background-image, nothing
    at all)? Pair this with the network log to also confirm the request
    for that src actually returned 200 -- an <img> with a 404'd src can
    still LOOK plausible in a screenshot (broken-image glyphs are easy to
    mistake for "small and blurry, probably fine" at 16px)."""
    return await page.eval_on_selector_all(
        selector,
        "els => els.map(e => ({tag: e.tagName, src: e.src || null, "
        "text: e.textContent, alt: e.alt || null}))",
    )


def write_bug_report(md_path: str, *, title: str, where: str, repro: str,
                      expected: str, actual: str, evidence: str,
                      suspected_cause: str = "unknown",
                      confidence: str = "confirmed reproducible") -> None:
    """Appends one bug entry, in the format DEEP_TESTING_METHOD.md
    describes, to `md_path` (created fresh with a header if it doesn't
    exist yet). Call once per bug found, right when you find it -- don't
    rely on remembering the details at the end of a session."""
    p = Path(md_path)
    if not p.exists():
        p.write_text("# Bugs found — simulation session\n\n", encoding="utf-8")
    entry = (
        f"### {title}\n\n"
        f"- **Where:** {where}\n"
        f"- **Repro:** {repro}\n"
        f"- **Expected:** {expected}\n"
        f"- **Actual:** {actual}\n"
        f"- **Evidence:** {evidence}\n"
        f"- **Suspected cause:** {suspected_cause}\n"
        f"- **Confidence:** {confidence}\n\n"
    )
    with p.open("a", encoding="utf-8") as f:
        f.write(entry)
