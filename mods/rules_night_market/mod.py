# -*- coding: utf-8 -*-
"""Night Market Timer rule mod: patches game constants via the mod API."""


def register(api):
    api.patch("game", "ACTION_TIMEOUT", 40)
