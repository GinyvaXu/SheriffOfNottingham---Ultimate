# -*- coding: utf-8 -*-
"""Steamforge City reskin mod: renames all goods + key UI terms to a Steamforge City theme.

Text-only overlay: the card type keys stay unchanged, so this mod only affects
the local client. During online play every player sees their own reskin while
the server keeps running with the canonical rules. Ships disabled by default;
enable it from the in-game Mods screen and restart.
"""

_NAMES_EN = {
    'APPLE': 'Brass Apples',
    'BLACK_MARKET': 'Underforge',
    'BREAD': 'Boiler Bread',
    'CHEESE': 'Cog-Cheese',
    'CHICKEN': 'Clockwork Fowl',
    'COFFEE': 'Espresso Boiler',
    'CROSSBOW': 'Steam Rifles',
    'ROYAL_BLUE_CHEESE': 'Blue Flame',
    'ROYAL_CHICKEN': 'Steam Rooster',
    'ROYAL_COARSE_BREAD': 'Furnace Bread',
    'ROYAL_GOLD_APPLE': 'Golden Gear',
    'ROYAL_GOUDA_CHEESE': 'Workshop Cheese',
    'ROYAL_GREEN_APPLE': 'Verdigris Fruit',
    'ROYAL_RYE_BREAD': 'Railway Rye',
    'SILK': 'Velvet Steam-Silk',
    'WINE': 'Coal Whiskey',
}

_NAMES_ZH = {
    'APPLE': '????',
    'BLACK_MARKET': '?????',
    'BREAD': '????',
    'CHEESE': '????',
    'CHICKEN': '???',
    'COFFEE': '????',
    'CROSSBOW': '????',
    'ROYAL_BLUE_CHEESE': '????',
    'ROYAL_CHICKEN': '????',
    'ROYAL_COARSE_BREAD': '????',
    'ROYAL_GOLD_APPLE': '????',
    'ROYAL_GOUDA_CHEESE': '????',
    'ROYAL_GREEN_APPLE': '???',
    'ROYAL_RYE_BREAD': '????',
    'SILK': '???????',
    'WINE': '?????',
}
_COLORS = {
    'APPLE': (200, 170, 80),
    'BLACK_MARKET': (80, 90, 110),
    'BREAD': (170, 130, 80),
    'CHEESE': (240, 200, 100),
    'CHICKEN': (210, 150, 70),
    'COFFEE': (120, 80, 50),
    'CROSSBOW': (140, 110, 90),
    'ROYAL_BLUE_CHEESE': (90, 130, 220),
    'ROYAL_CHICKEN': (190, 120, 40),
    'ROYAL_COARSE_BREAD': (130, 95, 60),
    'ROYAL_GOLD_APPLE': (230, 180, 40),
    'ROYAL_GOUDA_CHEESE': (220, 180, 90),
    'ROYAL_GREEN_APPLE': (110, 180, 90),
    'ROYAL_RYE_BREAD': (150, 110, 70),
    'SILK': (190, 120, 170),
    'WINE': (160, 80, 70),
}

_PHASES_EN = {
    'DECLARE': 'Manifest',
    'INSPECT': 'Inspect',
    'LOAD': 'Load Boiler',
    'MARKET': 'Grand Bazaar',
}
_PHASES_ZH = {
    'DECLARE': '????',
    'INSPECT': '??',
    'LOAD': '????',
    'MARKET': '???',
}
_UI_EN = {
    'head': 'Phase: {phase}   Round {r}/{t}   Chief Inspector: {name}',
    'sheriff_tag': '[Chief Inspector] ',
    'subtitle': 'a steampunk reskin | host a room + your own port forwarding',
    'title': 'Sheriff of Steamforge',
}
_UI_ZH = {
    'head': '???{phase}   ? {r}/{t} ??   ????{name}',
    'sheriff_tag': '?????',
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
