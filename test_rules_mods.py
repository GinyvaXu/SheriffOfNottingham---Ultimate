# -*- coding: utf-8 -*-
"""Rule mods: room check + one-key install support tests.

1. rules_mods() returns only enabled rule mods (category == "rules"),
   never reskin mods.
2. Server-side check: a guest without the host's rule mods is flagged
   (lobby mods_ok=False) and the host cannot start the game.
3. A guest with the exact same rule mods (id + version) makes the room
   ready and the game starts.

Usage: python test_rules_mods.py
"""
import io as _io
import json
import os
import shutil
import tempfile
import time

import mods
import net

RULES = [{"id": "marathon_market", "version": "1.4.0"}]
RULE_FOLDERS = ["rules_marathon_market", "rules_spice_road"]


def _enable(base, folder):
    p = os.path.join(base, folder, "mod.json")
    with _io.open(p, encoding="utf-8") as f:
        d = json.load(f)
    d["enabled"] = True
    with _io.open(p, "w", encoding="utf-8") as f:
        json.dump(d, f)


def _wait_lobby(client, timeout=8):
    deadline = time.time() + timeout
    while time.time() < deadline:
        for m in client.poll():
            if m.get("t") == "lobby":
                return m
        time.sleep(0.05)
    return None


def _wait_lobby_cond(client, pred, timeout=8):
    """Wait until a lobby message satisfies pred; returns it or None."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        for m in client.poll():
            if m.get("t") == "lobby" and pred(m):
                return m
        time.sleep(0.05)
    return None


def _drain(client, timeout=1.0):
    time.sleep(timeout)
    return [m for m in client.poll()]


def main():
    old_env = os.environ.get("SHERIFF_MODS_DIR")
    tmp = tempfile.mkdtemp(prefix="sheriff_rulemods_")
    try:
        base = os.path.join(tmp, "mods")
        for folder in RULE_FOLDERS:
            shutil.copytree(os.path.join("mods", folder), os.path.join(base, folder))
        os.environ["SHERIFF_MODS_DIR"] = base

        # ---- 1. rules_mods() filtering ----
        mods.reset_mods_base_cache()
        mods.load_mods()
        if mods.rules_mods() != []:
            print("FAIL: rule mods must be disabled by default:", mods.rules_mods())
            return 1
        _enable(base, "rules_marathon_market")
        mods.reset_mods_base_cache()
        mods.load_mods()
        got = mods.rules_mods()
        if got != [{"id": "marathon_market", "version": "1.4.0",
                    "name": "Marathon Market", "name_zh": "\u9a6c\u62c9\u677e\u96c6\u5e02"}]:
            print("FAIL: rules_mods() =", got)
            return 1
        print("PASS rules_mods() filter (reskin/disabled excluded)")

        # ---- 2. socket room check ----
        srv = net.GameServer(4, port=5605)
        host = net.GameClient("127.0.0.1", 5605, "Host", rules=RULES)
        guest = net.GameClient("127.0.0.1", 5605, "Guest", rules=[])  # no mods
        hl = _wait_lobby(host)
        gl = _wait_lobby(guest)
        # host sees an extra lobby broadcast right after it joins (before the
        # guest arrived); wait until the room contains both players.
        hl = _wait_lobby_cond(host, lambda m: len(m.get("joined", [])) == 2) or hl
        if not (hl and gl):
            print("FAIL: players did not reach the lobby")
            srv.stop()
            return 1
        if hl.get("mods_ok") is not False or gl.get("mods_ok") is not False:
            print("FAIL: mods_ok should be False:", hl.get("mods_ok"), gl.get("mods_ok"))
            srv.stop()
            return 1
        if hl.get("rules_mods") != RULES:
            print("FAIL: lobby rules_mods =", hl.get("rules_mods"))
            srv.stop()
            return 1
        # host tries to start -> must be rejected
        host.send({"t": "start_game", "rounds": 2})
        msgs = _drain(host)
        if not any(m.get("t") == "error" for m in msgs):
            print("FAIL: start must be rejected when mods mismatch")
            srv.stop()
            return 1
        if srv.game is not None:
            print("FAIL: game started despite mismatch")
            srv.stop()
            return 1
        if not any(m.get("t") == "mods_mismatch" for m in _drain(guest)):
            print("FAIL: mods_mismatch was not broadcast")
            srv.stop()
            return 1
        print("PASS room blocks start on rule-mods mismatch")

        # ---- 3. matching mods -> ready ----
        guest.close()
        time.sleep(0.3)
        guest2 = net.GameClient("127.0.0.1", 5605, "Guest", rules=RULES)
        gl2 = _wait_lobby(guest2)
        hl2 = _wait_lobby(host)
        if not gl2 or gl2.get("mods_ok") is not True or hl2.get("mods_ok") is not True:
            print("FAIL: mods_ok should be True:", gl2 and gl2.get("mods_ok"),
                  hl2 and hl2.get("mods_ok"))
            srv.stop()
            return 1
        host.send({"t": "start_game", "rounds": 2})
        time.sleep(0.9)
        if srv.game is None:
            print("FAIL: game should start when mods match")
            srv.stop()
            return 1
        print("PASS room starts when every player has the same rule mods")

        srv.stop()
    finally:
        os.environ.pop("SHERIFF_MODS_DIR", None)
        if old_env is not None:
            os.environ["SHERIFF_MODS_DIR"] = old_env
        shutil.rmtree(tmp, ignore_errors=True)

    print("ALL RULE MODS TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
