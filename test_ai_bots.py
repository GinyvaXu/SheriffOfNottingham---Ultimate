# -*- coding: utf-8 -*-
"""AI bots test: host + 2 bots (easy & hard) play a full game via the network.

Usage: python test_ai_bots.py [--port 5601] [--rounds 3]
"""
import argparse
import time

import net
from test_bot import Bot


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=5601)
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--timeout", type=float, default=240)
    args = ap.parse_args()

    srv = net.GameServer(3, port=args.port)
    host = Bot("Host", "127.0.0.1", args.port)

    deadline = time.time() + 10
    while time.time() < deadline and not host.in_lobby:
        host.act_once()
        time.sleep(0.05)
    if not host.in_lobby:
        print("FAIL: host did not enter the lobby")
        srv.stop()
        return 1

    # host adds two bots of different levels
    host.c.send({"t": "add_bot", "level": "easy"})
    host.c.send({"t": "add_bot", "level": "hard"})
    time.sleep(0.4)
    # find latest lobby state from the client queue (do not call act_once here,
    # it drains the queue)
    lobby = None
    for m in host.c.poll():
        if m.get("t") == "lobby":
            lobby = m
    if not lobby:
        print("FAIL: no lobby message after adding bots")
        srv.stop()
        return 1
    bots = [j for j in lobby.get("joined", []) if j.get("bot")]
    if len(bots) != 2:
        print(f"FAIL: expected 2 bots in lobby, got {len(bots)}")
        srv.stop()
        return 1
    levels = sorted(j["bot"] for j in bots)
    if levels != ["easy", "hard"]:
        print(f"FAIL: bot levels wrong: {levels}")
        srv.stop()
        return 1
    print("Lobby bots OK:", [(j["name"], j["bot"]) for j in bots])

    # remove one bot, then re-add it (tests the remove path)
    host.c.send({"t": "remove_bot", "seat": bots[0]["seat"]})
    time.sleep(0.3)
    host.c.send({"t": "add_bot", "level": "normal"})
    time.sleep(0.3)
    for m in host.c.poll():
        if m.get("t") == "lobby":
            lobby = m
    bots = [j for j in lobby.get("joined", []) if j.get("bot")]
    if len(bots) != 2:
        print(f"FAIL: after remove+add expected 2 bots, got {len(bots)}")
        srv.stop()
        return 1
    print("Remove/add bot OK")

    host.c.send({"t": "start_game", "rounds": args.rounds})
    print("Game started with 1 human + 2 bots, playing...")

    start = time.time()
    while time.time() - start < args.timeout:
        host.act_once()
        if host.over is not None:
            break
        time.sleep(0.05)

    srv.stop()
    host.c.close()

    if host.over is None:
        print("FAIL: game did not finish")
        return 1
    names = [r["name"] for r in host.over]
    print("Results:", names, [r["final"] for r in host.over])
    if not any("Bot-" in n for n in names):
        print("FAIL: bot players missing from results")
        return 1
    print(f"PASS: AI bots test passed (errors={host.error_count})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
