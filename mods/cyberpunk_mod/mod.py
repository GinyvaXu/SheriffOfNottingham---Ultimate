# -*- coding: utf-8 -*-
"""Cyberpunk Overlay reskin mod: renames all goods + key UI terms to a Cyberpunk Overlay theme.

Text-only overlay: the card type keys stay unchanged, so this mod only affects
the local client. During online play every player sees their own reskin while
the server keeps running with the canonical rules. Ships disabled by default;
enable it from the in-game Mods screen and restart.
"""

_NAMES_EN = {
    'APPLE': 'Synth-Fruit',
    'BLACK_MARKET': 'DarkNet',
    'BREAD': 'Nutri-Bread',
    'CHEESE': 'Nano-Dairy',
    'CHICKEN': 'Vat Protein',
    'COFFEE': 'Neuro-Stim',
    'CROSSBOW': 'Rail-Gun',
    'ROYAL_BLUE_CHEESE': 'Cyber Blue Dairy',
    'ROYAL_CHICKEN': 'Bionic Roast',
    'ROYAL_COARSE_BREAD': 'Data Bread',
    'ROYAL_GOLD_APPLE': 'Gold-Plated Fruit',
    'ROYAL_GOUDA_CHEESE': 'Quantum Dairy',
    'ROYAL_GREEN_APPLE': 'Chrome Fruit',
    'ROYAL_RYE_BREAD': 'Circuit Rye',
    'SILK': 'Memory Silk',
    'WINE': 'Night-Brew',
}

_NAMES_ZH = {
    'APPLE': '????',
    'BLACK_MARKET': '??',
    'BREAD': '????',
    'CHEESE': '????',
    'CHICKEN': '????',
    'COFFEE': '?????',
    'CROSSBOW': '???',
    'ROYAL_BLUE_CHEESE': '????',
    'ROYAL_CHICKEN': '????',
    'ROYAL_COARSE_BREAD': '????',
    'ROYAL_GOLD_APPLE': '???',
    'ROYAL_GOUDA_CHEESE': '????',
    'ROYAL_GREEN_APPLE': '??',
    'ROYAL_RYE_BREAD': '????',
    'SILK': '????',
    'WINE': '??',
}
_COLORS = {
    'APPLE': (110, 235, 130),
    'BLACK_MARKET': (0, 255, 220),
    'BREAD': (190, 140, 80),
    'CHEESE': (240, 220, 80),
    'CHICKEN': (250, 160, 60),
    'COFFEE': (255, 140, 80),
    'CROSSBOW': (80, 170, 255),
    'ROYAL_BLUE_CHEESE': (90, 150, 255),
    'ROYAL_CHICKEN': (230, 140, 40),
    'ROYAL_COARSE_BREAD': (140, 100, 60),
    'ROYAL_GOLD_APPLE': (255, 200, 40),
    'ROYAL_GOUDA_CHEESE': (230, 210, 60),
    'ROYAL_GREEN_APPLE': (60, 200, 110),
    'ROYAL_RYE_BREAD': (160, 120, 70),
    'SILK': (210, 90, 250),
    'WINE': (255, 90, 160),
}

_PHASES_EN = {
    'DECLARE': 'Broadcast',
    'INSPECT': 'Scan',
    'LOAD': 'Upload',
    'MARKET': 'Neon Market',
}
_PHASES_ZH = {
    'DECLARE': '??',
    'INSPECT': '??',
    'LOAD': '??',
    'MARKET': '????',
}
_UI_EN = {
    'head': 'Phase: {phase}   Round {r}/{t}   NetBoss: {name}',
    'sheriff_tag': '[NetBoss] ',
    'subtitle': 'a cyberpunk reskin | host a room + your own port forwarding',
    'title': 'Sheriff of Neo-Nottingham',
}
_UI_ZH = {
    'head': '???{phase}   ? {r}/{t} ??   ???{name}',
    'sheriff_tag': '????',
    'subtitle': '?????? | ???? + ????????',
    'title': '???????',
}
def register(api):
    for key in _NAMES_EN:
        api.rename(key, _NAMES_EN[key], _NAMES_ZH[key])

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
