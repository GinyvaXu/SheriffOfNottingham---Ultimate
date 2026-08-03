# -*- coding: utf-8 -*-
"""Mod market: remote manifest + one-click download & install of mods.

The manifest lives in the game repo (mods_market.json) and is reachable from
both raw.githubusercontent and the jsDelivr CDN, mirroring the update-check
design. Each entry points at a small zip (mods_pack/<folder>.zip) containing
mod.json + mod.py. Zips are installed into the effective mods folder (the
per-user %%APPDATA%% fallback is used automatically when the install dir is
not writable). Text-only reskin mods affect only the local client: the server
only ever sees canonical card type keys.
"""

import io
import json
import os
import tempfile
import urllib.request
import zipfile

import mods
import updater

_RAW_MANIFEST = ("https://raw.githubusercontent.com/GinyvaXu/"
                 "SheriffOfNottingham---Ultimate/main/mods_market.json")
MANIFEST_SOURCES = [
    "https://ghfast.top/" + _RAW_MANIFEST,
    _RAW_MANIFEST,
    "https://ghproxy.net/" + _RAW_MANIFEST,
    "https://gh.llkk.cc/" + _RAW_MANIFEST,
    "https://gh-proxy.com/" + _RAW_MANIFEST,
    "https://cdn.jsdelivr.net/gh/GinyvaXu/"
    "SheriffOfNottingham---Ultimate@main/mods_market.json",
]
_UA = "SheriffOfNottingham-Market/1.0"
_DEFAULT_TIMEOUT = 12
_DOWNLOAD_TIMEOUT = 60
_DOWNLOAD_ATTEMPTS = 2


def _fetch(url, timeout):
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch_market(timeout=_DEFAULT_TIMEOUT):
    """Return (mods_list, error). error is None or a friendly error code."""
    last = None
    for url in MANIFEST_SOURCES:
        try:
            data = _fetch(url, timeout)
            man = json.loads(data.decode("utf-8"))
            return list(man.get("mods") or []), None
        except Exception as e:  # noqa: BLE001 - never crash the UI thread
            last = e
    return [], updater.error_code(last)


def _download_once(url, path, timeout):
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        with io.open(path, "wb") as f:
            while True:
                chunk = r.read(65536)
                if not chunk:
                    break
                f.write(chunk)


def _download_zip(info, timeout=_DOWNLOAD_TIMEOUT):
    """Download a mod zip into %TEMP%; returns the local path (raises on fail)."""
    dest = os.path.join(tempfile.gettempdir(), "SheriffMods")
    os.makedirs(dest, exist_ok=True)
    # GitHub mirrors (url2 + proxy variants) are preferred over the jsDelivr
    # CDN (url), whose GitHub cache can lag behind and whose size limit rules
    # out bigger zips.
    urls = []
    for key in ("url2", "url"):
        u = info.get(key)
        if u:
            urls.extend(updater.mirror_urls(u))
    fname = str(info.get("folder") or info.get("id") or "mod") + ".zip"
    path = os.path.join(dest, fname)
    last_err = None
    for _ in range(_DOWNLOAD_ATTEMPTS):
        for url in urls:
            try:
                _download_once(url, path, timeout)
                return path
            except Exception as e:  # noqa: BLE001
                last_err = e
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError:
            pass
    raise last_err


def install_mod(info, base=None, timeout=_DOWNLOAD_TIMEOUT):
    """Download + extract a mod zip into the mods base.

    Returns (ok, msg); msg is empty on success. Never raises.
    """
    base = base or mods.effective_mods_base()
    folder = str(info.get("folder") or info.get("id") or "mod")
    try:
        zip_path = _download_zip(info, timeout)
        dest = os.path.join(base, folder)
        os.makedirs(dest, exist_ok=True)
        with zipfile.ZipFile(zip_path) as z:
            for name in z.namelist():
                clean = name.replace("\\", "/")
                if clean.endswith("/") or not clean:
                    continue
                if ".." in clean.split("/"):
                    continue
                target = os.path.join(dest, clean)
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with z.open(name) as src, io.open(target, "wb") as out:
                    out.write(src.read())
        if not os.path.isfile(os.path.join(dest, "mod.json")):
            return False, "zip has no mod.json"
        try:
            if os.path.exists(zip_path):
                os.remove(zip_path)
        except OSError:
            pass
        return True, ""
    except Exception as e:  # noqa: BLE001 - report to the UI instead of crashing
        return False, str(e)


def local_status(market_mod, base=None):
    """Classify a market mod locally: ('missing'|'installed'|'update', ver)."""
    base = base or mods.effective_mods_base()
    folder = str(market_mod.get("folder") or market_mod.get("id") or "")
    ver = ""
    target = os.path.join(base, folder) if folder else ""
    for info in mods.list_all_mods(base):
        if target and os.path.normpath(info["folder"]) == os.path.normpath(target):
            ver = str(info.get("version") or "")
            break
    if not ver:
        return "missing", ""
    if updater.is_newer(str(market_mod.get("version", "0")), ver):
        return "update", ver
    return "installed", ver
