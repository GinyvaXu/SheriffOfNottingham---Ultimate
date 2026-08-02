# -*- coding: utf-8 -*-
"""Adult Pleasure Shop reskin mod (18+).

Renames every goods to adult-shop products: vibrating eggs, flesh sleeves,
bondage rope, love potions, silk lingerie, magic wands ... Text-only overlay:
card type keys stay unchanged, so this mod only affects the local client.
Ships disabled by default; enable it from the in-game Mods screen and restart.
"""

_NAMES_EN = {
    'POT': 'Love Potion',
    'APPLE': 'Vibrating Egg',
    'BLACK_MARKET': 'Adult Black Market',
    'BREAD': 'Bondage Rope',
    'CHEESE': 'Anal Bead Set',
    'CHICKEN': 'Flesh Sleeve',
    'COFFEE': 'Blue Pill',
    'CROSSBOW': 'Magic Wand',
    'ROYAL_BLUE_CHEESE': 'Sapphire Plug',
    'ROYAL_CHICKEN': 'Realistic Sleeve',
    'ROYAL_COARSE_BREAD': 'Royal Bondage Set',
    'ROYAL_GOLD_APPLE': 'Diamond Egg',
    'ROYAL_GOUDA_CHEESE': 'Crystal Plug',
    'ROYAL_GREEN_APPLE': 'Golden Egg',
    'ROYAL_RYE_BREAD': 'Leather Rope',
    'SILK': 'Silk Lingerie',
    'WINE': 'Love Charm Champagne',
}

_NAMES_ZH = {
    'POT': '爱情灵药',
    'APPLE': '情趣跳蛋',
    'BLACK_MARKET': '成人黑市',
    'BREAD': '束缚绳',
    'CHEESE': '肛珠套装',
    'CHICKEN': '名器飞机杯',
    'COFFEE': '蓝色小药丸',
    'CROSSBOW': '魔法震动棒',
    'ROYAL_BLUE_CHEESE': '蓝钻肛塞',
    'ROYAL_CHICKEN': '真人名器',
    'ROYAL_COARSE_BREAD': '皇家束缚套组',
    'ROYAL_GOLD_APPLE': '钻石跳蛋',
    'ROYAL_GOUDA_CHEESE': '水晶肛塞',
    'ROYAL_GREEN_APPLE': '金装跳蛋',
    'ROYAL_RYE_BREAD': '真皮束缚绳',
    'SILK': '丝绸情趣内衣',
    'WINE': '催情香槟',
}

_COLORS = {
    'POT': (255, 80, 140),
    'APPLE': (255, 120, 190),
    'BLACK_MARKET': (255, 60, 160),
    'BREAD': (170, 120, 90),
    'CHEESE': (205, 130, 230),
    'CHICKEN': (240, 140, 170),
    'COFFEE': (80, 160, 255),
    'CROSSBOW': (130, 200, 255),
    'ROYAL_BLUE_CHEESE': (150, 110, 255),
    'ROYAL_CHICKEN': (255, 110, 150),
    'ROYAL_COARSE_BREAD': (150, 100, 80),
    'ROYAL_GOLD_APPLE': (255, 190, 60),
    'ROYAL_GOUDA_CHEESE': (240, 170, 90),
    'ROYAL_GREEN_APPLE': (255, 90, 170),
    'ROYAL_RYE_BREAD': (180, 120, 90),
    'SILK': (235, 120, 255),
    'WINE': (255, 70, 120),
}

_PHASES_EN = {
    'DECLARE': 'Report',
    'INSPECT': 'Body Search',
    'LOAD': 'Pack',
    'MARKET': 'Shopping',
}
_PHASES_ZH = {
    'DECLARE': '报备',
    'INSPECT': '搜身',
    'LOAD': '装袋',
    'MARKET': '采购',
}

_UI_EN = {
    'head': 'Phase: {phase}   Round {r}/{t}   Sheriff: {name}',
    'sheriff_tag': '[Lusty Sheriff] ',
    'subtitle': '18+ adult pleasure shop reskin | client-side only',
    'title': 'Sheriff of Lusty Nottingham',
}
_UI_ZH = {
    'head': '阶段：{phase}  第 {r}/{t} 回合  警长：{name}',
    'sheriff_tag': '[风流警长] ',
    'subtitle': '18+ 成人情趣用品店换皮 | 仅客户端生效',
    'title': '风流诺丁汉警长',
}

_AVATARS = {
    'pig': ((255, 60, 150), (255, 150, 200), (180, 20, 90)),
    'chicken': ((255, 130, 60), (255, 200, 150), (200, 60, 20)),
    'cat': ((255, 80, 190), (255, 170, 220), (190, 30, 110)),
    'fox': ((255, 70, 100), (255, 160, 170), (190, 20, 60)),
    'knight': ((180, 90, 220), (230, 180, 255), (110, 30, 150)),
    'merchant': ((255, 120, 160), (255, 200, 215), (190, 50, 90)),
    'wizard': ((200, 60, 200), (250, 160, 250), (120, 20, 120)),
    'captain': ((255, 90, 130), (255, 190, 205), (190, 30, 70)),
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
