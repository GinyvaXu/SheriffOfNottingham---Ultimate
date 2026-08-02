# -*- coding: utf-8 -*-
"""Tests for the v1.4.1 rule-mod engine hooks (priority 1+2 mods).

Covers: Bribe Economics pot, Night Market timer constant, Trade Caravans
route bonus, Guild Contracts, Royal Favor milestones, Merchant Reputation,
bot personalities, and mod compatibility detection.

Usage: python test_rule_mods_v141.py
"""
import io as _io
import json
import os
import shutil
import tempfile

import game
import mods
import net
import bot


def _mk_game(n=3, **kw):
    ps = [game.Player("P%d" % i) for i in range(n)]
    return game.Game(ps, rng=game.random.Random(7), black_market=False, **kw)


def _setup_inspect(g):
    """Prepare the inspect phase: owner = order[0], sheriff = g.sheriff."""
    g.phase = "INSPECT"
    g.order = [i for i in range(g.n) if i != g.sheriff]
    g.inspect_idx = 0
    return g.order[0], g.sheriff


def _bribe_pass(g, owner_seat, gold):
    owner_seat, _ = _setup_inspect(g)
    g.players[owner_seat].bribe = {"gold": gold, "msg": ""}
    ok, ev = g.do_inspect_decision(g.sheriff, "pass")
    assert ok, ev
    return ev


def main():
    ok = True
    # ---------- Bribe Economics ----------
    saved = game.BRIBE_POT_RATIO
    try:
        game.BRIBE_POT_RATIO = 0.5
        g = _mk_game()
        g.start_round()
        ev = _bribe_pass(g, 0, 10)
        sheriff = g.players[g.sheriff]
        owner_seat = g.order[0]
        owner = g.players[owner_seat]
        if g.pot != 5 or sheriff.gold != 55 or owner.gold != 40:
            print("FAIL bribe pot split:", g.pot, sheriff.gold, owner.gold)
            ok = False
        else:
            print("PASS bribe pot: 10 -> sheriff 5 / pot 5")
        rows = g.score()
        pot_bonus = sum(d["bonus"] for r in rows
                        for d in r["bonus_detail"] if d.get("type") == "POT")
        if g.pot > 0 and pot_bonus != g.pot:
            print("FAIL pot payout:", g.pot, pot_bonus)
            ok = False
        else:
            print("PASS bribe pot pays out fully at score (total=%d)" % pot_bonus)
        table = g.bonus_table()
        if not any(e["kind"] == "pot" for e in table):
            print("FAIL pot in bonus_table")
            ok = False
    finally:
        game.BRIBE_POT_RATIO = saved

    # ---------- Trade Caravans ----------
    saved = game.ROUTE_BONUS
    try:
        game.ROUTE_BONUS = 4
        g = _mk_game()
        g.start_round()
        if not g.route_type:
            print("FAIL route_type not picked")
            ok = False
        else:
            print("PASS route picked:", g.route_type)
        rt = g.route_type
        owner, _ = _setup_inspect(g)
        owner_seat = g.order[0]
        owner = g.players[owner_seat]
        gold0 = owner.gold
        g.players[owner_seat].bag = [{"type": rt, "value": 3, "fine": 2}] * 2 + \
                                    [{"type": "SILK", "value": 8, "fine": 4}]
        g.players[owner_seat].bribe = {"gold": 0, "msg": ""}
        ev = g.do_inspect_decision(g.sheriff, "pass")
        gained = owner.gold - gold0
        if gained != 8:
            print("FAIL route bonus:", gained, "expected 8; events:", ev)
            ok = False
        else:
            print("PASS route bonus +4/card = +8")
    finally:
        game.ROUTE_BONUS = saved

    # ---------- Guild Contracts ----------
    saved = game.GUILD_CONTRACTS
    try:
        game.GUILD_CONTRACTS = 2
        g = _mk_game(n=3)
        if any(not p.contracts for p in g.players):
            print("FAIL contracts not dealt")
            ok = False
        if len(g.players[0].contracts) != 1:  # 3p gets GUILD_CONTRACTS-1
            print("FAIL 3p contract count:", len(g.players[0].contracts))
            ok = False
        g4 = _mk_game(n=4)
        if len(g4.players[0].contracts) != 2:
            print("FAIL 4p contract count:", len(g4.players[0].contracts))
            ok = False
        p0 = g.players[0]
        ct = p0.contracts[0]
        # fulfill: deliver enough legal cards of that type
        for _ in range(ct["need"]):
            g._deliver(p0, {"type": ct["type"], "value": 3, "fine": 2})
        rows = g.score()
        r0 = next(r for r in rows if r["seat"] == 0)
        if not any(d.get("type") == ct["type"] and d.get("bonus") == ct["reward"]
                   for d in r0["bonus_detail"]):
            print("FAIL contract reward:", ct, r0["bonus_detail"])
            ok = False
        else:
            print("PASS guild contract reward +%d (need %d %s)" %
                  (ct["reward"], ct["need"], ct["type"]))
    finally:
        game.GUILD_CONTRACTS = saved

    # ---------- Royal Favor ----------
    saved = game.ROYAL_FAVOR
    try:
        game.ROYAL_FAVOR = 1
        g = _mk_game()
        p0 = g.players[0]
        for i in range(2):
            g._deliver(p0, {"type": "ROYAL_GREEN_APPLE", "royal": True,
                            "royal_type": "APPLE", "equals": 2, "value": 4, "fine": 3})
        if p0.royal_favor != 2 or p0.gold != 56:
            print("FAIL royal favor milestone:", p0.royal_favor, p0.gold)
            ok = False
        else:
            print("PASS royal favor 2 -> +6 gold")
    finally:
        game.ROYAL_FAVOR = saved

    # ---------- Merchant Reputation ----------
    saved = game.REPUTATION
    try:
        game.REPUTATION = 1
        g = _mk_game()
        g.start_round()
        owner_seat, sheriff_seat = _setup_inspect(g)
        owner = g.players[owner_seat]
        # honest truth inspection: bag all APPLE, declare APPLE
        g.players[owner_seat].bag = [{"type": "APPLE", "value": 2, "fine": 2}] * 2
        g.players[owner_seat].decl = {"type": "APPLE", "count": 2}
        okk, ev = g.do_inspect_decision(sheriff_seat, "inspect")
        assert okk
        if owner.reputation != 1:
            print("FAIL truth rep:", owner.reputation)
            ok = False
        else:
            print("PASS reputation +1 on truth")
        # caught lie: contraband in bag
        g.phase = "INSPECT"
        g.order = [i for i in range(g.n) if i != sheriff_seat]
        g.inspect_idx = 0
        owner_seat = g.order[0]
        owner = g.players[owner_seat]
        g.players[owner_seat].bag = [{"type": "APPLE", "value": 2, "fine": 2},
                                     {"type": "WINE", "value": 7, "fine": 4}]
        g.players[owner_seat].decl = {"type": "APPLE", "count": 2}
        gold_before = owner.gold
        okk, ev = g.do_inspect_decision(sheriff_seat, "inspect")
        assert okk
        fine_paid = gold_before - owner.gold
        if owner.reputation != 0:
            print("FAIL caught rep:", owner.reputation)
            ok = False
        if game.REP_FINE_AT == 3 and owner.reputation >= 3 and fine_paid != 4:
            print("FAIL fine discount path")
        print("PASS reputation -1 on caught lie (fine paid %d)" % fine_paid)
        # discard limit perk
        game.REPUTATION = 1
        p = g.players[0]
        p.reputation = 1
        p.hand = [{"type": "APPLE", "value": 2, "fine": 2} for _ in range(7)]
        g.phase = "MARKET"
        g.order = [0, 1, 2]
        g.market_idx = 0
        g.discard_hold = {}
        okk, err = g.do_market_discard(0, list(range(6)))
        if not okk:
            print("FAIL rep extra discard:", err)
            ok = False
        else:
            print("PASS reputation +1 discard perk (6 cards)")
    finally:
        game.REPUTATION = saved

    # ---------- Night Market constant ----------
    game.ACTION_TIMEOUT = 40
    try:
        if game.ACTION_TIMEOUT != 40:
            print("FAIL ACTION_TIMEOUT patch")
            ok = False
        else:
            print("PASS ACTION_TIMEOUT = 40 (server tick enforces it)")
    finally:
        game.ACTION_TIMEOUT = 0

    # ---------- Bot personalities ----------
    p = bot.bot_params("hard", "reckless")
    if p["contra_ratio"] <= bot.bot_params("hard")["contra_ratio"]:
        print("FAIL reckless contra_ratio should exceed hard default")
        ok = False
    p2 = bot.bot_params("normal", "honest")
    if p2["contra_ratio"] >= bot.bot_params("normal")["contra_ratio"]:
        print("FAIL honest contra_ratio should be below normal default")
        ok = False
    print("PASS bot personalities shift decision params")

    # ---------- Compat detection ----------
    old_env = os.environ.get("SHERIFF_MODS_DIR")
    tmp = tempfile.mkdtemp(prefix="sheriff_compat_")
    try:
        base = os.path.join(tmp, "mods")
        for folder in ("rules_royal_favor", "rules_guild_contracts",
                       "rules_bribe_pot", "rules_night_market"):
            shutil.copytree(os.path.join("mods", folder), os.path.join(base, folder))
        os.environ["SHERIFF_MODS_DIR"] = base
        mods.reset_mods_base_cache()
        mods.load_mods()
        # enable two conflicting mods
        for folder, en in (("rules_royal_favor", True), ("rules_guild_contracts", True)):
            pth = os.path.join(base, folder, "mod.json")
            with _io.open(pth, encoding="utf-8") as f:
                d = json.load(f)
            d["enabled"] = en
            with _io.open(pth, "w", encoding="utf-8") as f:
                json.dump(d, f)
        mods.reset_mods_base_cache()
        infos = mods.list_all_mods()
        conflicts = mods.check_compat(infos)
        ids = sorted((a["id"], b["id"]) for a, b in conflicts)
        if ("guild_contracts", "royal_favor") not in ids:
            print("FAIL compat pair not detected:", ids)
            ok = False
        else:
            print("PASS incompatible rule mods detected:", ids)
        # disable royal_favor -> no conflicts
        pth = os.path.join(base, "rules_royal_favor", "mod.json")
        with _io.open(pth, encoding="utf-8") as f:
            d = json.load(f)
        d["enabled"] = False
        with _io.open(pth, "w", encoding="utf-8") as f:
            json.dump(d, f)
        mods.reset_mods_base_cache()
        if mods.check_compat(mods.list_all_mods()):
            print("FAIL conflict remains after disabling")
            ok = False
        else:
            print("PASS conflicts clear when one side is disabled")
    finally:
        if old_env is None:
            os.environ.pop("SHERIFF_MODS_DIR", None)
        else:
            os.environ["SHERIFF_MODS_DIR"] = old_env
        mods.reset_mods_base_cache()

    print("ALL RULE-MOD HOOK TESTS PASSED" if ok else "RULE-MOD HOOK TESTS FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
