# -*- coding: utf-8 -*-
"""Bribe Economics rule mod: patches game constants via the mod API."""


def register(api):
    api.patch("game", "BRIBE_POT_RATIO", 0.5)
