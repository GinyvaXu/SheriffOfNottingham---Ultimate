# -*- coding: utf-8 -*-
"""Cyberpunk Overlay reskin mod: renames all goods + key UI terms to a Cyberpunk Overlay theme.

Text-only overlay: the card type keys stay unchanged, so this mod only affects
the local client. During online play every player sees their own reskin while
the server keeps running with the canonical rules. Ships disabled by default;
enable it from the in-game Mods screen and restart.
"""

_NAMES_EN = {
    'APPLE': 'Bio-Apple',
    'BLACK_MARKET': 'DarkNet',
    'BREAD': 'Nutri-Bread',
    'CHEESE': 'Nano-Cheese',
    'CHICKEN': 'Clone-Chicken',
    'COFFEE': 'Neuro-Coffee',
    'CROSSBOW': 'Rail-Bow',
    'ROYAL_BLUE_CHEESE': 'Cyber Blue Cheese',
    'ROYAL_CHICKEN': 'Bionic Chicken',
    'ROYAL_COARSE_BREAD': 'Data Bread',
    'ROYAL_GOLD_APPLE': 'Gold-Plated Apple',
    'ROYAL_GOUDA_CHEESE': 'Quantum Cheese',
    'ROYAL_GREEN_APPLE': 'Chrome Apple',
    'ROYAL_RYE_BREAD': 'Circuit Rye',
    'SILK': 'Nano-Silk',
    'WINE': 'Night-Wine',
}

_NAMES_ZH = {
    'APPLE': '合成苹果',
    'BLACK_MARKET': '暗网',
    'BREAD': '营养面包',
    'CHEESE': '纳米奶酱',
    'CHICKEN': '克隆鸡肉',
    'COFFEE': '神经咖啡',
    'CROSSBOW': '磁轨弩',
    'ROYAL_BLUE_CHEESE': '赛博蓝纹',
    'ROYAL_CHICKEN': '生化鸡肉',
    'ROYAL_COARSE_BREAD': '数据粗粮',
    'ROYAL_GOLD_APPLE': '镀金苹果',
    'ROYAL_GOUDA_CHEESE': '量子奶酱',
    'ROYAL_GREEN_APPLE': '铬苹果',
    'ROYAL_RYE_BREAD': '电路黑麦',
    'SILK': '纳米丝绸',
    'WINE': '夜行酒',
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
    'DECLARE': '广播',
    'INSPECT': '扫描',
    'LOAD': '上传',
    'MARKET': '霓虹市场',
}

_UI_EN = {
    'head': 'Phase: {phase}   Round {r}/{t}   NetBoss: {name}',
    'sheriff_tag': '[NetBoss] ',
    'subtitle': 'a cyberpunk reskin | host a room + your own port forwarding',
    'title': 'Sheriff of Neo-Nottingham',
}
_UI_ZH = {
    'head': '阶段：{phase}   第 {r}/{t} 回合   网警：{name}',
    'sheriff_tag': '【网警】',
    'subtitle': '赛博朋克皮肤 | 房主开房 + 自行端口映射联机',
    'title': '霓虹诺丁汉警长',
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
