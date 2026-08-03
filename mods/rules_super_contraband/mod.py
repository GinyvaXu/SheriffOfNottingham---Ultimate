# -*- coding: utf-8 -*-
"""Super Contraband rule mod: one triple-value/triple-fine card per type."""


def register(api):
    api.patch("game", "SUPER_CONTRA", 1)
    types_en = api.get("game", "TYPE_EN")
    types_zh = api.get("game", "TYPE_ZH")
    colors = api.get("gui", "TYPE_COLOR")
    for t in api.get("game", "CONTRABAND"):
        key = "SUPER_" + t
        api.set_type_name(key, "Super " + types_en.get(t, t),
                          "超级" + types_zh.get(t, t))
        c = colors.get(t, (180, 180, 180))
        api.set_type_color(key, tuple(min(255, x + 50) for x in c))
