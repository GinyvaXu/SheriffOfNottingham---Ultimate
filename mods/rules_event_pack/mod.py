# -*- coding: utf-8 -*-
"""Twists of Fate Event Pack rule mod ("风云变幻事件包").

One public event is revealed at the start of each round and lasts until the
round ends. All effects live in game.Game; this mod only switches them on.
"""


def register(api):
    api.patch("game", "EVENT_PACK", 1)
