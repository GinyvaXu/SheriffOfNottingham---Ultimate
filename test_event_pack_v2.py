# -*- coding: utf-8 -*-
"""v1.6.8: 10 new event-pack events + 6-player mode."""
import random

import game
import pytest

_SAVED = {}


@pytest.fixture(autouse=True)
def _save_consts():
    for name in ("EVENT_PACK", "WILD_CARDS", "SUPER_CONTRA", "REPUTATION", "ROUTE_BONUS"):
        _SAVED[name] = getattr(game, name)
    yield
    for name, val in _SAVED.items():
        setattr(game, name, val)


def _game(rng=7, n=3, rounds=9):
    return game.Game([game.Player("P%d" % i) for i in range(n)],
                     rng=random.Random(rng), rounds_total=rounds)


def _bag(cards):
    return [dict(c) for c in cards]


def _with_event(eid, n=3, rounds=9):
    g = _game(n=n, rounds=rounds)
    g.start_round()
    g.current_event = eid
    return g


def _enter_lie_inspect(g, merchant=1, sheriff=0, bag=None, decl="APPLE"):
    g.phase = "INSPECT"
    g.order = [1, 2]
    g.inspect_idx = 0
    g.sheriff = sheriff
    g.players[merchant].bag = bag or []
    g.players[merchant].decl = {"type": decl, "count": len(g.players[merchant].bag)}
    g.players[merchant].bribe = {"gold": 0, "msg": ""}


# ---------------- no immediate repeat ----------------

def test_no_same_event_twice_in_a_row():
    game.EVENT_PACK = 1
    g = _game(rounds=30)
    g.start_round()
    prev = g.current_event
    for _ in range(20):
        g.start_round()
        assert g.current_event != prev, "same event twice in a row"
        prev = g.current_event


# ---------------- Apple Blight ----------------

def test_apple_blight_bans_apples_and_wild():
    game.EVENT_PACK = 1
    game.WILD_CARDS = 3
    g = _with_event("APPLE_BLIGHT")
    g.phase = "LOAD"
    g.sheriff = 0
    p = g.players[1]
    p.hand = [{"type": "APPLE", "value": 2, "fine": 2},
              {"type": "CHICKEN", "value": 4, "fine": 2},
              {"type": "WILD", "value": 0, "fine": 0, "wild": True}]
    ok, err = g.do_load(1, [0])
    assert not ok and "Apple Blight" in err
    ok, err = g.do_load(1, [2])
    assert not ok  # wild cards are banned too
    ok, _ = g.do_load(1, [1])
    assert ok


# ---------------- Cheese Festival ----------------

def test_cheese_festival_value_and_note():
    game.EVENT_PACK = 1
    g = _with_event("CHEESE_FEST")
    p = g.players[1]
    ev = []
    c1 = {"type": "CHEESE", "value": 3, "fine": 2}
    c2 = {"type": "CHEESE", "value": 3, "fine": 2}
    ev.extend(g._deliver(p, c1))
    ev.extend(g._deliver(p, c2))
    assert c1["value"] == 4 and c2["value"] == 4
    assert sum("Cheese Festival" in e for e in ev) == 1  # noted once


# ---------------- Zero Tolerance ----------------

def test_zero_tolerance_extra_fine():
    game.EVENT_PACK = 1
    g = _with_event("ZERO_TOLERANCE")
    _enter_lie_inspect(g, bag=_bag([
        {"type": "APPLE", "value": 2, "fine": 2},
        {"type": "COFFEE", "value": 6, "fine": 4},
    ]))
    s0 = g.players[0].gold
    m0 = g.players[1].gold
    ok, events = g.do_inspect_decision(0, "inspect")
    assert ok
    assert g.players[0].gold == s0 + 7  # 4 fine + 3 zero tolerance
    assert g.players[1].gold == m0 - 7
    assert any("Zero Tolerance" in e for e in events)


# ---------------- Double Compensation ----------------

def test_double_comp_truth_penalty():
    game.EVENT_PACK = 1
    g = _with_event("DOUBLE_COMP")
    _enter_lie_inspect(g, bag=_bag([
        {"type": "APPLE", "value": 2, "fine": 2},
        {"type": "APPLE", "value": 2, "fine": 2},
    ]), decl="APPLE")
    s0 = g.players[0].gold
    m0 = g.players[1].gold
    ok, events = g.do_inspect_decision(0, "inspect")
    assert ok
    assert g.players[1].gold == m0 + 8  # (2+2) * 2
    assert g.players[0].gold == s0 - 8
    assert any("Double Compensation" in e for e in events)


# ---------------- Shortage ----------------

def test_shortage_discard_limit():
    game.EVENT_PACK = 1
    g = _with_event("SHORTAGE")
    g.phase = "MARKET"
    p = g.players[1]
    p.hand = [{"type": "APPLE", "value": 2, "fine": 2} for _ in range(6)]
    ok, err = g.do_market_discard(1, [0, 1, 2, 3, 4])
    assert not ok and "at most 4" in err
    ok, _ = g.do_market_discard(1, [0, 1, 2, 3])
    assert ok


# ---------------- Parade Day ----------------

def test_parade_day_end_of_round():
    game.EVENT_PACK = 1
    g = _with_event("PARADE_DAY")
    p1, p2 = g.players[1], g.players[2]
    g._deliver(p1, {"type": "COFFEE", "value": 6, "fine": 4})
    g._deliver(p2, {"type": "APPLE", "value": 2, "fine": 2})
    g0, g1, g2 = p1.gold, p2.gold, g.players[0].gold
    ev = []
    g.end_round(ev)
    assert p1.gold == g0 + 3
    assert p2.gold == g1  # legal delivery does not count
    assert g.players[0].gold == g2
    assert any("Parade Day" in e for e in ev)


# ---------------- Bounty Board ----------------

def test_bounty_board_first_smuggler_only():
    game.EVENT_PACK = 1
    g = _with_event("BOUNTY_BOARD")
    p1, p2 = g.players[1], g.players[2]
    g0 = p1.gold
    ev = []
    ev.extend(g._deliver(p1, {"type": "COFFEE", "value": 6, "fine": 4}))
    ev.extend(g._deliver(p1, {"type": "COFFEE", "value": 6, "fine": 4}))
    assert p1.gold == g0 + 5  # only once
    assert sum("Bounty Board" in e for e in ev) == 1
    # a different merchant cannot claim it anymore this round
    ev2 = []
    ev2.extend(g._deliver(p2, {"type": "SILK", "value": 8, "fine": 4}))
    assert p2.gold == 50  # no bounty
    assert not any("Bounty Board" in e for e in ev2)


# ---------------- Sheriff Payday ----------------

def test_sheriff_payday_gold_per_seized():
    game.EVENT_PACK = 1
    g = _with_event("SHERIFF_PAYDAY")
    _enter_lie_inspect(g, bag=_bag([
        {"type": "APPLE", "value": 2, "fine": 2},
        {"type": "COFFEE", "value": 6, "fine": 4},
        {"type": "SILK", "value": 8, "fine": 4},
    ]))
    s0 = g.players[0].gold
    ok, events = g.do_inspect_decision(0, "inspect")
    assert ok
    # fine 8 goes to sheriff + payday 3*2
    assert g.players[0].gold == s0 + 8 + 6
    assert any("Sheriff Payday" in e for e in events)


# ---------------- Rumors Pro ----------------

def test_rumor_pro_peeks_each_merchant_once():
    game.EVENT_PACK = 1
    g = _with_event("RUMOR_PRO")
    g.phase = "INSPECT"
    g.order = [1, 2]
    g.inspect_idx = 0
    g.sheriff = 0
    g.players[1].bag = _bag([{"type": "COFFEE", "value": 6, "fine": 4}])
    g.players[2].bag = _bag([{"type": "SILK", "value": 8, "fine": 4}])
    ok, res = g.do_sheriff_rumor(0, 1)
    assert ok and res["type"] == "COFFEE"
    ok, res = g.do_sheriff_rumor(0, 2)
    assert ok and res["type"] == "SILK"
    ok, _ = g.do_sheriff_rumor(0, 1)
    assert not ok  # already peeked this merchant
    # base Rumors is still once per round total
    g2 = _with_event("RUMORS")
    g2.phase = "INSPECT"
    g2.order = [1, 2]
    g2.inspect_idx = 0
    g2.sheriff = 0
    g2.players[1].bag = _bag([{"type": "COFFEE", "value": 6, "fine": 4}])
    g2.players[2].bag = _bag([{"type": "SILK", "value": 8, "fine": 4}])
    ok, _ = g2.do_sheriff_rumor(0, 1)
    assert ok
    ok, _ = g2.do_sheriff_rumor(0, 2)
    assert not ok


# ---------------- Royal Treasury ----------------

def test_treasury_doubles_bribe_cap():
    game.EVENT_PACK = 1
    g = _with_event("TREASURY")
    g.phase = "INSPECT"
    g.order = [1, 2]
    g.inspect_idx = 0
    g.sheriff = 0
    p = g.players[1]
    p.gold = 10
    ok, _ = g.do_bribe(1, 25)
    assert ok and p.bribe["gold"] == 20  # capped at 2x gold
    # without the event the cap is the player's gold
    g2 = _with_event("PLAGUE")
    g2.phase = "INSPECT"
    g2.order = [1, 2]
    g2.inspect_idx = 0
    g2.sheriff = 0
    p2 = g2.players[1]
    p2.gold = 10
    ok, _ = g2.do_bribe(1, 25)
    assert ok and p2.bribe["gold"] == 10


# ---------------- 6-player mode ----------------

def test_six_player_game_runs_and_card_counts():
    g = _game(n=6, rounds=12)
    assert g.n == 6
    assert g.rounds_total == 12  # 6 players x 2 sheriff rounds
    # 4-6 players share the cnt6 deck sizes (user-defined house numbers)
    deck6 = game.make_deck(random.Random(1), royal=True, players=6)
    counts = {}
    for c in deck6:
        counts[c["type"]] = counts.get(c["type"], 0) + 1
    assert counts["COFFEE"] == game.GOODS["COFFEE"]["cnt6"]
    assert counts["APPLE"] == game.GOODS["APPLE"]["cnt6"]
    g.start_round()
    assert g.phase == "MARKET"
    # a full round can run to completion with all merchants acting
    g.phase = "LOAD"
    for si in g.order:
        p = g.players[si]
        p.hand = [{"type": "APPLE", "value": 2, "fine": 2} for _ in range(6)]
        ok, _ = g.do_load(si, [0])
        assert ok
    g.phase = "DECLARE"
    for si in g.order:
        ok, _ = g.do_declare(si, "APPLE")
        assert ok
    assert g.phase == "INSPECT"
