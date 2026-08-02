# -*- coding: utf-8 -*-
"""GUI smoke: host + 2 bots play 2 rounds, screenshots at milestones."""
import os, sys, time, threading
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pygame
import net
from gui import App

PORT = 5561
app = App(host=True, players=3, port=PORT, name="Host")
app.rounds_input.text = "2"
started = [False]
over = [False]

def bot_loop(name):
    c = net.GameClient("127.0.0.1", PORT, name)
    while not over[0]:
        for m in c.poll():
            t = m.get("t")
            if t == "view":
                if m.get("phase") == "GAME_OVER":
                    return
                p = m.get("prompt") or {}
                k = p.get("kind")
                you = m.get("you", {})
                hand = you.get("hand", [])
                if k == "market_discard":
                    c.send({"t": "market_discard", "cards": []})
                elif k == "market_draw":
                    c.send({"t": "market_draw", "from": "deck"})
                elif k == "load_bag":
                    c.send({"t": "load_bag", "cards": list(range(min(1, len(hand))))})
                elif k == "declare":
                    c.send({"t": "declare", "type": "APPLE"})
                elif k == "bribe":
                    c.send({"t": "bribe", "gold": 0, "msg": ""})
                elif k == "inspect":
                    c.send({"t": "inspect_decision", "action": "pass"})
        time.sleep(0.02)
    c.close()

ts = [threading.Thread(target=bot_loop, args=(f"Bot{i}",), daemon=True) for i in range(2)]
for t in ts: t.start()

frames = 0
shots = 0
while frames < 30000 and not over[0]:
    for ev in pygame.event.get():
        app.handle_event(ev)
    app.process_client_msgs()
    joined_n = len((app.lobby or {}).get("joined", [])) if app.lobby else 0
    if app.screen_name == "lobby" and app.is_host and joined_n >= 2 and not started[0]:
        app._start_game_click()
        started[0] = True
    v = app.view or {}
    p = v.get("prompt") or {}
    k = p.get("kind")
    if app.screen_name == "game" and k:
        hand = (v.get("you") or {}).get("hand", [])
        if k == "market_discard":
            app._send({"t": "market_discard", "cards": []})
        elif k == "market_draw":
            app._send({"t": "market_draw", "from": "deck"})
        elif k == "load_bag":
            app._send({"t": "load_bag", "cards": list(range(min(1, len(hand))))})
        elif k == "declare":
            app._send({"t": "declare", "type": "APPLE"})
        elif k == "bribe":
            app._send({"t": "bribe", "gold": 0, "msg": ""})
        elif k == "inspect":
            app._send({"t": "inspect_decision", "action": "pass"})
    if app.screen_name == "over":
        over[0] = True
    app.draw()
    pygame.display.flip()
    frames += 1
    if frames % 90 == 0 and shots < 3:
        pygame.image.save(app.screen, f"smoke2_{shots}.png")
        shots += 1

for t in ts: t.join(timeout=5)
pygame.image.save(app.screen, "smoke2_over.png")
app.cleanup()
print("SMOKE DONE frames=", frames)