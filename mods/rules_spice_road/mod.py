# -*- coding: utf-8 -*-
"""Spice Road rule mod: adds new goods.

Adds a new legal goods type (Pepper) and a new contraband type (Tea).
The host server drives the rules; every player must install this mod so
the new cards render correctly on their client.
"""


def register(api):
    api.add_legal("PEPPER", "Pepper", "\u80e1\u6912", value=5, fine=2,
                  cnt3=12, cnt6=16, king_bonus=12, queen_bonus=6,
                  color=(210, 140, 60))
    api.add_contraband("TEA", "Tea", "\u8336\u53f6", value=7, fine=4,
                       cnt3=10, cnt6=14, color=(120, 170, 90))
