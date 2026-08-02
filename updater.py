# -*- coding: utf-8 -*-
"""Auto-update support.

The repo root holds a small JSON manifest ``update.json`` describing the
latest published release::

    {
      "version": "1.2.1",
      "url": "https://github.com/GinyvaXu/SheriffOfNottingham---Ultimate/releases/download/v1.2.1/SheriffOfNottingham-Setup-1.2.1.exe",
      "notes": "..."
    }

``check_for_update()`` fetches this manifest from raw.githubusercontent.com
and compares versions. In frozen (exe) builds the player can download the new
installer and silently reinstall: the game exits, a small .bat in %TEMP%
waits for the process to release the exe, runs the installer (which keeps the
previous install folder because the AppId matches), relaunches the game and
cleans up after itself.
"""

import io
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request

import version

MANIFEST_URL = ("https://raw.githubusercontent.com/GinyvaXu/"
                "SheriffOfNottingham---Ultimate/main/update.json")
RELEASE_PAGE_URL = ("https://github.com/GinyvaXu/"
                    "SheriffOfNottingham---Ultimate/releases")
_UA = "SheriffOfNottingham-Updater/1.0"
_DEFAULT_TIMEOUT = 8
_DOWNLOAD_TIMEOUT = 60


# ---------- version helpers ----------

def parse_version(s):
    """'1.2.1' -> (1, 2, 1). Handles dirty suffixes like '1.2.1-rc1'."""
    parts = re.findall(r"\d+", str(s))[:3]
    return tuple(int(x) for x in (parts + ["0", "0", "0"])[:3])


def is_newer(latest, current):
    return parse_version(latest) > parse_version(current)


def is_frozen():
    return bool(getattr(sys, "frozen", False))


# ---------- network ----------

def _fetch(url, timeout):
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch_manifest(url=MANIFEST_URL, timeout=_DEFAULT_TIMEOUT):
    """Download and parse update.json. Raises on any network/json problem."""
    data = _fetch(url, timeout)
    return json.loads(data.decode("utf-8"))


def check_for_update(url=MANIFEST_URL, timeout=_DEFAULT_TIMEOUT):
    """Return a status dict, never raises.

    Keys: available, version, current, url, notes, error.
    """
    current = version.__version__
    try:
        man = fetch_manifest(url, timeout)
        latest = str(man.get("version", "") or "").strip()
        if not latest:
            return {"available": False, "version": "", "current": current,
                    "url": "", "notes": "", "error": "empty manifest"}
        return {"available": is_newer(latest, current),
                "version": latest, "current": current,
                "url": str(man.get("url", "") or ""),
                "notes": str(man.get("notes", "") or ""),
                "error": None}
    except Exception as e:  # noqa: BLE001 - never crash the UI thread
        return {"available": False, "version": "", "current": current,
                "url": "", "notes": "", "error": str(e)}


def download_dir():
    d = os.path.join(tempfile.gettempdir(), "SheriffUpdate")
    try:
        os.makedirs(d, exist_ok=True)
    except OSError:
        d = tempfile.gettempdir()
    return d


def download_installer(url, dest_dir=None, progress=None, timeout=_DOWNLOAD_TIMEOUT):
    """Download the installer to a temp folder; returns the local path.

    ``progress`` is called as progress(got_bytes, total_bytes) when known.
    """
    dest_dir = dest_dir or download_dir()
    os.makedirs(dest_dir, exist_ok=True)
    fname = os.path.basename(url.split("?")[0]) or "SheriffOfNottingham-Setup.exe"
    path = os.path.join(dest_dir, fname)
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
    return path


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


def apply_update(installer_path, exe_path=None):
    """Schedule the silent reinstall + relaunch. Returns True on success.

    Only meaningful in frozen builds (we need the current exe path to
    relaunch after installing). Writes ``run_update.bat`` into %TEMP%.
    """
    exe_path = exe_path or _exe_path()
    if not exe_path:
        return False
    installer_path = os.path.abspath(installer_path)
    bat = os.path.join(download_dir(), "run_update.bat")
    lines = [
        "@echo off",
        # give the game process a moment to fully exit and release the exe
        "ping -n 4 127.0.0.1 >nul",
        '"{0}" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART'.format(installer_path),
        'start "" "{0}"'.format(exe_path),
        'del "{0}"'.format(installer_path),
        "(goto) 2>nul & del \"%~f0\"",
    ]
    with io.open(bat, "w", encoding="ascii", errors="replace") as f:
        f.write("\r\n".join(lines) + "\r\n")
    return _launch_bat(bat)


def open_release_page():
    """Open the GitHub releases page in the default browser."""
    import webbrowser
    webbrowser.open(RELEASE_PAGE_URL)
