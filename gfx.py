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
