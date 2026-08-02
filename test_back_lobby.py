# -*- coding: utf-8 -*-
"""Test: game-over -> back to lobby, and unique names for same-level bots.

Usage: python test_back_lobby.py
"""

import time

import net
from test_bot import Bot


def _last_lobby(bot):
    lobby = None
    for m in bot.c.poll():
        if m.get("t") == "lobby":
            lobby = m
    return lobby


def main():
    srv = net.GameServer(4, port=5603)
    host = Bot("Host", "127.0.0.1", 5603)
    guest = Bot("Guest", "127.0.0.1", 5603)

    deadline = time.time() + 10
    while time.time() < deadline and not (host.in_lobby and guest.in_lobby):
        host.act_once()
        guest.act_once()
        time.sleep(0.05)
    if not (host.in_lobby and guest.in_lobby):
        print("FAIL: players did not enter the lobby")
        srv.stop()
        return 1

    # host adds two bots of the SAME level -> must be distinguishable
    host.c.send({"t": "add_bot", "level": "easy"})
    host.c.send({"t": "add_bot", "level": "easy"})
    time.sleep(0.4)
    lobby = _last_lobby(host)
    bot_names = sorted(j["name"] for j in lobby.get("joined", []) if j.get("bot"))
    if bot_names != ["Bot-Easy 1", "Bot-Easy 2"]:
        print(f"FAIL: same-level bot names not unique: {bot_names}")
        srv.stop()
        return 1
    print("unique bot names OK:", bot_names)

    # start a game, force it to GAME_OVER, then go back to the lobby
    host.c.send({"t": "ready"})
    guest.c.send({"t": "ready"})
    time.sleep(0.2)
    host.c.send({"t": "start_game", "rounds": 2})
    time.sleep(0.6)
    if srv.game is None:
        print("FAIL: game did not start")
        srv.stop()
        return 1
    srv.game.phase = "GAME_OVER"
    time.sleep(0.2)

    # a non-host player triggers back_to_lobby
    guest.c.send({"t": "back_to_lobby"})
    time.sleep(0.5)

    if srv.started or srv.game is not None:
        print(f"FAIL: server did not reset (started={srv.started} game={srv.game})")
        srv.stop()
        return 1
    lobby = _last_lobby(host)
    joined = lobby.get("joined", [])
    names = sorted(j["name"] for j in joined)
    expected = ["Bot-Easy 1", "Bot-Easy 2", "Guest", "Host"]
    if names != expected:
        print(f"FAIL: seats after back-to-lobby = {names}, expected {expected}")
        srv.stop()
        return 1
    print("back-to-lobby OK, room kept:", names)

    srv.stop()
    print("PASS: back-to-lobby + unique bot names")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
