# -*- coding: utf-8 -*-
"""Mod loader.

Each mod is a subfolder of the ``mods/`` directory (next to the executable in
frozen builds, next to this file when running from source). A mod consists of:

    mod.json   -- manifest:
        {
          "id": "my_mod",            # unique id (folder name is used if missing)
          "name": "My Mod",
          "version": "0.1.0",
          "description": "...",
          "enabled": true            # set false to disable without deleting
        }
    mod.py     -- optional Python code. If it defines ``register(api)`` it is
                  called at startup with a ModAPI object.
    assets/    -- optional extra files (currently unused by the engine, but
                  mod code can read them via the folder path).

The ModAPI lets a mod add card types (legal / contraband / royal), set colors,
or patch engine attributes, e.g.::

    def register(api):
        api.add_contraband("TEA", "Tea", "\u8336\u53f6", value=5, fine=3,
                           cnt3=8, cnt6=12, color=(90, 160, 120))
        api.patch("game", "HAND_SIZE", 7)          # modify the game itself

All players in a room should install the same content mods (the server drives
the rules; clients need the names/colors to render cards).
"""

import importlib.util
import io
import json
import os
import shutil
import sys

import game
import gui
import lang

MODS_DIR = "mods"

# Snapshot of the canonical card names taken before any mod registers,
# used by text-only reskin mods (api.rename) to map server messages.
_BASE_EN = {}

_MODULES = {"game": game, "gui": gui, "lang": lang}


class ModAPI:
    """Functions exposed to a mod's register(api)."""

    def __init__(self, mod_id, folder):
        self.mod_id = mod_id
        self.folder = folder

    # ---------- helpers ----------

    def _sync_names(self, key, name_en, name_zh):
        game.TYPE_EN[key] = name_en
        game.TYPE_ZH[key] = name_zh
        lang.TYPE_ZH[key] = name_zh

    def _rebuild_all_types(self):
        game.ALL_TYPES[:] = game.LEGAL + game.CONTRABAND + game.ROYAL_TYPES

    # ---------- content ----------

    def add_legal(self, key, name_en, name_zh, value, fine=None, cnt3=0, cnt6=0,
                  color=None, king_bonus=0, queen_bonus=0):
        """Add a new legal goods type (declarable, no confiscation)."""
        key = str(key).upper()
        if key in game.GOODS or key in game.ROYAL_GOODS:
            raise ValueError(f"[{self.mod_id}] goods key {key} already exists")
        game.GOODS[key] = {"value": int(value),
                           "fine": int(value if fine is None else fine),
                           "cnt3": int(cnt3), "cnt6": int(cnt6)}
        if key not in game.LEGAL:
            game.LEGAL.append(key)
        game.KING_BONUS[key] = int(king_bonus)
        game.QUEEN_BONUS[key] = int(queen_bonus)
        self._sync_names(key, name_en, name_zh)
        if color:
            gui.TYPE_COLOR[key] = tuple(color)
        self._rebuild_all_types()

    def add_contraband(self, key, name_en, name_zh, value, fine=None, cnt3=0,
                       cnt6=0, color=None):
        """Add a new contraband type (cannot be declared, confiscated)."""
        key = str(key).upper()
        if key in game.GOODS or key in game.ROYAL_GOODS:
            raise ValueError(f"[{self.mod_id}] goods key {key} already exists")
        game.GOODS[key] = {"value": int(value),
                           "fine": int(value if fine is None else fine),
                           "cnt3": int(cnt3), "cnt6": int(cnt6)}
        if key not in game.CONTRABAND:
            game.CONTRABAND.append(key)
        self._sync_names(key, name_en, name_zh)
        if color:
            gui.TYPE_COLOR[key] = tuple(color)
        self._rebuild_all_types()

    def add_royal(self, key, name_en, name_zh, of, equals, value, fine=None,
                  cnt3=0, cnt6=0, color=None):
        """Add a royal goods card (contraband that counts as `equals` legal)."""
        key = str(key).upper()
        of = str(of).upper()
        if key in game.GOODS or key in game.ROYAL_GOODS:
            raise ValueError(f"[{self.mod_id}] goods key {key} already exists")
        if of not in game.LEGAL:
            raise ValueError(f"[{self.mod_id}] royal 'of' type {of} is not legal")
        game.ROYAL_GOODS[key] = {"of": of, "equals": int(equals),
                                 "value": int(value),
                                 "fine": int(value if fine is None else fine),
                                 "cnt3": int(cnt3), "cnt6": int(cnt6)}
        if key not in game.ROYAL_TYPES:
            game.ROYAL_TYPES.append(key)
        game.ROYAL_TYPE_OF[key] = of
        self._sync_names(key, name_en, name_zh)
        if color:
            gui.TYPE_COLOR[key] = tuple(color)
        self._rebuild_all_types()

    def rename(self, key, name_en, name_zh):
        """Text-only reskin: rename an existing card type (type key unchanged).

        Patches the card names used by the local UI and registers the canonical
        English name -> new names mapping so server chat/banner messages get
        renamed on this client too (the server itself is untouched, so every
        player sees only their own reskin).
        """
        key = str(key).upper()
        old_en = _BASE_EN.get(key, game.TYPE_EN.get(key, key))
        if old_en != name_en:
            lang.RENAME_MAP[old_en] = (name_en, name_zh)
        game.TYPE_EN[key] = name_en
        game.TYPE_ZH[key] = name_zh
        lang.TYPE_ZH[key] = name_zh
        return (old_en, name_en, name_zh)

    def set_avatar_colors(self, key, bg, fg, accent):
        """Reskin mod hook: recolor one builtin avatar.

        key is a builtin avatar id (pig/chicken/cat/fox/knight/merchant/
        wizard/captain); bg/fg/accent are (r,g,b) tuples used for the ring,
        the head and the detail color. Client-side only, like api.rename.
        """
        import gfx  # local import keeps mods dependency-light
        gfx.set_avatar_style(str(key), tuple(bg), tuple(fg), tuple(accent))
        return (bg, fg, accent)

    def patch(self, module_name, attr, value):
        """Modify the game itself, e.g. api.patch("game", "HAND_SIZE", 7)."""
        mod = _MODULES.get(module_name)
        if mod is None:
            raise KeyError(f"[{self.mod_id}] unknown module {module_name}")
        setattr(mod, attr, value)
        return value

    def get(self, module_name, attr):
        """Read an engine attribute, e.g. api.get("game", "HAND_SIZE")."""
        mod = _MODULES.get(module_name)
        if mod is None:
            raise KeyError(f"[{self.mod_id}] unknown module {module_name}")
        return getattr(mod, attr)


def mods_base():
    """Directory that contains the mods/ folder (executable dir when frozen)."""
    env = os.environ.get("SHERIFF_MODS_DIR")
    if env:
        return env
    if getattr(sys, "frozen", False):
        return os.path.join(os.path.dirname(sys.executable), MODS_DIR)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), MODS_DIR)


def _is_writable_dir(path):
    """True if we can create/delete a probe file inside ``path``."""
    try:
        os.makedirs(path, exist_ok=True)
        probe = os.path.join(path, ".sheriff_write_probe")
        with io.open(probe, "w", encoding="utf-8"):
            pass
        os.remove(probe)
        return True
    except Exception:
        return False


def _user_mods_base():
    """Per-user mods folder (%APPDATA% / ~), always writable by the player."""
    if os.name == "nt":
        root = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        root = os.path.join(os.path.expanduser("~"), ".local", "share")
    return os.path.join(root, "SheriffOfNottingham", MODS_DIR)


def _grant_users_write(folder):
    """Windows: best-effort grant the Users group modify rights (ACL).

    Only succeeds when the caller holds WRITE_DAC on the folder (e.g. the
    install folder is user-owned). The installer normally fixes Program Files
    ACLs, this is a safety net for already-installed copies.
    """
    if os.name != "nt":
        return False
    try:
        import subprocess
        flags = 0
        if hasattr(subprocess, "CREATE_NO_WINDOW"):
            flags = subprocess.CREATE_NO_WINDOW
        r = subprocess.run(
            ["icacls", folder, "/grant", "Users:(OI)(CI)M", "/T", "/Q"],
            capture_output=True, timeout=30, creationflags=flags)
        return r.returncode == 0
    except Exception:
        return False


def _migrate_mods(src, dst):
    """Copy every mod folder (folder containing mod.json) from src to dst.

    Existing folders in dst are kept (never overwritten). Returns True when
    dst is writable afterwards.
    """
    try:
        os.makedirs(dst, exist_ok=True)
        if os.path.isdir(src):
            for name in sorted(os.listdir(src)):
                if name.startswith((".", "_")):
                    continue
                src_folder = os.path.join(src, name)
                dst_folder = os.path.join(dst, name)
                if not os.path.isdir(src_folder):
                    continue
                if not os.path.isfile(os.path.join(src_folder, "mod.json")):
                    continue
                if os.path.isdir(dst_folder):
                    continue
                try:
                    shutil.copytree(src_folder, dst_folder)
                except Exception:
                    pass
        return _is_writable_dir(dst)
    except Exception:
        return False


_effective_base = None


def effective_mods_base():
    """Resolve the mods folder actually used by the game.

    Prefers the folder next to the game; if that folder is not writable
    (typical for installs under the protected Program Files folder), tries to repair its
    ACL, and finally falls back to a per-user folder under %APPDATA%,
    migrating any mods found next to the game.
    """
    env = os.environ.get("SHERIFF_MODS_DIR")
    if env:
        return env
    global _effective_base
    if _effective_base:
        return _effective_base
    primary = mods_base()
    if _is_writable_dir(primary):
        _effective_base = primary
        return _effective_base
    if os.name == "nt":
        _grant_users_write(primary)
        if _is_writable_dir(primary):
            _effective_base = primary
            return _effective_base
    alt = _user_mods_base()
    if _migrate_mods(primary, alt):
        _effective_base = alt
        return _effective_base
    _effective_base = primary
    return _effective_base


def reset_mods_base_cache():
    """Forget the cached resolution (used by tests / manual refresh)."""
    global _effective_base
    _effective_base = None


def discover_mods(base=None):
    """Return sorted list of enabled mod folders (manifest + path)."""
    base = base or effective_mods_base()
    out = []
    if not os.path.isdir(base):
        return out
    for name in sorted(os.listdir(base)):
        if name.startswith((".", "_")):
            continue
        folder = os.path.join(base, name)
        if not os.path.isdir(folder):
            continue
        mpath = os.path.join(folder, "mod.json")
        if not os.path.isfile(mpath):
            continue
        try:
            with io.open(mpath, encoding="utf-8-sig") as f:
                manifest = json.load(f)
        except Exception:
            continue
        if not isinstance(manifest, dict) or manifest.get("enabled", True) is False:
            continue
        manifest.setdefault("id", name)
        manifest.setdefault("name", name)
        manifest.setdefault("version", "0.0.0")
        out.append({"id": manifest["id"], "name": manifest["name"],
                    "version": str(manifest["version"]),
                    "description": str(manifest.get("description", "")),
                    "name_zh": str(manifest.get("name_zh", "")),
                    "description_zh": str(manifest.get("description_zh", "")),
                    "category": str(manifest.get("category", "other")),
                    "folder": folder, "manifest": manifest})
    return out


def list_all_mods(base=None):
    """Return ALL mod folders (enabled and disabled) with manifest info.

    Used by the in-game mods management screen.
    """
    base = base or effective_mods_base()
    out = []
    if not os.path.isdir(base):
        return out
    for name in sorted(os.listdir(base)):
        if name.startswith((".", "_")):
            continue
        folder = os.path.join(base, name)
        if not os.path.isdir(folder):
            continue
        mpath = os.path.join(folder, "mod.json")
        if not os.path.isfile(mpath):
            continue
        try:
            with io.open(mpath, encoding="utf-8-sig") as f:
                manifest = json.load(f)
        except Exception:
            manifest = {}
        if not isinstance(manifest, dict):
            manifest = {}
        out.append({
            "id": str(manifest.get("id", name)),
            "name": str(manifest.get("name", name)),
            "version": str(manifest.get("version", "0.0.0")),
            "description": str(manifest.get("description", "")),
            "name_zh": str(manifest.get("name_zh", "")),
            "description_zh": str(manifest.get("description_zh", "")),
            "category": str(manifest.get("category", "other")),
            "enabled": bool(manifest.get("enabled", True)),
            "incompatible_with": [str(x) for x in (manifest.get("incompatible_with") or [])],
            "folder": folder,
        })
    return out


def _clear_readonly(path):
    """Clear the read-only file attribute so the file can be rewritten."""
    try:
        import stat as statmod
        st = os.stat(path)
        os.chmod(path, st.st_mode | statmod.S_IWRITE)
    except Exception:
        pass


def _write_json(path, data):
    """Write JSON with three escalating attempts:

    1. plain write;
    2. clear the read-only attribute and retry;
    3. grant the Users group write ACL on the folder (Windows) and retry.
    """
    for attempt in range(3):
        try:
            with io.open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except (PermissionError, OSError):
            if attempt == 0:
                _clear_readonly(path)
            elif attempt == 1 and os.name == "nt":
                _grant_users_write(os.path.dirname(path) or ".")
            else:
                return False
    return False


def set_enabled(mod_id, enabled, base=None):
    """Persist the enabled flag in the mod's mod.json. Returns True on success."""
    base = base or effective_mods_base()
    for info in list_all_mods(base):
        if info["id"] != mod_id:
            continue
        mpath = os.path.join(info["folder"], "mod.json")
        try:
            with io.open(mpath, encoding="utf-8-sig") as f:
                manifest = json.load(f)
            if not isinstance(manifest, dict):
                manifest = {}
            manifest["enabled"] = bool(enabled)
            return _write_json(mpath, manifest)
        except Exception:
            return False
    return False


def load_mods(base=None):
    """Load all enabled mods. Returns (loaded, errors).

    ``loaded`` is a list of info dicts; ``errors`` is a list of
    "mod id: message" strings. A failing mod never crashes the game.
    """
    global _BASE_EN
    _BASE_EN = dict(game.TYPE_EN)
    lang.RENAME_MAP.clear()
    loaded, errors = [], []
    for info in discover_mods(base):
        mid = info["id"]
        try:
            py = os.path.join(info["folder"], "mod.py")
            if os.path.isfile(py):
                spec = importlib.util.spec_from_file_location(f"mod_{mid}", py)
                mod = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = mod
                spec.loader.exec_module(mod)
                register = getattr(mod, "register", None)
                if callable(register):
                    register(ModAPI(mid, info["folder"]))
            loaded.append(info)
        except Exception as e:  # noqa: BLE001 - one bad mod must not kill the game
            errors.append(f"{mid}: {e!r}")
    lang.rebuild_names()
    return loaded, errors


def rules_mods(base=None):
    """Return the enabled rule mods (category == "rules") as a stable list.

    Used for the server-side room check: every player in a room must have the
    exact same rule mods (id + version) installed so the rules stay in sync
    with the host's server. Text-only reskin mods are NOT included.
    """
    out = []
    for info in discover_mods(base):
        if str(info.get("category", "other")) != "rules":
            continue
        out.append({"id": str(info["id"]),
                    "version": str(info["version"]),
                    "name": str(info["name"]),
                    "name_zh": str(info.get("name_zh", "")),
                    "category": str(info.get("category", "rules")),
                    "description": str(info.get("description", "")),
                    "description_zh": str(info.get("description_zh", ""))})
    out.sort(key=lambda m: m["id"])
    return out


def is_rules_mod(info):
    """True when a mod info dict is a rule mod (category == "rules")."""
    return str((info or {}).get("category", "other")) == "rules"


def check_compat(mod_infos):
    """Find declared incompatibilities among enabled mods.

    ``mod_infos``: list of info dicts from list_all_mods()/rules_mods(). A mod
    declares conflicts with ``"incompatible_with": ["other_id", ...]`` in its
    mod.json (checked in both directions). Returns a list of
    (modA_info, modB_info) pairs that must not be enabled together.
    """
    enabled = [m for m in (mod_infos or []) if m.get("enabled", False)]
    by_id = {}
    for m in enabled:
        by_id.setdefault(str(m.get("id", "")).lower(), []).append(m)
    pairs = set()
    out = []
    for m in enabled:
        mid = str(m.get("id", "")).lower()
        for other in (m.get("incompatible_with") or []):
            oid = str(other).strip().lower()
            if not oid or oid == mid:
                continue
            for other_mod in by_id.get(oid, []):
                key = tuple(sorted((mid, oid)))
                if key not in pairs:
                    pairs.add(key)
                    out.append((m, other_mod))
    return out


def enabled_rule_mods_compat(base=None):
    """Return conflicts among enabled rule mods (used by the lobby/server)."""
    return check_compat([m for m in list_all_mods(base) if is_rules_mod(m)])
