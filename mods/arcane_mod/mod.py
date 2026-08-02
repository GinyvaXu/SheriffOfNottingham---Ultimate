# -*- coding: utf-8 -*-
"""Arcane Realms reskin mod: renames all goods + key UI terms to a Arcane Realms theme.

Text-only overlay: the card type keys stay unchanged, so this mod only affects
the local client. During online play every player sees their own reskin while
the server keeps running with the canonical rules. Ships disabled by default;
enable it from the in-game Mods screen and restart.
"""

_NAMES_EN = {
    'POT': 'Arcane Vault',
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
    'POT': '奥术宝库',
    'APPLE': '仙灵果',
    'BLACK_MARKET': '暗影集市',
    'BREAD': '附魔面包',
    'CHEESE': '月光奶酪',
    'CHICKEN': '使魔母鸡',
    'COFFEE': '女巫煮剂',
    'CROSSBOW': '奥术法杖',
    'ROYAL_BLUE_CHEESE': '星界蓝纹',
    'ROYAL_CHICKEN': '凤凰禽',
    'ROYAL_COARSE_BREAD': '巨人面包',
    'ROYAL_GOLD_APPLE': '黄金仙灵果',
    'ROYAL_GOUDA_CHEESE': '大法师奶酪',
    'ROYAL_GREEN_APPLE': '龙鳞果',
    'ROYAL_RYE_BREAD': '矮人黑麦',
    'SILK': '妖精丝绸',
    'WINE': '精灵酒',
}

_COLORS = {
    'POT': (150, 120, 220),
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
    'DECLARE': '吟唱申报',
    'INSPECT': '真视之眼',
    'LOAD': '施法装袋',
    'MARKET': '秘法集市',
}

_UI_EN = {
    'head': 'Phase: {phase}   Round {r}/{t}   Mage Warden: {name}',
    'sheriff_tag': '[Mage Warden] ',
    'subtitle': 'a fantasy reskin | host a room + your own port forwarding',
    'title': 'Sheriff of Arcane Realms',
}
_UI_ZH = {
    'head': '阶段：{phase}   第 {r}/{t} 回合   法师典狱：{name}',
    'sheriff_tag': '【法师典狱】',
    'subtitle': '魔法皮肤 | 房主开房 + 自行端口映射联机',
    'title': '奥术秘境警长',
}



_AVATARS = {
    'pig': ((225, 120, 155), (255, 195, 215), (150, 50, 90)),
    'chicken': ((240, 195, 85), (255, 235, 150), (190, 110, 30)),
    'cat': ((155, 120, 220), (205, 180, 250), (80, 50, 140)),
    'fox': ((225, 135, 60), (255, 205, 150), (130, 60, 20)),
    'knight': ((100, 115, 150), (175, 190, 220), (50, 65, 100)),
    'merchant': ((165, 130, 90), (235, 210, 170), (110, 75, 40)),
    'wizard': ((105, 75, 175), (195, 170, 245), (60, 40, 110)),
    'captain': ((75, 105, 165), (195, 220, 250), (40, 65, 110)),
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
    for key, (bg, fg, acc) in _AVATARS.items():
        api.set_avatar_colors(key, bg, fg, acc)

