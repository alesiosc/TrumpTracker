#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
keep_trump_tabs.py  (TrumpTracker)

Failsafe for the 9223 TrumpTracker browser. Runs forever and guarantees the
REQUIRED permanent tabs are always open and ready for scraping.

Uses DOMAIN-based matching so redirects (e.g. Google Sheets -> accounts.google.com
login) don't trigger duplicate tab opening. Only opens a tab if NO existing tab
matches the target domain.

Also closes duplicate tabs (more than one page matching a required domain).
"""

import os
import sys
import time
import json
import atexit
import urllib.request
import urllib.error
import subprocess
from urllib.parse import urlparse

try:
    import websocket
    _WS_OK = True
except Exception:
    _WS_OK = False

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = 9223
LAUNCHER = os.path.join(HERE, "launch_trump_browser.py")
LOCK_FILE = os.path.join(HERE, ".trump_keepalive.lock")


def _pid_alive(pid):
    try:
        out = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}"],
            capture_output=True, text=True, timeout=10,
        ).stdout
        return str(pid) in out
    except Exception:
        return False


def acquire_lock():
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, encoding="utf-8") as fh:
                old = int(fh.read().strip())
            if old != os.getpid() and _pid_alive(old):
                print(f"[{time.strftime('%H:%M:%S')}] another keep_trump_tabs.py "
                      f"already running (PID {old}); exiting")
                sys.exit(1)
        except (ValueError, OSError):
            pass
    with open(LOCK_FILE, "w", encoding="utf-8") as fh:
        fh.write(str(os.getpid()))


def release_lock():
    try:
        if os.path.exists(LOCK_FILE):
            with open(LOCK_FILE, encoding="utf-8") as fh:
                if fh.read().strip() == str(os.getpid()):
                    os.remove(LOCK_FILE)
    except OSError:
        pass


acquire_lock()
atexit.register(release_lock)

# Each entry is (launch_url, domain_to_match).
# domain_to_match is what we look for in existing tabs — this handles
# redirects (e.g. sheets -> accounts.google.com login) without reopening.
REQUIRED = [
    ("https://truthsocial.com/@realDonaldTrump", "truthsocial.com"),
    ("https://www.tradingview.com/chart/DXfkyRhX/", "tradingview.com"),
    ("https://docs.google.com/spreadsheets/d/16L022YuhgrlxwO3aJgWg1tiWVBchdKqRYCwcxqwSbJ0", "docs.google.com"),
    ("https://script.google.com/home/projects/1oCVHEJ_MvygePajMUCqF1D0PZI2Bw6uqi6l7l1D5skaVwo-t92eU0KEI/edit", "script.google.com"),
]

POLL = 20
RELAUNCH_WAIT = 8


def _http(method, url, data=None, timeout=10):
    req = urllib.request.Request(url, data=data, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8")


def _get_json(url):
    return json.loads(_http("GET", url))


def _new_tab(target):
    _http("PUT", f"http://127.0.0.1:{PORT}/json/new?{target}")


def _close_tab(tab_id):
    _http("GET", f"http://127.0.0.1:{PORT}/json/close/{tab_id}")


def _list_tabs():
    try:
        return _get_json(f"http://127.0.0.1:{PORT}/json")
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError):
        return None


def _relaunch_browser():
    print(f"[{_ts()}] browser debug port down -> relaunching")
    flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(
        subprocess, "CREATE_NEW_PROCESS_GROUP", 0
    )
    subprocess.Popen(
        [sys.executable, LAUNCHER],
        cwd=HERE,
        creationflags=flags,
    )
    time.sleep(RELAUNCH_WAIT)


def _ts():
    import datetime as dt
    return dt.datetime.now().strftime("%H:%M:%S")


def _dismiss_restore_bubble():
    if not _WS_OK:
        return
    tabs = _list_tabs()
    if not tabs:
        return
    for t in tabs:
        if t.get("type") != "page":
            continue
        ws_url = t.get("webSocketDebuggerUrl")
        if not ws_url:
            continue
        try:
            ws = websocket.create_connection(ws_url, timeout=3)
            for evt in ("keyDown", "keyUp"):
                ws.send(json.dumps({
                    "id": 1,
                    "method": "Input.dispatchKeyEvent",
                    "params": {
                        "type": evt,
                        "key": "Escape",
                        "windowsVirtualKeyCode": 27,
                    },
                }))
            ws.close()
        except Exception:
            pass


def _tab_matches_domain(tab_url, domain):
    """Check if a tab URL matches the required domain.
    Handles Google redirects: accounts.google.com matches 'google.com' domain,
    docs.google.com matches 'google.com', etc."""
    try:
        parsed = urlparse(tab_url)
        host = parsed.netloc.lower()
        # Direct match: host ends with the domain
        if host == domain or host.endswith("." + domain):
            return True
        # accounts.google.com redirects match docs.google.com or script.google.com
        # because accounts.google.com.netloc ends with .docs.google.com? No.
        # We handle this: if the tab is on accounts.google.com and the required
        # domain is docs.google.com or script.google.com, check if the redirect
        # URL in the query string contains the target domain.
        if host == "accounts.google.com":
            if domain in tab_url:
                return True
    except Exception:
        pass
    return False


def ensure_tabs():
    tabs = _list_tabs()
    if tabs is None:
        _relaunch_browser()
        return

    _dismiss_restore_bubble()

    page_tabs = []
    for t in tabs:
        if t.get("type") != "page":
            continue
        u = t.get("url", "")
        if u.startswith("http"):
            page_tabs.append(t)

    # Close duplicates: for each required domain, keep only the first match
    seen_domains = set()
    for t in page_tabs:
        url = t.get("url", "")
        matched_domain = None
        for _, domain in REQUIRED:
            if _tab_matches_domain(url, domain):
                matched_domain = domain
                break
        if matched_domain is None:
            continue
        if matched_domain in seen_domains:
            print(f"[{_ts()}] closing duplicate tab: {url[:80]}")
            try:
                _close_tab(t["id"])
            except Exception as exc:
                print(f"[{_ts()}] close failed: {exc!r}")
        else:
            seen_domains.add(matched_domain)

    # Re-list after closing duplicates
    tabs = _list_tabs()
    if tabs is None:
        return
    open_urls = []
    for t in tabs:
        if t.get("type") != "page":
            continue
        u = t.get("url", "")
        if u.startswith("http"):
            open_urls.append(u)

    # Only open a tab if NO existing tab matches its domain
    for launch_url, domain in REQUIRED:
        if not any(_tab_matches_domain(u, domain) for u in open_urls):
            print(f"[{_ts()}] reopening missing tab ({domain}): {launch_url[:80]}")
            try:
                _new_tab(launch_url)
            except Exception as exc:
                print(f"[{_ts()}] reopen failed: {exc!r}")


def main():
    print(f"[{_ts()}] keep_trump_tabs started (monitoring {len(REQUIRED)} tabs on :{PORT})")
    while True:
        try:
            ensure_tabs()
        except Exception as exc:
            print(f"[{_ts()}] unexpected error: {exc!r}")
        time.sleep(POLL)


if __name__ == "__main__":
    main()
