# -*- coding: utf-8 -*-
"""Example mod: demonstrates adding card types and patching the engine.

Copy this folder, rename it, set "enabled": true in mod.json, then restart.
All players in a room need the same mod for online play.
"""


def register(api):
    # New contraband: Tea (5 gold, caught fine 3, 8 cards at 3p / 12 at 4-6p)
    api.add_contraband("TEA", "Tea", "\u8336\u53f6", value=5, fine=3,
                       cnt3=8, cnt6=12, color=(96, 156, 120))

    # New legal good: Pear (2 gold, king/queen end bonuses 10/5)
    api.add_legal("PEAR", "Pear", "\u68a8\u5b50", value=2, fine=2,
                  cnt3=10, cnt6=14, color=(206, 182, 92),
                  king_bonus=10, queen_bonus=5)

    # Modify the game itself: uncomment to change hand size to 7
    # api.patch("game", "HAND_SIZE", 7)

    # Read values: api.get("game", "BAG_MAX")
