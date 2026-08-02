# -*- coding: utf-8 -*-
"""Cyberpunk Overlay reskin mod: renames all goods + key UI terms to a Cyberpunk Overlay theme.

Text-only overlay: the card type keys stay unchanged, so this mod only affects
the local client. During online play every player sees their own reskin while
the server keeps running with the canonical rules. Ships disabled by default;
enable it from the in-game Mods screen and restart.
"""

_NAMES_EN = {
    'POT': 'Data Credits',
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
    'POT': '数据信用点',
    'APPLE': '合成果',
    'BLACK_MARKET': '暗网',
    'BREAD': '营养面包',
    'CHEESE': '纳米乳品',
    'CHICKEN': '培养蛋白',
    'COFFEE': '神经兴奋剂',
    'CROSSBOW': '磁轨枪',
    'ROYAL_BLUE_CHEESE': '赛博蓝乳',
    'ROYAL_CHICKEN': '生化烤肉',
    'ROYAL_COARSE_BREAD': '数据面包',
    'ROYAL_GOLD_APPLE': '镀金果',
    'ROYAL_GOUDA_CHEESE': '量子乳品',
    'ROYAL_GREEN_APPLE': '铬果',
    'ROYAL_RYE_BREAD': '电路黑麦',
    'SILK': '记忆丝绸',
    'WINE': '夜酿',
}

_COLORS = {
    'POT': (0, 255, 180),
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



_AVATARS = {
    'pig': ((255, 50, 170), (255, 130, 210), (150, 0, 90)),
    'chicken': ((255, 210, 40), (255, 240, 130), (200, 80, 0)),
    'cat': ((255, 120, 30), (255, 180, 100), (120, 40, 0)),
    'fox': ((255, 60, 60), (255, 140, 130), (160, 0, 0)),
    'knight': ((80, 170, 255), (160, 220, 255), (0, 90, 200)),
    'merchant': ((180, 200, 220), (230, 240, 250), (90, 110, 130)),
    'wizard': ((170, 60, 255), (220, 150, 255), (90, 0, 160)),
    'captain': ((0, 220, 210), (150, 255, 245), (0, 130, 120)),
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

