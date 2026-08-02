# -*- coding: utf-8 -*-
"""Arcane Realms reskin mod: renames all goods + key UI terms to a Arcane Realms theme.

Text-only overlay: the card type keys stay unchanged, so this mod only affects
the local client. During online play every player sees their own reskin while
the server keeps running with the canonical rules. Ships disabled by default;
enable it from the in-game Mods screen and restart.
"""

_NAMES_EN = {
    'APPLE': 'Fey Fruit',
    'BLACK_MARKET': 'Shadow Bazaar',
    'BREAD': 'Enchanted Loaves',
    'CHEESE': 'Moon Cheese',
    'CHICKEN': 'Familiar Hens',
    'COFFEE': "Witch's Brew",
    'CROSSBOW': 'Arcane Staves',
    'ROYAL_BLUE_CHEESE': 'Astral Blue',
    'ROYAL_CHICKEN': 'Phoenix Fowl',
    'ROYAL_COARSE_BREAD': "Giant's Bread",
    'ROYAL_GOLD_APPLE': 'Golden Fey Fruit',
    'ROYAL_GOUDA_CHEESE': 'Archmage Cheese',
    'ROYAL_GREEN_APPLE': 'Dragon Fruit',
    'ROYAL_RYE_BREAD': 'Dwarf Rye',
    'SILK': 'Fae Silk',
    'WINE': 'Elven Wine',
}

_NAMES_ZH = {
    'APPLE': '???',
    'BLACK_MARKET': '????',
    'BREAD': '????',
    'CHEESE': '????',
    'CHICKEN': '????',
    'COFFEE': '????',
    'CROSSBOW': '????',
    'ROYAL_BLUE_CHEESE': '????',
    'ROYAL_CHICKEN': '???',
    'ROYAL_COARSE_BREAD': '????',
    'ROYAL_GOLD_APPLE': '?????',
    'ROYAL_GOUDA_CHEESE': '?????',
    'ROYAL_GREEN_APPLE': '???',
    'ROYAL_RYE_BREAD': '????',
    'SILK': '????',
    'WINE': '???',
}
_COLORS = {
    'APPLE': (140, 220, 110),
    'BLACK_MARKET': (150, 80, 230),
    'BREAD': (200, 160, 100),
    'CHEESE': (250, 220, 130),
    'CHICKEN': (230, 170, 90),
    'COFFEE': (130, 90, 70),
    'CROSSBOW': (120, 90, 230),
    'ROYAL_BLUE_CHEESE': (90, 110, 250),
    'ROYAL_CHICKEN': (220, 110, 160),
    'ROYAL_COARSE_BREAD': (140, 105, 70),
    'ROYAL_GOLD_APPLE': (255, 210, 50),
    'ROYAL_GOUDA_CHEESE': (235, 205, 110),
    'ROYAL_GREEN_APPLE': (70, 200, 100),
    'ROYAL_RYE_BREAD': (160, 120, 80),
    'SILK': (170, 110, 240),
    'WINE': (180, 80, 150),
}

_PHASES_EN = {
    'DECLARE': 'Enchant',
    'INSPECT': 'True Sight',
    'LOAD': 'Conjure',
    'MARKET': 'Mystic Bazaar',
}
_PHASES_ZH = {
    'DECLARE': '????',
    'INSPECT': '????',
    'LOAD': '????',
    'MARKET': '????',
}
_UI_EN = {
    'head': 'Phase: {phase}   Round {r}/{t}   Mage Warden: {name}',
    'sheriff_tag': '[Mage Warden] ',
    'subtitle': 'a fantasy reskin | host a room + your own port forwarding',
    'title': 'Sheriff of Arcane Realms',
}
_UI_ZH = {
    'head': '???{phase}   ? {r}/{t} ??   ?????{name}',
    'sheriff_tag': '??????',
    'subtitle': '???? | ???? + ????????',
    'title': '??????',
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
