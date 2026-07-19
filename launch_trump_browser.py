#!/usr/bin/env python3
"""Launch TrumpTracker's isolated Chrome on port 9224 (own profile).

ISOLATION CONTRACT: this launcher owns ONLY port 9224 + its profile. Never touch
port 9223 / D:\\MyPythonProjects_2\\browser_data (trading-daemons). Opens only
Truth Social; trading-daemons owns TradingView/Sheets/Apps Script on 9223.
"""
import os
import json
import subprocess
import sys
import time
import urllib.request

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROFILE = r"D:\MyPythonProjects_2\browser_data_trumptracker"
PREF_FILE = os.path.join(PROFILE, "Default", "Preferences")
PORT = 9224

# TrumpTracker owns ONLY Truth Social. Tracker.py creates ChatGPT/X tabs on demand.
# Trading-daemons owns TradingView/Sheets/Apps Script on port 9223 — do NOT open here.
TABS = [
    "https://truthsocial.com/@realDonaldTrump",
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


def clear_maximized_state():
    # Chrome remembers the last window state in Preferences and restores it on
    # launch, which overrides --start-minimized. Force a normal (non-maximized)
    # placement so the browser opens minimized to the taskbar, not maximized.
    try:
        if not os.path.exists(PREF_FILE):
            return
        with open(PREF_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        wp = data.setdefault("browser", {}).setdefault("window_placement", {})
        wp["maximized"] = False
        wp["type"] = "normal"
        wp["left"] = 0
        wp["top"] = 0
        wp["right"] = 420
        wp["bottom"] = 320
        with open(PREF_FILE, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
        print("[INFO] cleared maximized window state (forced normal/minimized)")
    except Exception as exc:
        print(f"[WARN] could not clear maximized state: {exc!r}")


def minimize_chrome_window(pid: int) -> None:
    # Chrome's saved window state can override --start-minimized, so force the
    # main window minimized via Win32. The window stays as a taskbar icon.
    try:
        import ctypes
        user32 = ctypes.windll.user32
        SW_MINIMIZE = 6
        psapi = ctypes.windll.psapi if hasattr(ctypes.windll, "psapi") else None
        # enumerate windows of this process
        EnumWindows = user32.EnumWindows
        GetWindowThreadProcessId = user32.GetWindowThreadProcessId
        IsWindowVisible = user32.IsWindowVisible

        class Info:
            found = 0

        def cb(hwnd, lparam):
            pid_buf = ctypes.c_int(0)
            GetWindowThreadProcessId(hwnd, ctypes.byref(pid_buf))
            if pid_buf.value == pid and IsWindowVisible(hwnd):
                user32.ShowWindowAsync(hwnd, SW_MINIMIZE)
                Info.found += 1
            return 1

        EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_int)(cb), 0)
        if Info.found:
            print(f"[INFO] minimized Chrome window(s) for PID {pid}")
        else:
            print(f"[WARN] no visible Chrome window found to minimize for PID {pid}")
    except Exception as exc:
        print(f"[WARN] could not minimize Chrome window: {exc!r}")


def launch_chrome():
    if not os.path.exists(CHROME):
        print(f"[ERROR] Chrome not found: {CHROME}")
        sys.exit(1)

    os.makedirs(PROFILE, exist_ok=True)
    clear_crash_marker()
    clear_maximized_state()

    args = [
        CHROME,
        f"--remote-debugging-port={PORT}",
        f"--user-data-dir={PROFILE}",
        "--no-first-run",
        "--disable-default-apps",
        "--start-minimized",
        "--new-window",
        "--hide-crash-restore-bubble",
        "--remote-allow-origins=*",
        "--disable-notifications",
        "--disable-popup-blocking",
    ] + TABS

    print(f"[INFO] Launching Chrome on port {PORT}...")
    flags = getattr(subprocess, 'DETACHED_PROCESS', 0) | getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0)
    proc = subprocess.Popen(args, shell=False, creationflags=flags)
    time.sleep(6)
    minimize_chrome_window(proc.pid)


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
    print("[INFO] Tab enforcement is owned by tracker.py / watchdog_tracker_v2.py (keep_trump_tabs.py stays disabled).")
    print("[INFO] TradingView Connect Watcher is NOT launched here: the TV chart lives on port 9223 (trading-daemons).")


if __name__ == "__main__":
    main()
