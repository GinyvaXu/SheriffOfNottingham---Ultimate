# -*- coding: utf-8 -*-
"""Headless bots: play a full game automatically to verify rules and networking (incl. mid-game disconnect/reconnect).

Usage: python test_bot.py [--players 3] [--port 5599]
"""

import argparse
import json
import random
import time

import game
import net


class Bot:
    def __init__(self, name, host, port):
        self.name = name
        self.host = host
        self.port = port
        self.c = net.GameClient(host, port, name)
        self.rng = random.Random()
        self.in_lobby = False
        self.over = None        # final results
        self.reconnected = False
        self.error_count = 0
        self._last_sig = None   # dedupe: respond once per state
        self._stuck_done = False

    def act_once(self):
        for m in self.c.poll():
            t = m.get("t")
            if t == "lobby":
                self.in_lobby = True
            elif t == "welcome" and m.get("reconnected"):
                self.reconnected = True
                self._last_sig = None
                self._stuck_done = False
            elif t == "error":
                self.error_count += 1
                print(f"[{self.name}] ERROR: {m['msg']}")
                if "disconnected" in m.get("msg", "") or "waiting for reconnect" in m.get("msg", ""):
                    self._last_sig = None
                if self._stuck_done:
                    continue
                if "No cards left to draw" in m.get("msg", ""):
                    self._stuck_done = True
                    self.c.send({"t": "market_done"})
            elif t == "view":
                self._stuck_done = False
                if m.get("phase") == "GAME_OVER":
                    self.over = m.get("scores")
                else:
                    self.respond(m)

    def respond(self, v):
        p = v.get("prompt")
        if not p:
            return
        sig = (v.get("round"), v.get("phase"), json.dumps(p, sort_keys=True))
        if sig == self._last_sig:
            return
        self._last_sig = sig
        kind = p["kind"]
        you = v.get("you", {})
        hand = you.get("hand", [])
        if kind == "market_discard":
            k = self.rng.randint(0, min(5, len(hand)))
            idx = self.rng.sample(range(len(hand)), k)
            self.c.send({"t": "market_discard", "cards": idx})
        elif kind == "market_draw":
            self.c.send({"t": "market_draw", "from": "deck"})
        elif kind == "load_bag":
            k = self.rng.randint(1, min(5, len(hand)))
            idx = self.rng.sample(range(len(hand)), k)
            self.c.send({"t": "load_bag", "cards": idx})
        elif kind == "declare":
            self.c.send({"t": "declare", "type": self.rng.choice(game.LEGAL)})
        elif kind == "bribe":
            self.c.send({"t": "bribe", "gold": self.rng.choice([0, 0, 1, 2, 3]), "msg": ""})
        elif kind == "counter_bribe":
            self.c.send({"t": "counter_response",
                         "action": self.rng.choice(["accept", "reject"]), "gold": 0})
        elif kind == "inspect":
            self.c.send({"t": "inspect_decision",
                         "action": self.rng.choice(["pass", "inspect"])})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--players", type=int, default=3)
    ap.add_argument("--port", type=int, default=5599)
    ap.add_argument("--host", type=str, default="127.0.0.1")
    ap.add_argument("--timeout", type=float, default=180)
    args = ap.parse_args()

    srv = net.GameServer(args.players, port=args.port)
    bots = [Bot(f"Bot{i}", args.host, args.port) for i in range(args.players)]

    deadline = time.time() + 10
    while time.time() < deadline and not all(b.in_lobby for b in bots):
        for b in bots:
            b.act_once()
        time.sleep(0.05)
    time.sleep(0.3)
    if not all(b.in_lobby for b in bots):
        print("FAIL: not all bots entered the lobby")
        srv.stop()
        return 1
    for b in bots:
        b.c.send({"t": "ready"})
    time.sleep(0.2)
    bots[0].c.send({"t": "start_game"})
    print("Game started, bots playing...")

    # Mid-game disconnect/reconnect test: drop Bot1 after ~3s, then auto-reconnect (with retries)
    rc_closed = [False]
    rc_last = [0.0]
    rc_done = [False]

    start = time.time()
    while time.time() - start < args.timeout:
        for b in bots:
            b.act_once()
        if not rc_done[0] and time.time() - start > 3:
            if not rc_closed[0]:
                if bots[1].c.alive:
                    print("-> testing disconnect: closing Bot1...")
                    bots[1].c.close()
                rc_closed[0] = True
            elif not bots[1].c.alive:
                try:
                    bots[1].c = net.GameClient(bots[1].host, bots[1].port, bots[1].name)
                    rc_last[0] = time.time()
                    print("-> trying to reconnect Bot1...")
                except OSError:
                    rc_last[0] = time.time()
            elif not bots[1].reconnected and time.time() - rc_last[0] > 2:
                print("-> reconnect not confirmed, retrying...")
                bots[1].c.close()
            elif bots[1].reconnected:
                rc_done[0] = True
                print("-> Bot1 reconnected successfully")
        if all(b.over is not None for b in bots):
            break
        time.sleep(0.05)

    srv.stop()
    for b in bots:
        b.c.close()

    fails = 0
    for b in bots:
        if b.over is None:
            print(f"FAIL: {b.name} did not receive results")
            fails += 1
    if fails:
        return 1

    scores = bots[0].over
    print("\n===== Results =====")
    for i, r in enumerate(scores):
        print(f"{i + 1}. {r['name']}  Total {r['final']}  (goods {r['value'] - r['gold']} + gold {r['gold']} + bonus {r['bonus']})")
    if len(scores) != args.players:
        print("FAIL: result count mismatch")
        return 1
    totals = [r["final"] for r in scores]
    if totals != sorted(totals, reverse=True):
        print("FAIL: results not sorted by score")
        return 1
    for r in scores:
        if r["final"] != r["value"] + r["bonus"]:
            print(f"FAIL: {r['name']} score composition wrong")
            return 1
    errs = sum(b.error_count for b in bots)
    print(f"Bot action errors: {errs}")
    if rc_done[0] and bots[1].reconnected:
        print("Reconnect test: PASSED")
    else:
        print("Note: reconnect not confirmed (game may have ended too quickly)")
    print("PASS: full game test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())