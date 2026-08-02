# -*- coding: utf-8 -*-
"""Local player profile: name + avatar persisted in the app-data folder.

The profile lives in %APPDATA%/SheriffOfNottingham/profile.json so the
player does not need to re-enter their name or re-pick an avatar every
launch. Custom avatars are stored as base64 PNG data (downscaled to a
small standard size) so they survive reinstall and can be sent to other
players over the network without any extra files.
"""

import base64
import io
import json
import os

APP_DIR_NAME = "SheriffOfNottingham"
PROFILE_FILE = "profile.json"
DEFAULT_AVATAR = "pig"
BUILTIN_AVATARS = [
    "pig", "chicken", "cat", "fox",
    "knight", "merchant", "wizard", "captain",
]
MAX_CUSTOM_B64 = 512 * 1024   # safety cap for the stored/transmitted image


def app_dir():
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    d = os.path.join(base, APP_DIR_NAME)
    try:
        os.makedirs(d, exist_ok=True)
    except OSError:
        pass
    return d


def profile_path():
    return os.path.join(app_dir(), PROFILE_FILE)


def default_profile():
    return {"name": "", "avatar": DEFAULT_AVATAR, "custom_avatar": None}


def load_profile():
    p = default_profile()
    try:
        with io.open(profile_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return p
        p["name"] = str(data.get("name", "") or "")
        av = str(data.get("avatar", "") or "")
        p["avatar"] = av if av in BUILTIN_AVATARS else DEFAULT_AVATAR
        ca = data.get("custom_avatar")
        if isinstance(ca, str) and 0 < len(ca) < MAX_CUSTOM_B64:
            p["custom_avatar"] = ca
    except (OSError, ValueError):
        pass
    return p


def save_profile(profile):
    try:
        with io.open(profile_path(), "w", encoding="utf-8", newline="") as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False


def avatar_payload(profile):
    """Serialize the chosen avatar for network messages."""
    if profile.get("custom_avatar"):
        return {"kind": "custom", "data": profile["custom_avatar"]}
    return {"kind": "builtin", "id": profile.get("avatar") or DEFAULT_AVATAR}


def avatar_from_payload(payload, default=None):
    """Normalize a received avatar payload (used by the server/seat records)."""
    if default is None:
        default = avatar_payload(default_profile())
    if not isinstance(payload, dict):
        return default
    kind = payload.get("kind")
    if kind == "custom":
        data = payload.get("data")
        if isinstance(data, str) and 0 < len(data) < MAX_CUSTOM_B64:
            return {"kind": "custom", "data": data}
        return default
    av = str(payload.get("id", "") or "")
    if av in BUILTIN_AVATARS:
        return {"kind": "builtin", "id": av}
    return default


def encode_png(surface, size=128):
    """Downscale a pygame surface to a standard size and encode as base64 PNG.

    Returns (b64_string, ok). The caller must convert the surface to a
    format pygame can save (32-bit with alpha works best).
    """
    try:
        import pygame
        if surface.get_width() > size or surface.get_height() > size:
            surface = pygame.transform.smoothscale(surface, (size, size))
        elif surface.get_width() != size or surface.get_height() != size:
            surface = pygame.transform.smoothscale(surface, (size, size))
        buf = io.BytesIO()
        pygame.image.save(surface, buf, "PNG")
        return base64.b64encode(buf.getvalue()).decode("ascii"), True
    except Exception:  # noqa: BLE001 - caller shows a friendly error
        return "", False
