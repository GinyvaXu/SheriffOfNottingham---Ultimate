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
    notes = str(data.get("body", "") or "")[:400]
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
            else:
                man = fetch_manifest(url, timeout)
                latest = str(man.get("version", "") or "").strip()
                if not latest:
                    raise ValueError("empty manifest")
                dl_url = str(man.get("url", "") or "")
                notes = str(man.get("notes", "") or "")
            return {"available": is_newer(latest, current),
                    "version": latest, "current": current,
                    "url": dl_url, "notes": notes, "error": None,
                    "detail": ""}
        except Exception as e:  # noqa: BLE001 - never crash the UI thread
            last_err = e
            continue
    return {"available": False, "version": "", "current": current,
            "url": "", "notes": "", "error": error_code(last_err),
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


def _launch_bat(bat_path):
    """Launch a .bat hidden and detached, so it survives this process."""
    flags = 0x08000000  # CREATE_NO_WINDOW
    flags |= getattr(subprocess, "DETACHED_PROCESS", 0)
    flags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    subprocess.Popen(["cmd.exe", "/c", bat_path], creationflags=flags,
                     close_fds=True, shell=False)
    return True


_PENDING_FLAG = "update_pending.flag"


def _pending_flag():
    return os.path.join(download_dir(), _PENDING_FLAG)


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
    if os.path.exists(flag):
        return True  # another install is already running
    bat = os.path.join(download_dir(), "run_update.bat")
    with io.open(flag, "w", encoding="ascii") as f:
        f.write("1")
    lines = [
        "@echo off",
        "setlocal enabledelayedexpansion",
        # give the game process a moment to fully exit and release the exe
        "ping -n 5 127.0.0.1 >nul",
        # retry the silent install a few times in case the exe is still locked
        "set /a n=0",
        ":install",
        '"{0}" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART'.format(installer_path),
        "if errorlevel 1 (",
        "  set /a n+=1",
        "  if !n! lss 3 ( ping -n 3 127.0.0.1 >nul & goto install )",
        ")",
        # wait until the game exe is really there before launching it
        "for /l %%i in (1,1,40) do (",
        '  if exist "{0}" goto launch'.format(exe_path),
        "  ping -n 1 127.0.0.1 >nul",
        ")",
        ":launch",
        'start "" "{0}"'.format(exe_path),
        'del "{0}" >nul 2>&1'.format(installer_path),
        'del "{0}" >nul 2>&1'.format(flag),
        "(goto) 2>nul & del \"%~f0\"",
    ]
    with io.open(bat, "w", encoding="ascii", errors="replace") as f:
        f.write("\r\n".join(lines) + "\r\n")
    ok = _launch_bat(bat)
    if not ok:
        try:
            os.remove(flag)
        except OSError:
            pass
        return False
    return True


def open_release_page():
    """Open the GitHub releases page in the default browser."""
    import webbrowser
    webbrowser.open(RELEASE_PAGE_URL)