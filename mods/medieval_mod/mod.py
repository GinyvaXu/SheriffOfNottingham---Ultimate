# -*- coding: utf-8 -*-
"""Medieval England reskin mod: renames all goods + key UI terms to a Medieval England theme.

Text-only overlay: the card type keys stay unchanged, so this mod only affects
the local client. During online play every player sees their own reskin while
the server keeps running with the canonical rules. Ships disabled by default;
enable it from the in-game Mods screen and restart.
"""

_NAMES_EN = {
    'APPLE': 'Orchard Apples',
    'BLACK_MARKET': "Smugglers' Den",
    'BREAD': 'Oat Loaves',
    'CHEESE': 'Monastery Cheese',
    'CHICKEN': 'Fattened Capons',
    'COFFEE': 'Arabian Brew',
    'CROSSBOW': 'War Crossbows',
    'ROYAL_BLUE_CHEESE': 'Noble Blue',
    'ROYAL_CHICKEN': 'Royal Roast',
    'ROYAL_COARSE_BREAD': 'Peasant Coarse',
    'ROYAL_GOLD_APPLE': 'Golden Herald Fruit',
    'ROYAL_GOUDA_CHEESE': "Abbot's Cheese",
    'ROYAL_GREEN_APPLE': 'Green Herald Fruit',
    'ROYAL_RYE_BREAD': "Monk's Rye",
    'SILK': 'Flemish Silk',
    'WINE': "Monks' Mead",
}

_NAMES_ZH = {
    'APPLE': '????',
    'BLACK_MARKET': '?????',
    'BREAD': '????',
    'CHEESE': '?????',
    'CHICKEN': '????',
    'COFFEE': '?????',
    'CROSSBOW': '??',
    'ROYAL_BLUE_CHEESE': '????',
    'ROYAL_CHICKEN': '????',
    'ROYAL_COARSE_BREAD': '????',
    'ROYAL_GOLD_APPLE': '????',
    'ROYAL_GOUDA_CHEESE': '????',
    'ROYAL_GREEN_APPLE': '????',
    'ROYAL_RYE_BREAD': '????',
    'SILK': '??????',
    'WINE': '?????',
}
_COLORS = {
    'APPLE': (150, 210, 90),
    'BLACK_MARKET': (60, 60, 60),
    'BREAD': (190, 150, 90),
    'CHEESE': (240, 210, 120),
    'CHICKEN': (220, 180, 90),
    'COFFEE': (150, 100, 60),
    'CROSSBOW': (130, 110, 100),
    'ROYAL_BLUE_CHEESE': (100, 130, 210),
    'ROYAL_CHICKEN': (200, 130, 40),
    'ROYAL_COARSE_BREAD': (130, 100, 60),
    'ROYAL_GOLD_APPLE': (230, 180, 40),
    'ROYAL_GOUDA_CHEESE': (230, 200, 100),
    'ROYAL_GREEN_APPLE': (80, 160, 70),
    'ROYAL_RYE_BREAD': (150, 120, 70),
    'SILK': (200, 120, 190),
    'WINE': (150, 60, 90),
}

_PHASES_EN = {
    'DECLARE': 'Proclaim',
    'INSPECT': 'Search',
    'LOAD': 'Load Wagon',
    'MARKET': 'Market Day',
}
_PHASES_ZH = {
    'DECLARE': '??',
    'INSPECT': '??',
    'LOAD': '??',
    'MARKET': '???',
}
_UI_EN = {
    'head': 'Phase: {phase}   Round {r}/{t}   Sheriff: {name}',
    'sheriff_tag': '[Sheriff] ',
    'subtitle': 'a medieval reskin | host a room + your own port forwarding',
    'title': 'Sheriff of Medieval Nottingham',
}
_UI_ZH = {
    'head': '???{phase}   ? {r}/{t} ??   ???{name}',
    'sheriff_tag': '????',
    'subtitle': '????? | ???? + ????????',
    'title': '????????',
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
