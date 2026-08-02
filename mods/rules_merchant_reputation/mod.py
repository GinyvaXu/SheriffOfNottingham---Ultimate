# -*- coding: utf-8 -*-
"""Merchant Reputation rule mod: patches game constants via the mod API."""


def register(api):
    api.patch("game", "REPUTATION", 1)
