# -*- coding: utf-8 -*-
"""Sheriff Intel rule mod: pay gold to learn a bucket of contraband remaining.

Implemented in game.Game.do_sheriff_intel; this mod only switches it on.
"""


def register(api):
    api.patch("game", "SHERIFF_INTEL", 1)
