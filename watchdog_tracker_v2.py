"""
TrumpTracker Watchdog - runs every 1 minute via Scheduled Task.
Silent when browser+tracker are alive. Restarts what's broken.

Detection:
  1. Chrome CDP port 9224 alive (TrumpTracker's isolated browser)
  2. tracker.py process alive (the scraper loop)

ISOLATION CONTRACT: owns ONLY port 9224 + its profile. Never touches 9223 /
D:\\MyPythonProjects_2\\browser_data (trading-daemons). Auto-cleans only
stale tracker.py processes (by commandline), never a global chrome.exe kill.
"""
import os
import subprocess
import sys
import socket
import datetime
import time

PROJECT_DIR = r"D:\MyPythonProjects_2\TrumpTracker + PORTABLE - ORIGINAL"
VENV_PYTHON = os.path.join(PROJECT_DIR, "venv", "Scripts", "python.exe")
TRACKER_SCRIPT = os.path.join(PROJECT_DIR, "tracker.py")
PID_FILE = os.path.join(PROJECT_DIR, "tracker.pid")
LOG_FILE = os.path.join(PROJECT_DIR, "watchdog_tracker.log")
PORT = 9224


def log(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def read_pid():
    try:
        with open(PID_FILE) as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return None


def pid_alive(pid):
    try:
        r = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
            capture_output=True, text=True, timeout=10
        )
        return "No tasks" not in r.stdout and str(pid) in r.stdout
    except Exception:
        return False


def port_in_use(port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        ok = s.connect_ex(("127.0.0.1", port)) == 0
        s.close()
        return ok
    except Exception:
        return False


def kill_stale_tracker_processes():
    killed = 0
    try:
        ps_cmd = (
            'Get-CimInstance Win32_Process -Filter "Name = \'python.exe\'" | '
            'Where-Object { $_.CommandLine -match \'tracker.py\' } | '
            'ForEach-Object { $_.ProcessId }'
        )
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True, text=True, timeout=15
        )
        current_pid = read_pid()
        for line in r.stdout.splitlines():
            line = line.strip()
            if line.isdigit():
                pid = int(line)
                if current_pid and pid == current_pid:
                    continue
                subprocess.run(
                    ["taskkill", "/F", "/PID", str(pid)],
                    capture_output=True, timeout=10
                )
                killed += 1
    except Exception as e:
        log(f"  Cleanup error (non-fatal): {e}")
    return killed


def start_tracker():
    os.chdir(PROJECT_DIR)
    try:
        proc = subprocess.Popen(
            [VENV_PYTHON, TRACKER_SCRIPT],
            cwd=PROJECT_DIR,
            creationflags=subprocess.CREATE_NO_WINDOW,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        with open(PID_FILE, "w") as f:
            f.write(str(proc.pid))
        time.sleep(3)
        return True
    except Exception as e:
        log(f"FAILED to start tracker: {e}")
        return False


def start_browser():
    try:
        launcher = os.path.join(PROJECT_DIR, "launch_trump_browser.py")
        flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(
            subprocess, "CREATE_NEW_PROCESS_GROUP", 0
        )
        subprocess.Popen(
            [sys.executable, launcher],
            cwd=PROJECT_DIR,
            creationflags=flags,
        )
        time.sleep(8)
        return port_in_use(PORT)
    except Exception as e:
        log(f"FAILED to start browser: {e}")
        return False


LOCK_FILE = os.path.join(PROJECT_DIR, "watchdog_tracker.lock")


def acquire_lock():
    # Single-instance guard: only one watchdog may manage the 9224 browser at a time.
    try:
        fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        return True
    except FileExistsError:
        return False


def release_lock():
    try:
        os.remove(LOCK_FILE)
    except OSError:
        pass


if __name__ == "__main__":
    if not acquire_lock():
        # Another watchdog instance holds the lock; exit silently.
        sys.exit(0)
    try:
        browser_ok = port_in_use(PORT)

        pid = read_pid()
        tracker_ok = pid and pid_alive(pid)

        if browser_ok and tracker_ok:
            sys.exit(0)

        if not browser_ok:
            log("WATCHDOG: Browser port 9224 is DOWN. Restarting browser...")
            if start_browser():
                log("WATCHDOG: Browser restarted on port 9224")
            else:
                log("WATCHDOG: CRITICAL - Failed to restart browser!")

        if not tracker_ok:
            log("WATCHDOG: Tracker NOT running. Restarting...")
            kill_stale_tracker_processes()
            if start_tracker():
                log("WATCHDOG: Tracker started (PID in tracker.pid)")
            else:
                log("WATCHDOG: CRITICAL - Failed to start tracker!")
                sys.exit(1)
    except Exception as e:
        log(f"WATCHDOG: UNHANDLED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        release_lock()
