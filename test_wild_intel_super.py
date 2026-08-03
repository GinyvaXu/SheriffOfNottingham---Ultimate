# -*- coding: utf-8 -*-
"""Rule mods: Wild Card, Sheriff Intel, Super Contraband, Merchant Reputation v2.

Covers the four game hooks with global-constant save/restore so the classic
deck sizes stay untouched for other tests.
"""
import random
from collections import Counter

import game
import pytest

_SAVED = {}


@pytest.fixture(autouse=True)
def _save_game_consts():
    for name in ("WILD_CARDS", "SHERIFF_INTEL", "SUPER_CONTRA", "REPUTATION"):
        _SAVED[name] = getattr(game, name)
    yield
    for name, val in _SAVED.items():
        setattr(game, name, val)


def _game(rng=3, n=3, rounds=3):
    return game.Game([game.Player("P%d" % i) for i in range(n)],
                     rng=random.Random(rng), rounds_total=rounds)


def _bag(cards):
    return [dict(c) for c in cards]


# ---------------- Wild Card ----------------

def test_wild_deck_and_declare():
    game.WILD_CARDS = 4
    deck = game.make_deck(random.Random(1), players=3)
    wilds = [c for c in deck if c.get("wild")]
    assert len(wilds) == 4
    assert all(c["type"] == "WILD" and not game.is_contraband(c) for c in wilds)
    # declaring APPLE turns the bag wild card into an apple
    g = _game()
    g.sheriff = 0
    g.order = [1, 2]
    g.phase = "DECLARE"
    g.players[1].bag = _bag([{"type": "WILD", "value": 0, "fine": 0, "wild": True},
                             {"type": "WILD", "value": 0, "fine": 0, "wild": True}])
    ok, _ = g.do_declare(1, "APPLE")
    assert ok
    apple, apple2 = g.players[1].bag
    assert apple["type"] == "APPLE" and apple["value"] == 2 and apple["fine"] == 2
    assert not apple.get("wild")
    assert apple2["type"] == "APPLE"
    # truthful pass delivers the converted card to the legal stall
    g.phase = "INSPECT"
    g.inspect_idx = 0
    g.players[1].bribe = None
    ok, events = g.do_inspect_decision(0, "inspect")
    assert ok and "TRUTH" in " ".join(events)
    assert len(g.players[1].stand_legal) == 2
    assert all(c["type"] == "APPLE" for c in g.players[1].stand_legal)


def test_wild_disabled_ignores_wild_cards():
    game.WILD_CARDS = 0
    deck = game.make_deck(random.Random(1), players=3)
    assert not any(c.get("wild") for c in deck)
    assert len(deck) == 162


# ---------------- Super Contraband ----------------

def test_super_deck():
    game.SUPER_CONTRA = 1
    deck = game.make_deck(random.Random(1), players=3)
    supers = [c for c in deck if c.get("super")]
    assert len(supers) == len(game.CONTRABAND)
    for c in supers:
        base = c["of"]
        assert c["type"] == "SUPER_" + base
        assert c["value"] == game.GOODS[base]["value"] * 3
        assert c["fine"] == game.GOODS[base]["fine"] * 3
        assert game.is_contraband(c)


def test_super_caught_triple_fine():
    game.SUPER_CONTRA = 1
    g = _game()
    g.sheriff = 0
    g.order = [1, 2]
    g.phase = "INSPECT"
    g.inspect_idx = 0
    g.players[1].bag = _bag([{"type": "SUPER_COFFEE", "value": 18, "fine": 12,
                              "super": True, "of": "COFFEE"}])
    g.players[1].decl = {"type": "APPLE", "count": 1}
    g.players[1].bribe = None
    before = g.players[1].gold
    ok, events = g.do_inspect_decision(0, "inspect")
    assert ok
    assert g.players[1].gold == before - 12
    assert g.players[1].stand_contra == []
    assert "12 gold fine" in " ".join(events)
    # scoring counts the super card under its base type at face value
    g._deliver(g.players[1], {"type": "SUPER_COFFEE", "value": 18, "fine": 12,
                              "super": True, "of": "COFFEE"})
    rows = g._base_rows()
    row = rows[1]
    assert row["contra"]["COFFEE"] == 1
    assert row["value"] == g.players[1].gold + 18


# ---------------- Sheriff Intel ----------------

def test_intel_basic():
    game.SHERIFF_INTEL = 1
    g = _game()
    g.sheriff = 0
    g.order = [1, 2]
    g.phase = "INSPECT"
    g.inspect_idx = 0
    g.players[1].bag = _bag([{"type": "APPLE", "value": 2, "fine": 2},
                             {"type": "COFFEE", "value": 6, "fine": 4}])
    g.players[1].bag_loaded = True
    g.players[2].bag = _bag([{"type": "WINE", "value": 7, "fine": 4}])
    g.players[2].bag_loaded = True
    ok, res = g.do_sheriff_intel(0)
    assert ok
    assert res["cost"] == 3
    assert res["lo"] == 0 and res["hi"] == 2   # 2 contraband -> bucket 0-2
    assert g.players[0].gold == 47
    # once per round only
    ok2, _ = g.do_sheriff_intel(0)
    assert not ok2
    # need 2+ merchants left
    g.intel_used = False
    g.inspect_idx = 1
    ok3, err = g.do_sheriff_intel(0)
    assert not ok3 and "2 merchants" in err


def test_intel_off():
    game.SHERIFF_INTEL = 0
    g = _game()
    g.phase = "INSPECT"
    g.order = [1, 2]
    ok, err = g.do_sheriff_intel(0)
    assert not ok and "disabled" in err


# ---------------- Merchant Reputation v2 ----------------

def test_reputation_legal_mismatch_no_loss():
    game.REPUTATION = 1
    g = _game()
    g.sheriff = 0
    g.order = [1, 2]
    g.phase = "INSPECT"
    g.inspect_idx = 0
    g.players[1].bag = _bag([{"type": "CHICKEN", "value": 4, "fine": 2}])
    g.players[1].decl = {"type": "APPLE", "count": 1}
    g.players[1].bribe = None
    g.players[1].reputation = 0
    ok, events = g.do_inspect_decision(0, "inspect")
    assert ok and g.players[1].reputation == 0
    assert "no fine" in " ".join(events)


def test_reputation_contraband_still_costs():
    game.REPUTATION = 1
    g = _game()
    g.sheriff = 0
    g.order = [1, 2]
    g.phase = "INSPECT"
    g.inspect_idx = 0
    g.players[1].bag = _bag([{"type": "COFFEE", "value": 6, "fine": 4}])
    g.players[1].decl = {"type": "APPLE", "count": 1}
    g.players[1].bribe = None
    g.players[1].reputation = 3
    ok, events = g.do_inspect_decision(0, "inspect")
    assert ok and g.players[1].reputation == 2


def test_reputation_draw_bias():
    game.REPUTATION = 1
    g = _game()
    g.players[0].reputation = 5
    g.players[1].reputation = -5
    g.players[2].reputation = 0
    stats = {0: [0, 0], 1: [0, 0], 2: [0, 0]}  # [legal, contraband]
    for _ in range(900):
        for seat in (0, 1, 2):
            if not g.deck:
                g.deck = game.make_deck(random.Random(9), players=3)
            c = g._draw_card(g.players[seat])
            stats[seat][0 if not game.is_contraband(c) else 1] += 1
    base = stats[2][0] / sum(stats[2])
    hi = stats[0][0] / sum(stats[0])
    low = stats[1][0] / sum(stats[1])
    assert hi > 0.85, hi            # rep +5 draws mostly legal (~90%)
    assert low < base - 0.10, (low, base)  # rep -5 draws notably more contraband
    assert low > 0.30, low          # ... but not the 90% mirror (room to recover)
