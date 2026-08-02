# -*- coding: utf-8 -*-
"""Royal Favor rule mod: patches game constants via the mod API."""


def register(api):
    api.patch("game", "ROYAL_FAVOR", 1)
