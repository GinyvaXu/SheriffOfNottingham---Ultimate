# -*- coding: utf-8 -*-
"""GUI polish smoke: walk every screen in both languages, save screenshots."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pygame
from gui import App

OUT = "smoke3"
os.makedirs(OUT, exist_ok=True)
shots = []

def snap(app, name):
    app.draw()
    pygame.display.flip()
    pygame.image.save(app.screen, os.path.join(OUT, name + ".png"))
    shots.append(name)

for lng in ("zh", "en"):
    print("app", lng, flush=True)
    app = App(lang_name=lng, name="Tester")
    app._rebuild_menu_ui()
    snap(app, "menu_%s" % lng)
    app._open_mods()
    snap(app, "mods_%s" % lng)
    app._open_market()
    app.market_state = "ready"
    app.market_mods = []
    snap(app, "market_%s" % lng)
    app.screen_name = "update"
    app.update_info = {
        "version": "9.9.9", "current": "1.5.0", "url": "", "available": True,
        "notes": ("v9.9.9 changelog:\n- New GUI polish and layout\n- Rule mods: Bribe Economics, "
                  "Night Market, Trade Caravans, Guild Contracts, Royal Favor, Merchant Reputation\n"
                  "- Bot personalities (Paranoid / Greedy / Honest / Reckless)\n"
                  "- Rule-mod compatibility warnings\n- Update page shows the full changelog"),
    }
    app.update_state = "available"
    app._rebuild_update_ui()
    snap(app, "update_%s" % lng)
    if app.server:
        app.server.stop()
    if app.client:
        app.client.close()

app = App(host=True, players=4, port=5565, name="Host", lang_name="zh")
app.rounds_input.text = "9"
app.lobby = {
    "max_players": 4, "can_start": True,
    "joined": [
        {"seat": 0, "name": "Host", "host": True, "avatar": {"kind": "builtin", "id": "knight"}},
        {"seat": 1, "name": "Bot-Normal (Greedy) 1", "host": False, "bot": "normal",
         "avatar": {"kind": "builtin", "id": "fox"}, "personality": "greedy"},
        {"seat": 2, "name": "Bot-Hard (Paranoid) 1", "host": False, "bot": "hard",
         "avatar": {"kind": "builtin", "id": "captain"}, "personality": "paranoid"},
        {"seat": 3, "name": "Bob", "host": False, "avatar": {"kind": "builtin", "id": "pig"}},
    ],
    "rules_mods": [
        {"id": "bribe_pot", "name": "Bribe Economics", "name_zh": "bribe", "version": "1.4.1"},
        {"id": "guild_contracts", "name": "Guild Contracts", "name_zh": "guild", "version": "1.4.1"},
        {"id": "royal_favor", "name": "Royal Favor", "name_zh": "royal", "version": "1.4.1"},
    ],
    "players_mods": [
        {"seat": 0, "name": "Host", "mods": [{"id": "bribe_pot", "version": "1.4.1"}]},
        {"seat": 3, "name": "Bob", "mods": [{"id": "bribe_pot", "version": "1.4.1"}]},
    ],
    "mods_ok": True,
    "rmods_conflicts": [["guild_contracts", "royal_favor"]],
}
app.screen_name = "lobby"
app.is_host = True
app._rebuild_lobby_ui()
snap(app, "lobby_host")
app.is_host = False
app.lobby_mods_ok = False
app._rebuild_lobby_ui()
snap(app, "lobby_guest")
app.cleanup()
print("SMOKE3 DONE:", len(shots))
