# -*- coding: utf-8 -*-
"""Starlight Colony reskin mod: renames all goods + key UI terms to a Starlight Colony theme.

Text-only overlay: the card type keys stay unchanged, so this mod only affects
the local client. During online play every player sees their own reskin while
the server keeps running with the canonical rules. Ships disabled by default;
enable it from the in-game Mods screen and restart.
"""

_NAMES_EN = {
    'APPLE': 'Hydroponic Fruit',
    'BLACK_MARKET': 'Smuggler Ring',
    'BREAD': 'Nutri-Paste Loaf',
    'CHEESE': 'Synth-Curd',
    'CHICKEN': 'Protein Slabs',
    'COFFEE': 'Gravity Brew',
    'CROSSBOW': 'Plasma Rifles',
    'ROYAL_BLUE_CHEESE': 'Blue Dwarf',
    'ROYAL_CHICKEN': 'Geno-Turkey',
    'ROYAL_COARSE_BREAD': 'Dust Bread',
    'ROYAL_GOLD_APPLE': 'Star Fruit',
    'ROYAL_GOUDA_CHEESE': 'Cryo-Curd',
    'ROYAL_GREEN_APPLE': 'Terra Fruit',
    'ROYAL_RYE_BREAD': 'Asteroid Rye',
    'SILK': 'Zero-G Silk',
    'WINE': 'Nebula Wine',
}

_NAMES_ZH = {
    'APPLE': '水培果',
    'BLACK_MARKET': '走私星环',
    'BREAD': '营养膏包',
    'CHEESE': '合成凝乳',
    'CHICKEN': '蛋白块',
    'COFFEE': '引力咖啡',
    'CROSSBOW': '等离子步枪',
    'ROYAL_BLUE_CHEESE': '蓝矮星凝乳',
    'ROYAL_CHICKEN': '基因火鸡',
    'ROYAL_COARSE_BREAD': '星尘面包',
    'ROYAL_GOLD_APPLE': '恒星果',
    'ROYAL_GOUDA_CHEESE': '冷冻凝乳',
    'ROYAL_GREEN_APPLE': '移民果',
    'ROYAL_RYE_BREAD': '小行星黑麦',
    'SILK': '零重力丝绸',
    'WINE': '星云酒',
}

_COLORS = {
    'APPLE': (120, 230, 150),
    'BLACK_MARKET': (90, 200, 255),
    'BREAD': (200, 170, 110),
    'CHEESE': (250, 230, 140),
    'CHICKEN': (180, 140, 220),
    'COFFEE': (140, 90, 60),
    'CROSSBOW': (90, 160, 255),
    'ROYAL_BLUE_CHEESE': (70, 110, 255),
    'ROYAL_CHICKEN': (200, 120, 200),
    'ROYAL_COARSE_BREAD': (120, 100, 80),
    'ROYAL_GOLD_APPLE': (255, 210, 50),
    'ROYAL_GOUDA_CHEESE': (230, 210, 120),
    'ROYAL_GREEN_APPLE': (60, 190, 110),
    'ROYAL_RYE_BREAD': (150, 120, 90),
    'SILK': (150, 120, 255),
    'WINE': (170, 90, 200),
}

_PHASES_EN = {
    'DECLARE': 'Customs Form',
    'INSPECT': 'Scan Hold',
    'LOAD': 'Cargo Load',
    'MARKET': 'Trade Deck',
}
_PHASES_ZH = {
    'DECLARE': '报关',
    'INSPECT': '货舱扫描',
    'LOAD': '装载货舱',
    'MARKET': '贸易甲板',
}

_UI_EN = {
    'head': 'Phase: {phase}   Round {r}/{t}   Patrol AI: {name}',
    'sheriff_tag': '[Patrol AI] ',
    'subtitle': 'a space reskin | host a room + your own port forwarding',
    'title': 'Sheriff of Starlight Colony',
}
_UI_ZH = {
    'head': '阶段：{phase}   第 {r}/{t} 回合   巡逻AI：{name}',
    'sheriff_tag': '【巡逻AI】',
    'subtitle': '星际皮肤 | 房主开房 + 自行端口映射联机',
    'title': '星光殖民地警长',
}



_AVATARS = {
    'pig': ((240, 130, 190), (255, 190, 225), (180, 60, 130)),
    'chicken': ((200, 200, 120), (250, 245, 170), (140, 140, 40)),
    'cat': ((170, 130, 240), (215, 190, 255), (90, 60, 160)),
    'fox': ((120, 200, 250), (190, 235, 255), (40, 120, 190)),
    'knight': ((150, 220, 235), (210, 245, 255), (70, 150, 175)),
    'merchant': ((190, 210, 225), (235, 245, 250), (110, 140, 160)),
    'wizard': ((160, 120, 255), (215, 190, 255), (90, 50, 180)),
    'captain': ((70, 150, 255), (170, 210, 255), (30, 80, 190)),
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

