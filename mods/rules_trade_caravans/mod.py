# -*- coding: utf-8 -*-
"""Trade Caravans rule mod: patches game constants via the mod API."""


def register(api):
    api.patch("game", "ROUTE_BONUS", 4)
