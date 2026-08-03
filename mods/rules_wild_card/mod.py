# -*- coding: utf-8 -*-
"""Wild Card rule mod: adds N legal wild cards to the deck.

The host sets the count in the lobby (sent as `wild` when starting the game).
A wild card in a declared bag turns into the declared goods type, so it can be
declared as anything and passes inspection truthfully.
"""


def register(api):
    api.patch("game", "WILD_CARDS", 4)
    api.set_type_name("WILD", "Wild Card", "万能卡")
    api.set_type_color("WILD", (230, 200, 80))
