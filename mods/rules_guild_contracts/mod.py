# -*- coding: utf-8 -*-
"""Guild Contracts rule mod: patches game constants via the mod API."""


def register(api):
    api.patch("game", "GUILD_CONTRACTS", 2)
