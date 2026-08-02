# -*- coding: utf-8 -*-
"""Bundled-mod compatibility checks for the current game build.

Every shipped mod must:
  * declare a mod.json version equal to the game version (v1.6.2),
  * still register() against the current engine API without raising,
  * be present in the market manifest with the same version,
  * have a fresh zip in mods_pack/ (used by the in-game mod market).
"""
import importlib.util
import io
import json
import os
import sys
import zipfile

import version

ROOT = os.path.dirname(os.path.abspath(__file__))
MOD_DIR = os.path.join(ROOT, "mods")
PACK_DIR = os.path.join(ROOT, "mods_pack")
MARKET = os.path.join(ROOT, "mods_market.json")

MOD_FOLDERS = sorted(
    name for name in os.listdir(MOD_DIR)
    if os.path.isdir(os.path.join(MOD_DIR, name))
    and os.path.isfile(os.path.join(MOD_DIR, name, "mod.json"))
)


def _load_manifest(folder):
    with io.open(os.path.join(MOD_DIR, folder, "mod.json"), encoding="utf-8-sig") as f:
        return json.load(f)


def _fresh_register(folder):
    """Run a mod's register() against a freshly imported engine."""
    for modname in ("game", "gui", "lang", "mods"):
        sys.modules.pop(modname, None)
    import game  # noqa: F401
    import gui  # noqa: F401
    import lang  # noqa: F401
    import mods
    py = os.path.join(MOD_DIR, folder, "mod.py")
    if not os.path.isfile(py):
        return  # manifest-only mod (no code to run)
    spec = importlib.util.spec_from_file_location("modcompat_" + folder, py)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    register = getattr(mod, "register", None)
    if callable(register):
        register(mods.ModAPI(folder, os.path.join(MOD_DIR, folder)))


def test_all_mod_versions_match_game():
    for folder in MOD_FOLDERS:
        man = _load_manifest(folder)
        assert str(man.get("version")) == version.__version__, (
            folder, man.get("version"), version.__version__)


def test_all_mods_register_cleanly():
    for folder in MOD_FOLDERS:
        _fresh_register(folder)  # raises on any API incompatibility


def test_market_manifest_versions_and_zips():
    with io.open(MARKET, encoding="utf-8") as f:
        market = json.load(f)
    market_mods = {m["id"]: m for m in market["mods"]}
    for folder in MOD_FOLDERS:
        man = _load_manifest(folder)
        mid = man.get("id") or folder
        mm = market_mods.get(mid)
        if mm is None:
            continue  # example_mod is local-only, not in the market
        assert str(mm.get("version")) == version.__version__, (mid, mm.get("version"))
        zpath = os.path.join(PACK_DIR, str(mm.get("folder", "")) + ".zip")
        assert os.path.isfile(zpath), zpath
        with zipfile.ZipFile(zpath) as z:
            names = set(z.namelist())
            assert "mod.json" in names and "mod.py" in names, (zpath, names)
            with z.open("mod.json") as f:
                zman = json.load(io.TextIOWrapper(f, encoding="utf-8"))
        assert str(zman.get("version")) == version.__version__, (zpath, zman.get("version"))
