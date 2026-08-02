# -*- coding: utf-8 -*-
"""Cyberpunk overlay mod: renames all goods + key UI terms to a neon theme.

Ships disabled by default (\"enabled\": false in mod.json). Enable it from the
in-game Mods screen (menu -> Mods -> Enable) and restart, or set enabled: true
here and restart. All players in a room should enable the same content mods.
"""

# ---- card names (en / zh) ----
_NAMES_EN = {
    "APPLE": "Bio-Apple",
    "CHICKEN": "Clone-Chicken",
    "CHEESE": "Nano-Cheese",
    "BREAD": "Nutri-Bread",
    "SILK": "Nano-Silk",
    "CROSSBOW": "Rail-Bow",
    "COFFEE": "Neuro-Coffee",
    "WINE": "Night-Wine",
    "ROYAL_GREEN_APPLE": "Chrome Apple",
    "ROYAL_GOLD_APPLE": "Gold-Plated Apple",
    "ROYAL_GOUDA_CHEESE": "Quantum Cheese",
    "ROYAL_BLUE_CHEESE": "Cyber Blue Cheese",
    "ROYAL_RYE_BREAD": "Circuit Rye",
    "ROYAL_COARSE_BREAD": "Data Bread",
    "ROYAL_CHICKEN": "Bionic Chicken",
    "BLACK_MARKET": "DarkNet",
}
_NAMES_ZH = {
    "APPLE": "\u5408\u6210\u82f9\u679c",
    "CHICKEN": "\u514b\u9686\u9e21\u8089",
    "CHEESE": "\u7eb3\u7c73\u5976\u9171",
    "BREAD": "\u8425\u517b\u9762\u5305",
    "SILK": "\u7eb3\u7c73\u4e1d\u7ef8",
    "CROSSBOW": "\u78c1\u8f68\u5f29",
    "COFFEE": "\u795e\u7ecf\u5496\u5561",
    "WINE": "\u591c\u884c\u9152",
    "ROYAL_GREEN_APPLE": "\u94ec\u82f9\u679c",
    "ROYAL_GOLD_APPLE": "\u9540\u91d1\u82f9\u679c",
    "ROYAL_GOUDA_CHEESE": "\u91cf\u5b50\u5976\u9171",
    "ROYAL_BLUE_CHEESE": "\u8d5b\u535a\u84dd\u7eb9",
    "ROYAL_RYE_BREAD": "\u7535\u8def\u9ed1\u9ea6",
    "ROYAL_COARSE_BREAD": "\u6570\u636e\u7c97\u7cae",
    "ROYAL_CHICKEN": "\u751f\u5316\u9e21\u8089",
    "BLACK_MARKET": "\u6697\u7f51",
}

# ---- neon colors ----
_COLORS = {
    "APPLE": (110, 235, 130),
    "CHEESE": (240, 220, 80),
    "BREAD": (190, 140, 80),
    "CHICKEN": (250, 160, 60),
    "SILK": (210, 90, 250),
    "CROSSBOW": (80, 170, 255),
    "COFFEE": (255, 140, 80),
    "WINE": (255, 90, 160),
    "ROYAL_GREEN_APPLE": (60, 200, 110),
    "ROYAL_GOLD_APPLE": (255, 200, 40),
    "ROYAL_GOUDA_CHEESE": (230, 210, 60),
    "ROYAL_BLUE_CHEESE": (90, 150, 255),
    "ROYAL_RYE_BREAD": (160, 120, 70),
    "ROYAL_COARSE_BREAD": (140, 100, 60),
    "ROYAL_CHICKEN": (230, 140, 40),
    "BLACK_MARKET": (0, 255, 220),
}

# ---- phase names ----
_PHASES_EN = {"MARKET": "Neon Market", "LOAD": "Upload", "DECLARE": "Broadcast", "INSPECT": "Scan"}
_PHASES_ZH = {"MARKET": "\u9713\u8679\u5e02\u573a", "LOAD": "\u4e0a\u4f20",
              "DECLARE": "\u5e7f\u64ad", "INSPECT": "\u626b\u63cf"}

# ---- UI strings ----
_UI_EN = {
    "title": "Sheriff of Neo-Nottingham",
    "subtitle": "a cyberpunk reskin | host a room + your own port forwarding",
    "sheriff_tag": "[NetBoss] ",
    "head": "Phase: {phase}   Round {r}/{t}   NetBoss: {name}",
}
_UI_ZH = {
    "title": "\u9713\u8679\u8bfa\u4e01\u6c49\u8b66\u957f",
    "subtitle": "\u8d5b\u535a\u670b\u514b\u76ae\u80a4 | \u623f\u4e3b\u5f00\u623f + \u81ea\u884c\u7aef\u53e3\u6620\u5c04\u8054\u673a",
    "sheriff_tag": "\u3010\u7f51\u8b66\u3011",
    "head": "\u9636\u6bb5\uff1a{phase}   \u7b2c {r}/{t} \u56de\u5408   \u7f51\u8b66\uff1a{name}",
}


def register(api):
    en = dict(api.get("game", "TYPE_EN"))
    en.update(_NAMES_EN)
    api.patch("game", "TYPE_EN", en)

    zh = dict(api.get("game", "TYPE_ZH"))
    zh.update(_NAMES_ZH)
    api.patch("game", "TYPE_ZH", zh)

    lzh = dict(api.get("lang", "TYPE_ZH"))
    lzh.update(_NAMES_ZH)
    api.patch("lang", "TYPE_ZH", lzh)

    colors = dict(api.get("gui", "TYPE_COLOR"))
    colors.update(_COLORS)
    api.patch("gui", "TYPE_COLOR", colors)

    phases = dict(api.get("lang", "PHASES"))
    phases = {lng: dict(d) for lng, d in phases.items()}
    phases["en"].update(_PHASES_EN)
    phases["zh"].update(_PHASES_ZH)
    api.patch("lang", "PHASES", phases)

    ui = dict(api.get("lang", "UI"))
    ui = {lng: dict(d) for lng, d in ui.items()}
    ui["en"].update(_UI_EN)
    ui["zh"].update(_UI_ZH)
    api.patch("lang", "UI", ui)
