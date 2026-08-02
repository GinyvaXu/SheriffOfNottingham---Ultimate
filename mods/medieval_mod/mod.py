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
    'APPLE': '果园苹果',
    'BLACK_MARKET': '走私者巢穴',
    'BREAD': '燕麦面包',
    'CHEESE': '修道院奶酪',
    'CHICKEN': '肥育阉鸡',
    'COFFEE': '阿拉伯咖啡',
    'CROSSBOW': '战弩',
    'ROYAL_BLUE_CHEESE': '贵族蓝纹',
    'ROYAL_CHICKEN': '王室烤禽',
    'ROYAL_COARSE_BREAD': '农夫粗粮',
    'ROYAL_GOLD_APPLE': '金纹章果',
    'ROYAL_GOUDA_CHEESE': '院长奶酪',
    'ROYAL_GREEN_APPLE': '绿纹章果',
    'ROYAL_RYE_BREAD': '修士黑麦',
    'SILK': '弗兰德丝绸',
    'WINE': '修士蜜酒',
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
    'DECLARE': '申报',
    'INSPECT': '搜查',
    'LOAD': '装货',
    'MARKET': '赶集日',
}

_UI_EN = {
    'head': 'Phase: {phase}   Round {r}/{t}   Sheriff: {name}',
    'sheriff_tag': '[Sheriff] ',
    'subtitle': 'a medieval reskin | host a room + your own port forwarding',
    'title': 'Sheriff of Medieval Nottingham',
}
_UI_ZH = {
    'head': '阶段：{phase}   第 {r}/{t} 回合   郡长：{name}',
    'sheriff_tag': '【郡长】',
    'subtitle': '中世纪皮肤 | 房主开房 + 自行端口映射联机',
    'title': '中世纪诺丁汉警长',
}



_AVATARS = {
    'pig': ((210, 140, 130), (240, 185, 170), (130, 60, 50)),
    'chicken': ((220, 180, 80), (250, 225, 140), (180, 110, 30)),
    'cat': ((200, 150, 90), (240, 205, 150), (90, 60, 30)),
    'fox': ((200, 110, 60), (250, 200, 160), (110, 55, 25)),
    'knight': ((120, 130, 145), (180, 190, 205), (70, 80, 95)),
    'merchant': ((170, 130, 85), (235, 210, 165), (115, 75, 40)),
    'wizard': ((125, 95, 165), (205, 180, 240), (75, 50, 110)),
    'captain': ((95, 120, 165), (200, 220, 245), (50, 70, 110)),
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

