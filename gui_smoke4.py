# -*- coding: utf-8 -*-
"""Smoke render: lobby ready bar + game panel (stall colors, bag line,
black market secrecy, scrollable chat). Run once per language."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pygame
from gui import App

OUT = "smoke3"
os.makedirs(OUT, exist_ok=True)
lng = sys.argv[1] if len(sys.argv) > 1 else "zh"

def snap(app, name):
    app.draw()
    pygame.display.flip()
    pygame.image.save(app.screen, os.path.join(OUT, name + ".png"))
    print("saved", name, flush=True)

av = lambda i: {"kind": "builtin", "id": i}
card = lambda t, v=None: {"type": t, "value": v or 3, "fine": 2}

# ---------- lobby with ready bar ----------
app = App(lang_name=lng, name="Host")
app.my_seat = 0
app.is_host = True
app.rounds_input.text = "9"
app.lobby = {
    "max_players": 5, "can_start": False,
    "joined": [
        {"seat": 0, "name": "Host", "host": True, "ready": True, "avatar": av("knight")},
        {"seat": 1, "name": "Alice", "host": False, "ready": True, "avatar": av("pig")},
        {"seat": 2, "name": "Bob", "host": False, "ready": False, "avatar": av("fox")},
        {"seat": 3, "name": "Bot-Easy 1", "host": False, "bot": "easy", "ready": True,
         "avatar": av("captain"), "personality": "greedy"},
    ],
    "rules_mods": [], "players_mods": [], "mods_ok": True, "rmods_conflicts": [],
}
app.screen_name = "lobby"
app._rebuild_lobby_ui()
snap(app, "new_lobby_ready_%s" % lng)

# ---------- game panel ----------
app2 = App(lang_name=lng, name="Me")
app2.screen_name = "game"
app2.my_seat = 0
players = [
    {"name": "Me", "avatar": av("knight"), "gold": 42, "hand_count": 5, "bag_size": 3,
     "stand_legal": {"APPLE": 4, "CHEESE": 2, "BREAD": 1},
     "stand_royal": ["ROYAL_GREEN_APPLE", "ROYAL_CHICKEN"],
     "smuggle_count": 2, "connected": True, "decl": {"type": "APPLE", "count": 3},
     "reputation": 0, "royal_favor": 0},
    {"name": "Alice", "avatar": av("pig"), "gold": 30, "hand_count": 6, "bag_size": 0,
     "stand_legal": {"BREAD": 3}, "stand_royal": [], "smuggle_count": 0,
     "connected": True, "decl": None, "reputation": 0, "royal_favor": 0},
    {"name": "Sheriff Bob", "avatar": av("fox"), "gold": 55, "hand_count": 6, "bag_size": 0,
     "stand_legal": {"CHICKEN": 2}, "stand_royal": [], "smuggle_count": 1,
     "connected": True, "decl": None, "reputation": 0, "royal_favor": 0},
]
bm = {
    "types": ["COFFEE", "SILK", "WINE"],
    "rewards": {"COFFEE": [33, 27], "SILK": [34, 28], "WINE": [31, 26]},
    "claimed": {"COFFEE": 1, "SILK": 0, "WINE": 0},
    "claimers": {"COFFEE": ["Alice", None], "SILK": [None, None], "WINE": [None, None]},
    "need": 3,
}
app2.view = {
    "t": "view", "phase": "INSPECT", "round": 3, "rounds_total": 9, "sheriff": 2,
    "players": players, "deck_count": 12, "acting": "Sheriff Bob", "acting_phase": "inspect",
    "black_market": bm, "route": None, "pot": 0,
    "prompt": {"kind": "counter_bribe", "owner": "Me", "demand": 10, "last_offer": 4,
               "round": 1, "max_round": 3},
    "you": {"hand": [card("APPLE", 2), card("COFFEE", 6), card("ROYAL_GREEN_APPLE", 4)],
            "bag": [card("APPLE", 2), card("COFFEE", 6), card("WINE", 7)],
            "stand_contra": [card("COFFEE", 6), card("COFFEE", 6), card("WINE", 7),
                             card("ROYAL_GREEN_APPLE", 4)],
            "black_market_cards": 1, "contracts": [], "reputation": 0, "royal_favor": 0},
}
for i in range(40):
    app2._append_chat("Line %d: long chat message for scrolling test line %d" % (i, i), None)
app2._rebuild_game_ui()
snap(app2, "new_game_bargain_%s" % lng)
print("DONE", lng, flush=True)
