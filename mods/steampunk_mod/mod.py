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
    'APPLE': '黄铜苹果',
    'BLACK_MARKET': '地下锻造坊',
    'BREAD': '锅炉面包',
    'CHEESE': '齿轮奶酪',
    'CHICKEN': '发条禽',
    'COFFEE': '蒸汽咖啡',
    'CROSSBOW': '蒸汽步枪',
    'ROYAL_BLUE_CHEESE': '蓝焰蓝纹',
    'ROYAL_CHICKEN': '蒸汽雄鸡',
    'ROYAL_COARSE_BREAD': '熔炉面包',
    'ROYAL_GOLD_APPLE': '黄金齿轮',
    'ROYAL_GOUDA_CHEESE': '工坊奶酪',
    'ROYAL_GREEN_APPLE': '铜绿果',
    'ROYAL_RYE_BREAD': '铁路黑麦',
    'SILK': '天鹅绒蒸汽丝绸',
    'WINE': '煤烟威士忌',
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
    'DECLARE': '申报清单',
    'INSPECT': '查验',
    'LOAD': '装载锅炉',
    'MARKET': '大集市',
}

_UI_EN = {
    'head': 'Phase: {phase}   Round {r}/{t}   Chief Inspector: {name}',
    'sheriff_tag': '[Chief Inspector] ',
    'subtitle': 'a steampunk reskin | host a room + your own port forwarding',
    'title': 'Sheriff of Steamforge',
}
_UI_ZH = {
    'head': '阶段：{phase}   第 {r}/{t} 回合   总督查：{name}',
    'sheriff_tag': '【总督查】',
    'subtitle': '蒸汽朋克皮肤 | 房主开房 + 自行端口映射联机',
    'title': '蒸汽锻炉城警长',
}



_AVATARS = {
    'pig': ((220, 150, 120), (250, 195, 160), (150, 70, 40)),
    'chicken': ((215, 175, 80), (245, 220, 130), (170, 110, 30)),
    'cat': ((185, 130, 70), (235, 195, 140), (95, 60, 25)),
    'fox': ((195, 120, 65), (245, 195, 145), (110, 60, 25)),
    'knight': ((125, 115, 100), (185, 175, 155), (70, 65, 55)),
    'merchant': ((160, 125, 75), (235, 210, 165), (105, 75, 40)),
    'wizard': ((120, 95, 155), (195, 175, 225), (70, 50, 100)),
    'captain': ((90, 110, 140), (185, 205, 230), (45, 60, 85)),
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

