#!/usr/bin/env python3
"""Launch TrumpTracker debug Chrome on port 9223, independent of tracker.py.

Pattern mirrors launch_mq_browser.py: starts Chrome with --remote-debugging-port,
a dedicated profile, and the required tabs. Clears crash markers so the
"Restore pages?" bubble never blocks startup.
"""
import os
import json
import subprocess
import sys
import time
import urllib.request

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROFILE = r"C:\Users\Cameron\AppData\Local\Temp\DrissionPage\userData\9223"
PREF_FILE = os.path.join(PROFILE, "Default", "Preferences")
PORT = 9223

TABS = [
    "https://truthsocial.com/@realDonaldTrump",
    "https://www.tradingview.com/chart/DXfkyRhX/",
    "https://docs.google.com/spreadsheets/d/16L022YuhgrlxwO3aJgWg1tiWVBchdKqRYCwcxqwSbJ0/edit?gid=688023582#gid=688023582",
    "https://script.google.com/home/projects/1oCVHEJ_MvygePajMUCqF1D0PZI2Bw6uqi6l7l1D5skaVwo-t92eU0KEI/edit",
]


def port_open():
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/version", timeout=2)
        return True
    except Exception:
        return False


def clear_crash_marker():
    try:
        if not os.path.exists(PREF_FILE):
            return
        with open(PREF_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        data.setdefault("profile", {})["exit_type"] = "Normal"
        data.setdefault("session", {})["restore_on_startup"] = 1
        with open(PREF_FILE, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
        print("[INFO] cleared crash marker (exit_type=Normal)")
    except Exception as exc:
        print(f"[WARN] could not clear crash marker: {exc!r}")


def launch_chrome():
    if not os.path.exists(CHROME):
        print(f"[ERROR] Chrome not found: {CHROME}")
        sys.exit(1)

    os.makedirs(PROFILE, exist_ok=True)
    clear_crash_marker()

    args = [
        CHROME,
        f"--remote-debugging-port={PORT}",
        f"--user-data-dir={PROFILE}",
        "--no-first-run",
        "--disable-default-apps",
        "--start-maximized",
        "--new-window",
        "--hide-crash-restore-bubble",
        "--remote-allow-origins=*",
        "--disable-notifications",
        "--disable-popup-blocking",
    ] + TABS

    print(f"[INFO] Launching Chrome on port {PORT}...")
    flags = getattr(subprocess, 'DETACHED_PROCESS', 0) | getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0)
    subprocess.Popen(args, shell=False, creationflags=flags)
    time.sleep(6)


def main():
    if port_open():
        print(f"[INFO] TrumpTracker debug browser already running on port {PORT}.")
        return

    launch_chrome()

    for i in range(20):
        if port_open():
            break
        time.sleep(1)
    else:
        print(f"[ERROR] Chrome debug port {PORT} did not open.")
        sys.exit(1)

    print(f"[INFO] TrumpTracker debug browser open on port {PORT} with {len(TABS)} tabs:")
    for url in TABS:
        print(f"  - {url}")
    print("[INFO] tab-keepalive is owned by keep_trump_tabs.py (run separately).")

    # Launch TradingView Connect Watcher (auto-clicks "Connect" popup on TV chart)
    watcher = r"D:\MyPythonProjects_2\AIO_internals_equities_ma_x3_indicator\docs\13-TS-DASH-v4.0\Module-04 - INDICATORS\tradingview_connect_watcher.py"
    if os.path.exists(watcher):
        subprocess.Popen(
            [sys.executable, watcher],
            cwd=os.path.dirname(watcher),
            creationflags=getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )
        print("[INFO] TradingView Connect Watcher launched.")


if __name__ == "__main__":
    main()
