# -*- coding: utf-8 -*-
"""Twists of Fate Event Pack rule mod tests (all 10 events)."""
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


def _game(rng=3, n=3, rounds=9):
    return game.Game([game.Player("P%d" % i) for i in range(n)],
                     rng=random.Random(rng), rounds_total=rounds)


def _bag(cards):
    return [dict(c) for c in cards]


def _with_event(eid, n=3, rounds=9):
    """A game in round 1 whose current event is forced to ``eid``."""
    g = _game(n=n, rounds=rounds)
    g.start_round()
    g.current_event = eid
    g.plague_type = "APPLE" if eid == "PLAGUE" else None
    return g


def _enter_inspect(g, merchant=1, sheriff=0):
    g.phase = "INSPECT"
    g.order = [1, 2]
    g.inspect_idx = 0
    g.sheriff = sheriff
    g.players[merchant].decl = {"type": "APPLE", "count": len(g.players[merchant].bag)}
    g.players[merchant].bribe = {"gold": 0, "msg": ""}


# ---------------- deck & round flow ----------------

def test_event_random_each_round_never_runs_out():
    game.EVENT_PACK = 1
    g = _game(rounds=20)  # more rounds than events in the pool
    assert not g.event_deck  # events are no longer pre-drawn
    seen = set()
    for _ in range(15):
        g.start_round()
        assert g.current_event in game.EVENT_IDS  # every round has an event
        seen.add(g.current_event)
    assert g.current_event is not None  # events never run out
    assert len(seen) >= 5  # random spread over the pool


def test_events_off_by_default():
    game.EVENT_PACK = 0
    g = _game()
    assert not g.event_deck
    g.start_round()
    assert g.current_event is None
    assert g._bag_max() == game.BAG_MAX


def test_plague_picks_available_legal():
    game.EVENT_PACK = 1
    g = _game(rounds=20)
    g.start_round()
    g.current_event = "PLAGUE"
    g.plague_type = None
    g._next_round = None
    # re-run the plague pick through start_round semantics is internal;
    # simply verify the helper path assigns a legal type
    g.start_round()
    if g.current_event == "PLAGUE":
        assert g.plague_type in game.LEGAL


# ---------------- Bountiful Harvest ----------------

def test_bountiful_extra_draw():
    game.EVENT_PACK = 1
    g = _with_event("BOUNTIFUL")
    p = g.players[1]
    p.hand = [{"type": "APPLE", "value": 2, "fine": 2} for _ in range(5)]
    ok, _ = g.do_market_discard(1, [0, 1])
    assert ok and g.draw_allow[1] == 3  # 2 discarded + 1 bounty
    # discarding nothing still grants 1 free draw
    g2 = _with_event("BOUNTIFUL")
    ok2, _ = g2.do_market_discard(1, [])
    assert ok2
    assert g2.draw_allow[1] == 1
    assert g2.phase == "MARKET"


def test_bountiful_draw_seventh_card():
    game.EVENT_PACK = 1
    g = _with_event("BOUNTIFUL")
    g.phase = "MARKET"
    p = g.players[1]
    p.hand = [{"type": "APPLE", "value": 2, "fine": 2} for _ in range(6)]
    # discarding 0 cards still grants 1 free draw, and the hand cap is 7
    ok, _ = g.do_market_discard(1, [])
    assert ok and g.draw_allow[1] == 1
    g.deck = [{"type": "CHICKEN", "value": 4, "fine": 2} for _ in range(20)]
    ok2, _ = g.do_market_draw(1, "deck")
    assert ok2 and len(p.hand) == 7


# ---------------- Black market auto submit ----------------

def test_black_market_auto_submit_on_delivery():
    game.EVENT_PACK = 0
    game.SUPER_CONTRA = 0
    game.REPUTATION = 0
    game.ROUTE_BONUS = 0
    g = _game(rounds=1)
    g.quest_types = ("COFFEE",)
    g.quest_rewards = {"COFFEE": [30, 25]}
    g.quest_claimed = {"COFFEE": 0}
    g.quest_claimers = {"COFFEE": [None, None]}
    p = g.players[1]
    gold0 = p.gold
    events = []
    for _ in range(3):
        events.extend(g._deliver(p, {"type": "COFFEE", "value": 6, "fine": 4}))
    assert p.stand_contra == []
    assert p.gold == gold0 + 30
    assert g.quest_claimed["COFFEE"] == 1
    assert any("auto-completes" in e for e in events)


def test_black_market_auto_submit_needs_three():
    game.EVENT_PACK = 0
    game.SUPER_CONTRA = 0
    game.REPUTATION = 0
    game.ROUTE_BONUS = 0
    g = _game(rounds=1)
    g.quest_types = ("COFFEE",)
    g.quest_rewards = {"COFFEE": [30, 25]}
    g.quest_claimed = {"COFFEE": 0}
    p = g.players[1]
    gold0 = p.gold
    for _ in range(2):
        g._deliver(p, {"type": "COFFEE", "value": 6, "fine": 4})
    assert len(p.stand_contra) == 2
    assert p.gold == gold0  # not claimed yet
    assert g.quest_claimed["COFFEE"] == 0


# ---------------- Famine ----------------

def test_famine_bag_max():
    game.EVENT_PACK = 1
    g = _with_event("FAMINE")
    assert g._bag_max() == 4
    g.phase = "LOAD"
    p = g.players[1]
    p.hand = [{"type": "APPLE", "value": 2, "fine": 2} for _ in range(6)]
    ok, _ = g.do_load(1, [0, 1, 2, 3, 4])
    assert not ok
    ok, msg = g.do_load(1, [0, 1, 2, 3])
    assert ok and "4" in msg


# ---------------- Plague ----------------

def test_plague_bans_type():
    game.EVENT_PACK = 1
    g = _with_event("PLAGUE")
    assert g.plague_type == "APPLE"
    g.phase = "LOAD"
    p = g.players[1]
    p.hand = [{"type": "APPLE", "value": 2, "fine": 2},
              {"type": "CHICKEN", "value": 4, "fine": 2}]
    ok, err = g.do_load(1, [0])
    assert not ok and "banned" in err
    ok, _ = g.do_load(1, [1])
    assert ok


# ---------------- Market Day ----------------

def test_market_day_truth_bonus():
    game.EVENT_PACK = 1
    g = _with_event("MARKET_DAY")
    _enter_inspect(g)
    g.players[1].bag = _bag([{"type": "APPLE", "value": 2, "fine": 2} for _ in range(2)])
    g.players[1].decl = {"type": "APPLE", "count": 2}
    before_s = g.players[0].gold
    before_m = g.players[1].gold
    ok, events = g.do_inspect_decision(0, "inspect")
    assert ok
    assert g.players[1].gold == before_m + 6  # 2*2 + 2*1 bonus
    assert g.players[0].gold == before_s - 6
    assert any("Market Day" in e for e in events)


# ---------------- Tax ----------------

def test_tax_on_load():
    game.EVENT_PACK = 1
    g = _with_event("TAX")
    g.phase = "LOAD"
    p = g.players[1]
    p.gold = 10
    p.hand = [{"type": "APPLE", "value": 2, "fine": 2}]
    ok, msg = g.do_load(1, [0])
    assert ok and "tax" in msg
    assert p.gold == 9


# ---------------- Inspector Visit ----------------

def test_inspector_blocks_full_pass():
    game.EVENT_PACK = 1
    g = _with_event("INSPECTOR")
    _enter_inspect(g)
    g.players[1].bag = _bag([{"type": "APPLE", "value": 2, "fine": 2}])
    g.players[2].bag = _bag([{"type": "APPLE", "value": 2, "fine": 2}])
    g.players[2].decl = {"type": "APPLE", "count": 1}
    g.players[1].bribe = {"gold": 0, "msg": ""}
    g.players[2].bribe = {"gold": 0, "msg": ""}
    ok, _ = g.do_inspect_decision(0, "pass")  # first merchant may pass
    assert ok
    g.players[2].bribe = {"gold": 0, "msg": ""}
    ok, err = g.do_inspect_decision(0, "pass")  # last merchant: refused
    assert not ok and "inspect at least one" in err[0]
    ok, _ = g.do_inspect_decision(0, "inspect")
    assert ok


def test_plague_bans_wild_cards():
    game.EVENT_PACK = 1
    game.WILD_CARDS = 2
    g = _with_event("PLAGUE")
    g.phase = "LOAD"
    seat = next(i for i in range(3) if i != g.sheriff)
    p = g.players[seat]
    p.hand = [{"type": "WILD", "value": 0, "fine": 0, "wild": True},
              {"type": "BREAD", "value": 3, "fine": 2}]
    ok, err = g.do_load(seat, [0])
    assert not ok and "wild cards" in err
    ok, _ = g.do_load(seat, [1])
    assert ok


def test_plague_allows_other_legals():
    game.EVENT_PACK = 1
    g = _with_event("PLAGUE")
    g.plague_type = "APPLE"
    g.phase = "LOAD"
    seat = next(i for i in range(3) if i != g.sheriff)
    p = g.players[seat]
    p.hand = [{"type": "BREAD", "value": 3, "fine": 2}]
    ok, _ = g.do_load(seat, [0])
    assert ok


# ---------------- Lockdown ----------------

def test_lockdown_double_fine():
    game.EVENT_PACK = 1
    g = _with_event("LOCKDOWN")
    _enter_inspect(g)
    g.players[1].bag = _bag([{"type": "COFFEE", "value": 6, "fine": 4}])
    g.players[1].decl = {"type": "APPLE", "count": 1}
    before = g.players[1].gold
    ok, events = g.do_inspect_decision(0, "inspect")
    assert ok
    assert g.players[1].gold == before - 8  # 4 x2
    assert any("doubled" in e for e in events)


def test_lockdown_super_contraband_also_doubled():
    game.EVENT_PACK = 1
    game.SUPER_CONTRA = 1
    g = _with_event("LOCKDOWN")
    _enter_inspect(g)
    g.players[1].bag = _bag([{"type": "SUPER_COFFEE", "value": 18, "fine": 12,
                              "super": True, "of": "COFFEE"}])
    g.players[1].decl = {"type": "APPLE", "count": 1}
    before = g.players[1].gold
    ok, _ = g.do_inspect_decision(0, "inspect")
    assert ok
    assert g.players[1].gold == before - 24  # 12 x2


# ---------------- Amnesty ----------------

def test_amnesty_no_fine():
    game.EVENT_PACK = 1
    g = _with_event("AMNESTY")
    _enter_inspect(g)
    g.players[1].bag = _bag([{"type": "COFFEE", "value": 6, "fine": 4}])
    g.players[1].decl = {"type": "APPLE", "count": 1}
    before = g.players[1].gold
    ok, events = g.do_inspect_decision(0, "inspect")
    assert ok
    assert g.players[1].gold == before  # no fine
    assert any("without a fine" in e for e in events)
    assert g.players[1].stand_contra == []  # seized, not delivered


# ---------------- Black Market Boom ----------------

def test_black_boom_adds_value_on_pass():
    game.EVENT_PACK = 1
    g = _with_event("BLACK_BOOM")
    _enter_inspect(g)
    g.players[1].bag = _bag([{"type": "COFFEE", "value": 6, "fine": 4}])
    g.players[1].decl = {"type": "APPLE", "count": 1}
    ok, _ = g.do_inspect_decision(0, "pass")
    assert ok
    assert g.players[1].stand_contra[0]["value"] == 7
    rows = g._base_rows()
    assert rows[1]["value"] == g.players[1].gold + 7


# ---------------- Rumors ----------------

def test_rumors_peek_once():
    game.EVENT_PACK = 1
    g = _with_event("RUMORS")
    _enter_inspect(g)
    g.players[1].bag = _bag([{"type": "COFFEE", "value": 6, "fine": 4},
                             {"type": "APPLE", "value": 2, "fine": 2}])
    ok, res = g.do_sheriff_rumor(0)
    assert ok and res["target"] == 1 and res["type"] in ("COFFEE", "APPLE")
    ok2, err2 = g.do_sheriff_rumor(0)
    assert not ok2 and "already used" in err2
    ok3, _ = g.do_sheriff_rumor(1)
    assert not ok3


def test_rumors_off():
    game.EVENT_PACK = 0
    g = _game()
    g.start_round()
    ok, err = g.do_sheriff_rumor(0)
    assert not ok and "not active" in err
