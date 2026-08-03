# -*- coding: utf-8 -*-
"""Smoke render: event strip (name + detailed desc), rumor button, plague greyout."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pygame
from gui import App

OUT = "smoke3"
os.makedirs(OUT, exist_ok=True)

def snap(app, name):
    app.draw()
    pygame.display.flip()
    pygame.image.save(app.screen, os.path.join(OUT, name + ".png"))
    print("saved", name, flush=True)

av = lambda i: {"kind": "builtin", "id": i}
card = lambda t, v=None: {"type": t, "value": v or 3, "fine": 2}

def make_app(lng):
    app = App(lang_name=lng, name="Me")
    app.screen_name = "game"
    app.my_seat = 0
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
    base = {
        "t": "view", "phase": "INSPECT", "round": 3, "rounds_total": 9, "sheriff": 2,
        "players": players, "deck_count": 12, "acting": "Sheriff Bob", "acting_phase": "inspect",
        "black_market": None, "route": None, "pot": 0,
        "you": {"hand": [card("APPLE", 2), card("COFFEE", 6), card("ROYAL_GREEN_APPLE", 4)],
                "bag": [], "stand_contra": [], "black_market_cards": 0, "contracts": [],
                "reputation": 0, "royal_favor": 0},
    }
    return app, base

for lng in ("zh", "en"):
    # 1) LOCKDOWN event strip, inspect prompt with rumor button
    app, base = make_app(lng)
    base["event"] = "LOCKDOWN"
    base["prompt"] = {"kind": "inspect", "owner": "Alice", "bribe_gold": 3,
                      "rumor_ok": True, "round": 1, "max_round": 3}
    app.view = base
    app._rebuild_game_ui()
    snap(app, "event_lockdown_rumor_%s" % lng)

    # 2) PLAGUE event strip + banned good
    app, base = make_app(lng)
    base["event"] = "PLAGUE"
    base["plague"] = "APPLE"
    base["prompt"] = {"kind": "inspect", "owner": "Alice"}
    app.view = base
    app._rebuild_game_ui()
    snap(app, "event_plague_%s" % lng)

    # 3) Load bag prompt with famine max + plague banned greyout
    app, base = make_app(lng)
    base["event"] = "FAMINE"
    base["phase"] = "LOAD"
    base["prompt"] = {"kind": "load_bag", "bag_max": 4, "banned": "APPLE", "hand": 5}
    base["you"]["hand"] = [card("APPLE", 2), card("COFFEE", 6), card("BREAD", 3),
                           card("APPLE", 2), card("CHICKEN", 4)]
    app.view = base
    app._rebuild_game_ui()
    snap(app, "event_load_banned_%s" % lng)

print("DONE", flush=True)
