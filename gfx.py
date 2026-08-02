# -*- coding: utf-8 -*-
"""Procedural decorative graphics (no external image assets needed).

Every surface is drawn once at import / on demand with pygame primitives so
the game works from source and from the frozen exe without extra files.
"""

import math
import os
import sys

import pygame

GOLD = (226, 168, 52)
GOLD_LIGHT = (248, 214, 120)
DARK = (58, 46, 36)
BROWN = (74, 60, 46)
CREAM = (224, 210, 180)

_CACHE = {}


def asset_path(name):
    """Locate an asset file (works from source and from the PyInstaller exe)."""
    base_dirs = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        base_dirs.append(meipass)
    base_dirs.append(os.path.dirname(os.path.abspath(__file__)))
    for d in base_dirs:
        p = os.path.join(d, "assets", name)
        if os.path.isfile(p):
            return p
    return None


def _cache(key, size, fn):
    """Render once and keep (key includes size)."""
    ck = (key, size)
    if ck not in _CACHE:
        _CACHE[ck] = fn()
    return _CACHE[ck]


def _star_pts(cx, cy, r_out, r_in, points=5, rot=0.0):
    pts = []
    for i in range(points * 2):
        r = r_out if i % 2 == 0 else r_in
        a = math.pi / 2 + rot + i * math.pi / points
        pts.append((cx + r * math.cos(a), cy - r * math.sin(a)))
    return pts


def badge(size=48):
    """Five-point sheriff star badge."""
    def _draw():
        s = pygame.Surface((size, size), pygame.SRCALPHA)
        cx = cy = size // 2
        pts = _star_pts(cx, cy, size * 0.47, size * 0.22)
        pygame.draw.polygon(s, GOLD, pts)
        pygame.draw.polygon(s, (120, 84, 24), pts, 2)
        pygame.draw.circle(s, DARK, (cx, cy), size * 0.20)
        pygame.draw.circle(s, GOLD_LIGHT, (cx, cy), size * 0.20, 2)
        pygame.draw.circle(s, GOLD, (cx, cy), size * 0.10)
        return s
    return _cache("badge", size, _draw)


def coin(size=22):
    """Gold coin icon."""
    def _draw():
        s = pygame.Surface((size, size), pygame.SRCALPHA)
        r = size // 2
        c = (r, r)
        pygame.draw.circle(s, (196, 146, 44), c, r)
        pygame.draw.circle(s, GOLD_LIGHT, c, r - 1)
        pygame.draw.circle(s, (140, 100, 30), c, r - 1, 2)
        pygame.draw.circle(s, GOLD, c, max(2, r - 5), 2)
        return s
    return _cache("coin", size, _draw)


def card_back(w=64, h=92):
    """Decorative card back (used for the deck)."""
    def _draw():
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(s, BROWN, (0, 0, w, h), border_radius=8)
        pygame.draw.rect(s, GOLD, (0, 0, w, h), 3, border_radius=8)
        pygame.draw.rect(s, (120, 96, 70), (6, 6, w - 12, h - 12), 1, border_radius=6)
        cx, cy = w // 2, h // 2
        pts = _star_pts(cx, cy, w * 0.24, w * 0.11, rot=math.pi / 5)
        pygame.draw.polygon(s, GOLD, pts)
        pygame.draw.circle(s, GOLD, (w // 2, 16), 3)
        pygame.draw.circle(s, GOLD, (w // 2, h - 16), 3)
        return s
    return _cache("card_back", (w, h), _draw)


def bag(size=30):
    """Burlap sack icon (sealed bag)."""
    def _draw():
        s = pygame.Surface((size, size + 4), pygame.SRCALPHA)
        w, h = size, size
        # body
        body = pygame.Rect(w * 0.16, h * 0.24, w * 0.68, h * 0.70)
        pygame.draw.ellipse(s, (150, 116, 74), body)
        pygame.draw.ellipse(s, (90, 70, 46), body, 2)
        # neck
        pygame.draw.rect(s, (150, 116, 74), (w * 0.30, h * 0.10, w * 0.40, h * 0.26), border_radius=4)
        # tie
        pygame.draw.line(s, GOLD, (w * 0.30, h * 0.20), (w * 0.70, h * 0.20), 3)
        return s
    return _cache("bag", size, _draw)


def icon(size=256):
    """Full app icon: sheriff badge over a dark rounded panel."""
    def _draw():
        s = pygame.Surface((size, size), pygame.SRCALPHA)
        m = int(size * 0.03)
        pygame.draw.rect(s, (38, 30, 22), (m, m, size - 2 * m, size - 2 * m),
                         border_radius=int(size * 0.18))
        pygame.draw.rect(s, GOLD, (m, m, size - 2 * m, size - 2 * m),
                         max(3, size // 32), border_radius=int(size * 0.18))
        # star badge
        cx = cy = size // 2
        r_out = size * 0.36
        pts = _star_pts(cx, cy, r_out, r_out * 0.46)
        pygame.draw.polygon(s, GOLD, pts)
        pygame.draw.polygon(s, (120, 84, 24), pts, max(3, size // 32))
        # inner ring + card motif
        pygame.draw.circle(s, DARK, (cx, cy), size * 0.155)
        pygame.draw.circle(s, GOLD_LIGHT, (cx, cy), size * 0.155, max(2, size // 64))
        cw, ch = size * 0.18, size * 0.24
        card = pygame.Rect(cx - cw // 2, cy - ch // 2, cw, ch)
        pygame.draw.rect(s, (52, 44, 36), card, border_radius=max(3, size // 40))
        pygame.draw.rect(s, GOLD, card, max(2, size // 64), border_radius=max(3, size // 40))
        # card pips
        px = card.centerx
        pygame.draw.circle(s, GOLD, (px, card.top + ch * 0.22), max(2, size // 64))
        pygame.draw.circle(s, GOLD, (px, card.centery), max(2, size // 64))
        pygame.draw.circle(s, GOLD, (px, card.bottom - ch * 0.22), max(2, size // 64))
        # flanking dots
        for dx in (-size * 0.21, size * 0.21):
            pygame.draw.circle(s, GOLD_LIGHT, (cx + dx, cy), max(2, size // 64))
        return s
    return _cache("icon", size, _draw)


def title_logo(size=72):
    """Badge with a thin underline used next to the menu title."""
    def _draw():
        s = pygame.Surface((size, size + 6), pygame.SRCALPHA)
        s.blit(badge(size), (0, 0))
        pygame.draw.rect(s, GOLD, (size * 0.18, size, size * 0.64, max(2, size // 24)),
                         border_radius=2)
        return s
    return _cache("title_logo", size, _draw)
# ---------- Avatars ----------

AVATAR_STYLE = {
    # key: (background ring, head, accent)
    "pig":     ((196, 108, 122), (244, 190, 198), (150, 60, 80)),
    "chicken": ((206, 158, 62), (250, 224, 140), (206, 90, 40)),
    "cat":     ((196, 118, 52), (248, 202, 138), (70, 45, 25)),
    "fox":     ((188, 88, 52), (248, 190, 150), (90, 50, 30)),
    "knight":  ((104, 114, 132), (176, 186, 200), (52, 62, 78)),
    "merchant":((166, 122, 74), (238, 210, 168), (110, 72, 40)),
    "wizard":  ((112, 88, 160), (200, 176, 240), (64, 46, 104)),
    "captain": ((70, 104, 160), (196, 222, 250), (38, 66, 104)),
}


def set_avatar_style(key, bg, fg, accent):
    """Reskin mod hook: recolor one builtin avatar."""
    AVATAR_STYLE[key] = (tuple(bg), tuple(fg), tuple(accent))


def _circle_crop(surf, size):
    """Crop a square surface into a circle of the given size."""
    if surf.get_width() != size or surf.get_height() != size:
        surf = pygame.transform.smoothscale(surf, (size, size))
    mask = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(mask, (255, 255, 255, 255), (size // 2, size // 2), size // 2)
    surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    return surf


def _custom_avatar_surface(b64data, size):
    def _draw():
        try:
            import base64 as _b64
            import io as _io
            raw = _b64.b64decode(b64data)
            surf = pygame.image.load(_io.BytesIO(raw)).convert_alpha()
            return _circle_crop(surf, size)
        except Exception:  # noqa: BLE001 - fall back to a neutral face
            return _builtin_avatar_surface("pig", size)
    return _cache(("avatar_custom", b64data[:64]), size, _draw)


def _face_base(size, bg, fg):
    """Shared circular head: ring + face + eyes + mouth."""
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    c = size // 2
    r = size // 2
    pygame.draw.circle(s, bg, (c, c), r)
    pygame.draw.circle(s, fg, (c, c), r - max(2, size // 12))
    eye_y = int(size * 0.42)
    eye_r = max(2, size // 16)
    for ex in (int(size * 0.38), int(size * 0.62)):
        pygame.draw.circle(s, (40, 32, 28), (ex, eye_y), eye_r)
        pygame.draw.circle(s, (255, 255, 255), (ex - eye_r // 3, eye_y - eye_r // 3),
                           max(1, eye_r // 3))
    pygame.draw.arc(s, (40, 32, 28),
                    (int(size * 0.32), int(size * 0.52), int(size * 0.36), int(size * 0.28)),
                    0.15, 3.0, max(1, size // 22))
    return s


def _builtin_avatar_surface(key, size):
    def _draw():
        bg, fg, accent = AVATAR_STYLE.get(key, AVATAR_STYLE["pig"])
        s = _face_base(size, bg, fg)
        c = size // 2
        u = max(2, size // 12)
        if key == "pig":
            # big round snout
            pygame.draw.ellipse(s, (232, 170, 180),
                                (int(size * 0.32), int(size * 0.52),
                                 int(size * 0.36), int(size * 0.26)))
            for nx in (int(size * 0.42), int(size * 0.58)):
                pygame.draw.circle(s, (120, 50, 66), (nx, int(size * 0.65)), u // 2)
            for ex in (int(size * 0.24), int(size * 0.76)):
                pygame.draw.polygon(s, accent,
                                    [(ex, int(size * 0.20)), (ex - u, int(size * 0.02)),
                                     (ex + u, int(size * 0.02))])
        elif key == "chicken":
            # red comb + orange beak
            for dy in range(3):
                pygame.draw.circle(s, (214, 70, 40),
                                   (c, int(size * 0.10) + dy * int(size * 0.10)),
                                   u)
            pygame.draw.polygon(s, (240, 140, 50),
                                [(int(size * 0.44), int(size * 0.56)),
                                 (int(size * 0.56), int(size * 0.56)),
                                 (c, int(size * 0.70))])
        elif key == "cat":
            for ex in (int(size * 0.24), int(size * 0.76)):
                pygame.draw.polygon(s, accent,
                                    [(ex, int(size * 0.22)), (ex - u * 2, -2),
                                     (ex + u * 2, -2)])
            for w in (-1, 1):
                pygame.draw.line(s, (60, 40, 24),
                                 (c + w * int(size * 0.30), int(size * 0.56)),
                                 (c + w * int(size * 0.50), int(size * 0.60)), 1)
                pygame.draw.line(s, (60, 40, 24),
                                 (c + w * int(size * 0.30), int(size * 0.64)),
                                 (c + w * int(size * 0.48), int(size * 0.72)), 1)
        elif key == "fox":
            for ex in (int(size * 0.22), int(size * 0.78)):
                pygame.draw.polygon(s, accent,
                                    [(ex, int(size * 0.24)), (ex - u * 2, -2),
                                     (ex + u, int(size * 0.18))])
            pygame.draw.ellipse(s, (252, 240, 226),
                                (int(size * 0.30), int(size * 0.56),
                                 int(size * 0.40), int(size * 0.22)))
        elif key == "knight":
            # steel helmet + plume
            pygame.draw.ellipse(s, (150, 160, 175),
                                (int(size * 0.14), int(size * 0.02),
                                 int(size * 0.72), int(size * 0.50)))
            pygame.draw.line(s, (70, 80, 96), (int(size * 0.30), int(size * 0.16)),
                             (int(size * 0.70), int(size * 0.16)), u)
            pygame.draw.polygon(s, accent,
                                [(int(size * 0.70), int(size * 0.10)),
                                 (int(size * 0.90), int(size * 0.02)),
                                 (int(size * 0.86), int(size * 0.20))])
        elif key == "merchant":
            # wide-brim hat + mustache
            pygame.draw.rect(s, accent, (int(size * 0.06), int(size * 0.14),
                                         int(size * 0.88), u * 2), border_radius=u)
            pygame.draw.rect(s, (90, 60, 34), (int(size * 0.26), int(size * 0.02),
                                               int(size * 0.48), int(size * 0.18)),
                             border_radius=u)
            for w in (-1, 1):
                pygame.draw.line(s, (90, 60, 34),
                                 (c, int(size * 0.62)), (c + w * int(size * 0.22), int(size * 0.58)), 2)
        elif key == "wizard":
            # pointed hat + star + beard
            pygame.draw.polygon(s, accent,
                                [(int(size * 0.24), int(size * 0.20)),
                                 (int(size * 0.76), int(size * 0.20)),
                                 (c, -2)])
            pts = _star_pts(c, int(size * 0.14), u, u // 2, points=5)
            pygame.draw.polygon(s, (250, 220, 120), pts)
            pygame.draw.ellipse(s, (235, 228, 255),
                                (int(size * 0.30), int(size * 0.56),
                                 int(size * 0.40), int(size * 0.24)))
        elif key == "captain":
            # white captain hat + beard
            pygame.draw.rect(s, (240, 244, 250), (int(size * 0.10), int(size * 0.10),
                                                  int(size * 0.80), u * 2), border_radius=u)
            pygame.draw.rect(s, (240, 244, 250), (int(size * 0.28), int(size * 0.00),
                                                  int(size * 0.44), int(size * 0.16)),
                             border_radius=u)
            pygame.draw.circle(s, accent, (c, int(size * 0.20)), u // 2)
            pygame.draw.ellipse(s, (220, 228, 240),
                                (int(size * 0.30), int(size * 0.58),
                                 int(size * 0.40), int(size * 0.22)))
        return s
    return _cache(("avatar_builtin", key), size, _draw)


def avatar_surface(avatar, size):
    """Render an avatar dict (from profile.avatar_payload) at a square size."""
    if not isinstance(avatar, dict):
        avatar = {"kind": "builtin", "id": "pig"}
    if avatar.get("kind") == "custom" and avatar.get("data"):
        return _custom_avatar_surface(avatar["data"], size)
    key = str(avatar.get("id") or "pig")
    if key not in AVATAR_STYLE:
        key = "pig"
    return _builtin_avatar_surface(key, size)
