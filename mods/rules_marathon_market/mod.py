# -*- coding: utf-8 -*-
"""Marathon Market rule mod: lengthens the match.

Patches the default rounds-per-player so a normal match lasts longer:
2 -> 3 rounds per player (3-player games 3 -> 4). Rule mods run on the
host server; every player must install the same mod to join a room.
"""


def register(api):
    api.patch("game", "ROUNDS_PER_PLAYER", 3)
    api.patch("game", "ROUNDS_PER_PLAYER_3P", 4)
