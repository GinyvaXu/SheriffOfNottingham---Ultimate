# -*- coding: utf-8 -*-
"""In-game GUI smoke (single language per process): renders every phase x
3/4/5/6 players, with/without black market and events; asserts all buttons
stay in the canvas and never overlap each other; asserts layout zones never
collide. Screenshots saved under smoke5/."""
import os, sys, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
from gui import App, W, H

OUT = "smoke5"
os.makedirs(OUT, exist_ok=True)
errors = []

def check(app, name):
    try:
        app._last_drawn_screen = app.screen_name  # keep the fade finished
        app._fade_t = None
        app._present_valid = False
        app.draw()
    except Exception:
        errors.append("%s: DRAWEXC %s" % (name, traceback.format_exc(limit=3).replace("\n", " | ")))
        return
    rects = []
    for b in app.hand_buttons + app.buttons:
        r = b.rect
        if r.right > W + 1 or r.bottom > H + 1 or r.left < -1 or r.top < -1:
            errors.append("%s: out-of-canvas %r %r" % (name, r, b.text[:20]))
        for o in rects:
            if r.colliderect(o[0]):
                errors.append("%s: OVERLAP %r %r <=> %r %r"
                              % (name, r, b.text[:14], o[0], o[1][:14]))
        rects.append((r, b.text or ""))
    pygame.image.save(app.screen, os.path.join(OUT, name + ".png"))
    open("smoke5_progress.txt", "a", encoding="utf-8").write(name + "\n")

def zone_check(app, name):
    lay = app.game_lay
    zones = [
        ("chat", pygame.Rect(lay["chat_rect"])),
        ("players", pygame.Rect(16, lay["play_top"], 880, lay["play_h"])),
        ("bm", pygame.Rect(16, lay["bm_top"], 880, lay["bm_h"]) if lay["bm_h"] else None),
        ("bag", pygame.Rect(16, lay["bag_y"], 880, 26)),
        ("hand", pygame.Rect(16, lay["hand_y"], 860, 120)),
        ("instr", pygame.Rect(16, lay["instr_y"], 880, 24)),
        ("act", pygame.Rect(16, lay["act_y"], 880, 42)),
        ("top", pygame.Rect(0, 0, 1280, 64)),
    ]
    zl = [z for z in zones if z[1]]
    for a in range(len(zl)):
        for b in range(a + 1, len(zl)):
            if zl[a][1].colliderect(zl[b][1]):
                errors.append("%s: ZONE OVERLAP %s %s" % (name, zl[a][0], zl[b][0]))

av = lambda i: {"kind": "builtin", "id": i}
card = lambda t, v=None: {"type": t, "value": v or 3, "fine": 2}

def make_view(n, prompt, bm=True, event=None, extra=None):
    players = []
    names = ["Me", "Alice", "Bob", "Carol", "Dave", "Eve"]
    for i in range(n):
        p = {"name": names[i], "avatar": av("knight" if i == 0 else "pig"),
             "gold": 30 + i * 5, "hand_count": 6, "bag_size": 3 if i % 2 else 0,
             "stand_legal": {"APPLE": 4, "CHEESE": 2, "BREAD": 1} if i % 2 == 0 else {"APPLE": 2},
             "stand_royal": ["ROYAL_GREEN_APPLE", "ROYAL_CHICKEN"] if i == 0 else [],
             "smuggle_count": 2, "connected": True,
             "decl": {"type": "APPLE", "count": 3} if i % 2 == 0 else None,
             "reputation": 3, "royal_favor": 1}
        players.append(p)
    view = {
        "t": "view", "phase": "INSPECT", "round": 3, "rounds_total": 9,
        "sheriff": n - 1, "players": players, "deck_count": 12,
        "acting": "Alice", "acting_phase": "load",
        "route": "APPLE", "pot": 8, "time_left": 15,
        "prompt": prompt,
        "you": {"hand": [card("APPLE", 2), card("COFFEE", 6),
                         card("ROYAL_GREEN_APPLE", 4), card("WINE", 7),
                         card("CHEESE", 3), card("BREAD", 3), card("SILK", 8)],
                "bag": [card("APPLE", 2), card("COFFEE", 6), card("WINE", 7)],
                "stand_contra": [card("COFFEE", 6), card("COFFEE", 6),
                                 card("WINE", 7), card("ROYAL_GREEN_APPLE", 4)],
                "black_market_cards": 1, "contracts": [{"type": "APPLE", "need": 3}],
                "reputation": 3, "royal_favor": 1},
    }
    if bm:
        view["black_market"] = {
            "types": ["COFFEE", "SILK", "WINE"],
            "rewards": {"COFFEE": [33, 27], "SILK": [34, 28], "WINE": [31, 26]},
            "claimed": {"COFFEE": 1, "SILK": 0, "WINE": 0},
            "claimers": {"COFFEE": ["Alice", None], "SILK": [None, None], "WINE": [None, None]},
            "need": 3,
        }
    if event:
        view["event"] = event
    if extra:
        view.update(extra)
    return view

phases = [
    ("declare", {"kind": "declare", "bag_count": 3}),
    ("load", {"kind": "load_bag", "bag_max": 5}),
    ("market", {"kind": "market_discard", "hand": 6}),
    ("draw", {"kind": "market_draw", "hand": 6, "draw_left": 3}),
    ("bribe", {"kind": "bribe", "owner": "Me"}),
    ("inspect", {"kind": "inspect", "owner": "Alice", "bribe_gold": 6,
                 "bribe_msg": "hi", "round": 1, "max_round": 3}),
    ("counter", {"kind": "counter_bribe", "owner": "Me", "demand": 10,
                 "last_offer": 4, "round": 1, "max_round": 3}),
    ("wait", None),
]

lng = sys.argv[1] if len(sys.argv) > 1 else "zh"
app = App(lang_name=lng, name="Me")
app.screen_name = "game"
app.my_seat = 0
count = 0
for n in (3, 4, 5, 6):
    for pname, pk in phases:
        for bm in (True, False):
            for ev in (None, "BOUNTIFUL"):
                count += 1
                name = "%s_%dp_%s_%s%s" % (lng, n, pname, "bm" if bm else "nobm",
                                           "_ev" if ev else "")
                try:
                    app.view = make_view(n, pk, bm=bm, event=ev)
                    app._rebuild_game_ui()
                    for i in range(20):
                        app._append_chat("Line %d: 测试聊天消息 Test chat %d" % (i, i), None)
                    check(app, name)
                    zone_check(app, name)
                except Exception:
                    errors.append("%s: EXC %s" % (name, traceback.format_exc(limit=3).replace("\n", " | ")))

print("rendered", count, "errors", len(errors))
for e in errors[:60]:
    print(" -", e)
open("smoke5_progress.txt", "a", encoding="utf-8").write("DONE %s errors=%d\n" % (lng, len(errors)))
