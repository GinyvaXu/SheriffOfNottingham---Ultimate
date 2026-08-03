# -*- coding: utf-8 -*-
"""Auto-update support.

The repo root holds a small JSON manifest ``update.json`` describing the
latest published release::

    {
      "version": "1.2.2",
      "url": "https://github.com/GinyvaXu/SheriffOfNottingham---Ultimate/releases/download/v1.2.2/SheriffOfNottingham-Setup-1.2.2.exe",
      "notes": "..."
    }

``check_for_update()`` tries several sources in order (raw.githubusercontent,
the jsDelivr CDN mirror, then the GitHub releases API) so that slow or
blocked networks do not break the check, and returns a friendly error code
("timeout" / "network" / "unknown") instead of a raw exception string.

In frozen (exe) builds the player can download the new installer and
silently reinstall: the game exits, a small .bat in %TEMP% waits for the
process to release the exe, runs the installer (which keeps the previous
install folder because the AppId matches), relaunches the game and cleans
up after itself.
"""

import io
import json
import os
import re
import socket
import ssl
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

import version

MANIFEST_SOURCES = [
    ("raw", "https://raw.githubusercontent.com/GinyvaXu/"
            "SheriffOfNottingham---Ultimate/main/update.json"),
    ("cdn", "https://cdn.jsdelivr.net/gh/GinyvaXu/"
            "SheriffOfNottingham---Ultimate@main/update.json"),
    ("api", "https://api.github.com/repos/GinyvaXu/"
            "SheriffOfNottingham---Ultimate/releases/latest"),
]
RELEASE_PAGE_URL = ("https://github.com/GinyvaXu/"
                    "SheriffOfNottingham---Ultimate/releases")
_UA = "SheriffOfNottingham-Updater/1.0"
_DEFAULT_TIMEOUT = 12
_DOWNLOAD_TIMEOUT = 60
_DOWNLOAD_ATTEMPTS = 2


# ---------- version helpers ----------

def parse_version(s):
    """'1.2.2' -> (1, 2, 2). Handles dirty suffixes like '1.2.2-rc1'."""
    parts = re.findall(r"\d+", str(s))[:3]
    return tuple(int(x) for x in (parts + ["0", "0", "0"])[:3])


def is_newer(latest, current):
    return parse_version(latest) > parse_version(current)


def is_frozen():
    return bool(getattr(sys, "frozen", False))


# ---------- network ----------

def _fetch(url, timeout):
    req = urllib.request.Request(url, headers={"User-Agent": _UA,
                                               "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def error_code(e):
    """Map an exception to a friendly code: 'timeout' | 'network' | 'unknown'."""
    if isinstance(e, (TimeoutError, socket.timeout)):
        return "timeout"
    if isinstance(e, urllib.error.URLError):
        reason = getattr(e, "reason", None)
        if isinstance(reason, (TimeoutError, socket.timeout)):
            return "timeout"
        return "network"
    if isinstance(e, (ssl.SSLError, socket.gaierror, OSError)):
        return "network"
    return "unknown"


def fetch_manifest(url, timeout=_DEFAULT_TIMEOUT):
    """Download and parse update.json. Raises on any network/json problem."""
    data = _fetch(url, timeout)
    return json.loads(data.decode("utf-8"))


def _from_release_api(data):
    """Turn a GitHub releases/latest API response into (version, url, notes)."""
    tag = str(data.get("tag_name", "") or "").strip().lstrip("vV")
    if not tag:
        raise ValueError("empty tag")
    url = ""
    for a in (data.get("assets") or []):
        u = str(a.get("browser_download_url", "") or "")
        if u.lower().endswith(".exe"):
            url = u
            break
    if not url:
        raise ValueError("no installer asset")
    notes = str(data.get("body", "") or "")[:400].replace("\r", "")
    return tag, url, notes


def check_for_update(timeout=_DEFAULT_TIMEOUT):
    """Return a status dict, never raises.

    Keys: available, version, current, url, notes, error, detail.
    ``error`` is None on success or one of "timeout" / "network" / "unknown".
    """
    current = version.__version__
    last_err = None
    for kind, url in MANIFEST_SOURCES:
        try:
            if kind == "api":
                data = _fetch(url, timeout)
                latest, dl_url, notes = _from_release_api(json.loads(data.decode("utf-8")))
                notes_zh = ""
            else:
                man = fetch_manifest(url, timeout)
                latest = str(man.get("version", "") or "").strip()
                if not latest:
                    raise ValueError("empty manifest")
                dl_url = str(man.get("url", "") or "")
                notes = str(man.get("notes", "") or "").replace("\r", "")
                notes_zh = str(man.get("notes_zh", "") or "").replace("\r", "")
            return {"available": is_newer(latest, current),
                    "version": latest, "current": current,
                    "url": dl_url, "notes": notes, "notes_zh": notes_zh,
                    "error": None, "detail": ""}
        except Exception as e:  # noqa: BLE001 - never crash the UI thread
            last_err = e
            continue
    return {"available": False, "version": "", "current": current,
            "url": "", "notes": "", "notes_zh": "", "error": error_code(last_err),
            "detail": str(last_err) if last_err else ""}


def download_dir():
    d = os.path.join(tempfile.gettempdir(), "SheriffUpdate")
    try:
        os.makedirs(d, exist_ok=True)
    except OSError:
        d = tempfile.gettempdir()
    return d


def _download_once(url, path, timeout, progress):
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        total = int(r.headers.get("Content-Length") or 0)
        got = 0
        with io.open(path, "wb") as f:
            while True:
                chunk = r.read(65536)
                if not chunk:
                    break
                f.write(chunk)
                got += len(chunk)
                if progress:
                    progress(got, total)


def download_installer(url, dest_dir=None, progress=None, timeout=_DOWNLOAD_TIMEOUT,
                       attempts=_DOWNLOAD_ATTEMPTS):
    """Download the installer to a temp folder; returns the local path.

    ``progress`` is called as progress(got_bytes, total_bytes) when known.
    Retries ``attempts`` times; the last exception propagates to the caller.
    """
    dest_dir = dest_dir or download_dir()
    os.makedirs(dest_dir, exist_ok=True)
    fname = os.path.basename(url.split("?")[0]) or "SheriffOfNottingham-Setup.exe"
    path = os.path.join(dest_dir, fname)
    last_err = None
    for attempt in range(max(1, attempts)):
        try:
            _download_once(url, path, timeout, progress)
            return path
        except Exception as e:  # noqa: BLE001
            last_err = e
            try:
                if os.path.exists(path):
                    os.remove(path)
            except OSError:
                pass
    raise last_err


# ---------- apply / relaunch ----------

def _exe_path():
    """Path of the running executable (frozen builds only)."""
    if is_frozen():
        return sys.executable
    return None


def _launch_bat(bat_path, args=None):
    """Launch a .bat hidden and detached, so it survives this process.

    Returns the Popen handle (for pid tracking) or None when the batch
    could not be started at all.
    """
    # CREATE_NO_WINDOW runs cmd hidden (no console). DETACHED_PROCESS must NOT
    # be combined with it: per CreateProcess docs CREATE_NO_WINDOW is ignored
    # when DETACHED_PROCESS is used, which lets console children pop up
    # visible windows. CREATE_NEW_PROCESS_GROUP keeps Ctrl+C isolated.
    flags = 0x08000000  # CREATE_NO_WINDOW
    flags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    try:
        return subprocess.Popen(["cmd.exe", "/c", bat_path] + list(args or []),
                                creationflags=flags, close_fds=True, shell=False)
    except Exception:  # noqa: BLE001 - caller falls back to a manual update
        return None


_PENDING_FLAG = "update_pending.flag"
_FLAG_MAX_AGE = 600.0  # seconds; a hung batch older than this is considered stale
_BOOT_FLAG = "boot_ok.flag"  # written by the game once its GUI is up


def _pending_flag():
    return os.path.join(download_dir(), _PENDING_FLAG)


def _pid_alive(pid):
    """Best-effort Windows check whether a process id is still running."""
    if not pid:
        return False
    try:
        import ctypes
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        h = ctypes.windll.kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid))
        if not h:
            return False
        ctypes.windll.kernel32.CloseHandle(h)
        return True
    except Exception:  # noqa: BLE001 - treat unknown as not alive
        return False


def _pending_flag_state():
    """Return (pid, age_seconds) described by the pending flag.

    Returns (None, 0.0) when there is no flag file at all.  An unreadable
    or older-format flag (plain "1") yields (None, -1.0), which the caller
    treats as stale so the update can be re-scheduled.
    """
    flag = _pending_flag()
    if not os.path.exists(flag):
        return None, 0.0
    pid, ts = None, 0.0
    try:
        with io.open(flag, "r", encoding="ascii", errors="ignore") as f:
            for ln in f:
                if "=" not in ln:
                    continue
                k, v = ln.strip().split("=", 1)
                if k == "pid":
                    pid = int(v) or None
                elif k == "ts":
                    ts = float(v) or 0.0
    except Exception:  # noqa: BLE001
        return None, -1.0
    age = time.time() - ts if ts else -1.0
    return pid, age


def _flag_is_stale(pid, age):
    """True when the pending batch is no longer actually running."""
    if pid and _pid_alive(pid):
        return age > _FLAG_MAX_AGE  # batch hung for a long time
    return True  # no live batch process behind the flag -> stale


def boot_marker():
    """Path of the boot-OK marker the update batch watches for."""
    return os.path.join(download_dir(), _BOOT_FLAG)


def mark_boot_ok():
    """Write the boot-OK marker after the game initializes.

    The update batch only considers the relaunched game a success when this
    marker appears. A PyInstaller onefile boot failure (e.g. antivirus racing
    the extraction -> "Failed to load Python DLL ... python312.dll") happens
    before any Python code runs, so no marker is written and the batch retries
    with a fresh launch instead of declaring victory while an error dialog is
    stuck on screen.
    """
    try:
        p = boot_marker()
        os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
        with io.open(p, "w", encoding="ascii") as f:
            f.write("ver=%s\nts=%d\n" % (version.__version__, int(time.time())))
        return True
    except Exception:  # noqa: BLE001 - best effort only
        return False


def apply_update(installer_path, exe_path=None):
    """Schedule the silent reinstall + relaunch. Returns True on success.

    Only meaningful in frozen builds (we need the current exe path to
    relaunch after installing). Writes ``run_update.bat`` into %TEMP%.

    A guard flag prevents double-scheduling: if the player clicks install
    twice (or re-enters the update screen while a reinstall is pending),
    the second call just returns True because the first batch file is
    already running the installer.
    """
    exe_path = exe_path or _exe_path()
    if not exe_path:
        return False
    installer_path = os.path.abspath(installer_path)
    flag = _pending_flag()
    # A leftover flag (crashed / killed / blocked batch) would otherwise make
    # every later click silently "succeed" without installing anything.
    pid, age = _pending_flag_state()
    if pid is not None and not _flag_is_stale(pid, age):
        return True  # a batch is genuinely still running
    if pid is not None:
        try:
            os.remove(flag)
        except OSError:
            pass
    bat = os.path.join(download_dir(), "run_update.bat")
    with io.open(flag, "w", encoding="ascii") as f:
        f.write("pid=0\nts=%d\n" % int(time.time()))
    # %1 = game exe, %2 = installer, %3 = pending flag, %4 = boot marker
    lines = [
        '@echo off',
        'setlocal enabledelayedexpansion',
        'set "EXE=%~1"',
        'set "INST=%~2"',
        'set "FLAG=%~3"',
        'set "BOOT=%~4"',
        'set "LOG=%~dp0update.log"',
        'set "INNO=%~dp0inno_install.log"',
        'set "NAME=%~n1"',
        'echo [%date% %time%] batch started >> "%LOG%"',
        'rem wait until the old game process fully exits (a PyInstaller onefile',
        'rem process keeps its own exe open while running, so the installer',
        'rem cannot replace it until the process is gone)',
        'rem NOTE: hidden PowerShell is used instead of tasklist/find: console',
        'rem tools spawned from a hidden cmd allocate visible console windows,',
        'rem and find can block forever on an open pipe. -WindowStyle Hidden',
        'rem shows no window and never reads stdin.',
        'set /a n=0',
        ':wait_exit',
        'powershell -NoProfile -WindowStyle Hidden -Command "if (Get-Process -Name \'%NAME%\' -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"',
        'if errorlevel 1 goto exit_done',
        'set /a n+=1',
        'if !n! lss 20 ( powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2" & goto wait_exit )',
        'rem give up waiting: force-kill so the installer can replace the exe',
        'echo [%date% %time%] game did not exit, forcing kill >> "%LOG%"',
        'powershell -NoProfile -WindowStyle Hidden -Command "Stop-Process -Name \'%NAME%\' -Force -ErrorAction SilentlyContinue"',
        'powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2"',
        ':exit_done',
        'rem silent install, retry while the exe is still locked',
        'set /a n=0',
        ':install',
        'echo [%date% %time%] running installer >> "%LOG%"',
        '"%INST%" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /LOG="%INNO%"',
        'set ec=!errorlevel!',
        'echo [%date% %time%] installer exit code=!ec! >> "%LOG%"',
        'if !ec! neq 0 (',
        '  set /a n+=1',
        '  if !n! lss 3 ( powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 3" & goto install )',
        '  echo [%date% %time%] install failed after retries, opening releases page >> "%LOG%"',
        '  start "" "https://github.com/GinyvaXu/SheriffOfNottingham---Ultimate/releases"',
        ')',
        'rem launch the new game and watch for a real boot. The game writes',
        'rem %BOOT% once its GUI is up. The first boot of a fresh onefile exe',
        'rem can be raced by antivirus scans that break the onefile extraction',
        'rem (the classic "Failed to load Python DLL ... python312.dll" bootloader',
        'rem error). So we give the AV a head start, wait for the marker, and',
        'rem retry several times; a process object alone is NOT proof of a boot',
        'rem (a stuck bootloader error dialog would fool that check).',
        'set /a n=0',
        ':launch',
        'set /a n+=1',
        'if !n! gtr 6 (',
        '  echo [%date% %time%] could not boot new game after 6 tries >> "%LOG%"',
        '  start "" "https://github.com/GinyvaXu/SheriffOfNottingham---Ultimate/releases"',
        '  goto end',
        ')',
        'echo [%date% %time%] launch try !n! >> "%LOG%"',
        'powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 8"',
        'if exist "%BOOT%" del "%BOOT%" >nul 2>&1',
        'if exist "%EXE%" powershell -NoProfile -WindowStyle Hidden -Command "Start-Process -FilePath \'%EXE%\' -WorkingDirectory \'%~dp1\'"',
        'set /a w=0',
        ':watch',
        'powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 3"',
        'if exist "%BOOT%" ( echo [%date% %time%] new game booted OK >> "%LOG%" & goto end )',
        'powershell -NoProfile -WindowStyle Hidden -Command "if (Get-Process -Name \'%NAME%\' -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"',
        'if errorlevel 1 ( echo [%date% %time%] boot failed on try !n! >> "%LOG%" & goto launch )',
        'set /a w+=3',
        'if !w! lss 45 goto watch',
        'rem process alive but no boot marker for 45s: a bootloader error dialog',
        'rem ("Failed to load Python DLL ... python312.dll", Smart App Control,',
        'rem AV) is likely stuck on screen. A healthy game writes %BOOT% seconds',
        'rem after launch, so kill the process (this dismisses any error dialog)',
        'rem and relaunch for another try.',
        'echo [%date% %time%] alive but no boot marker, killing and retrying >> "%LOG%"',
        'powershell -NoProfile -WindowStyle Hidden -Command "Stop-Process -Name \'%NAME%\' -Force -ErrorAction SilentlyContinue"',
        'goto launch',
        ':end',
        'echo [%date% %time%] batch finished >> "%LOG%"',
        'del "%INST%" >nul 2>&1',
        'del "%FLAG%" >nul 2>&1',
        '(goto) 2>nul & del "%~f0"',
    ]
    with io.open(bat, "w", encoding="ascii", errors="replace", newline="") as f:
        f.write("\r\n".join(lines) + "\r\n")
    # %1 = exe, %2 = installer, %3 = pending flag, %4 = boot marker the
    # relaunched game writes once its GUI is up (see main.py).
    proc = _launch_bat(bat, [exe_path, installer_path, flag, boot_marker()])
    if proc is None:
        try:
            os.remove(flag)
        except OSError:
            pass
        return False
    # Record the batch pid so a later click can tell a running batch apart
    # from a stale flag left behind by a killed/interrupted one.
    with io.open(flag, "w", encoding="ascii") as f:
        f.write("pid=%d\nts=%d\n" % (proc.pid, int(time.time())))
    return True


def open_release_page():
    """Open the GitHub releases page in the default browser."""
    import webbrowser
    webbrowser.open(RELEASE_PAGE_URL)