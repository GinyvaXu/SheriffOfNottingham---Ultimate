# -*- coding: utf-8 -*-
"""Bribe bargaining: sheriff counter-offers and merchant responses."""

import game
import bot


def _mk_inspect(gold=50, offer=3):
    ps = [game.Player("A"), game.Player("B"), game.Player("C")]
    g = game.Game(ps, rng=game.random.Random(7), royal=False, black_market=False,
                  rounds_total=1)
    g.start_round()
    g.phase = "INSPECT"
    g.order = [i for i in range(3) if i != g.sheriff]
    g.inspect_idx = 0
    owner = g.order[0]
    sh = g.sheriff
    g.players[owner].bag = [{"type": "APPLE", "value": 2, "fine": 2}]
    g.players[owner].decl = {"type": "APPLE", "count": 1}
    g.players[owner].gold = gold
    if offer is not None:
        ok, _ = g.do_bribe(owner, offer)
        assert ok
    return g, owner, sh


def test_initial_offer_and_duplicate_rejected():
    g, owner, sh = _mk_inspect()
    ok, msg = g.do_bribe(owner, 5)
    assert not ok and "already offered" in msg
    ok, _ = g.do_bribe(owner, 0)
    assert not ok  # duplicate still rejected
    assert g.players[owner].bribe == {"gold": 3, "msg": ""}


def test_sheriff_counter_then_merchant_accept():
    g, owner, sh = _mk_inspect(offer=3)
    ok, ev = g.do_counter_bribe(sh, 8)
    assert ok and ev == ["B demands 8 gold from A"]
    assert g.players[owner].sheriff_demand == 8
    assert g.players[owner].bribe_round == 1
    gold_sh = g.players[sh].gold
    ok, ev = g.do_respond_counter(owner, "accept")
    assert ok
    assert any("A accepts the counter-offer of 8 gold" in e for e in ev)
    assert any("A bribes the Sheriff 8 gold" in e for e in ev)
    assert g.players[sh].gold - gold_sh == 8
    assert g.players[owner].bribe is None
    assert g.inspect_idx == 1  # moved to the next merchant


def test_sheriff_cannot_counter_without_offer_or_too_low():
    g, owner, sh = _mk_inspect(offer=0)
    ok, ev = g.do_counter_bribe(sh, 5)
    assert not ok and "offered no bribe" in ev[0]

    g, owner, sh = _mk_inspect(offer=3)
    ok, ev = g.do_counter_bribe(sh, 3)  # must be strictly more
    assert not ok and "more than the current offer" in ev[0]
    ok, ev = g.do_counter_bribe(sh, 99)  # cannot exceed merchant gold
    assert not ok and "only has" in ev[0]


def test_merchant_counter_raises_offer_then_sheriff_passes():
    g, owner, sh = _mk_inspect(offer=3)
    # validation only applies while a demand is pending
    g.do_counter_bribe(sh, 8)
    ok, ev = g.do_respond_counter(owner, "counter", 3)   # must exceed own offer
    assert not ok and "more than your current offer" in ev[0]
    ok, ev = g.do_respond_counter(owner, "counter", 8)   # must be below demand
    assert not ok and "less than the Sheriff" in ev[0]
    # a valid counter raises the offer and clears the demand
    ok, ev = g.do_respond_counter(owner, "counter", 7)
    assert ok and ev == ["A counters with 7 gold"]
    assert g.players[owner].bribe["gold"] == 7
    assert g.players[owner].sheriff_demand is None
    # the sheriff accepts the raised offer by passing
    gold_sh = g.players[sh].gold
    ok, ev = g.do_inspect_decision(sh, "pass")
    assert ok
    assert g.players[sh].gold - gold_sh == 7
    assert any("A bribes the Sheriff 7 gold" in e for e in ev)


def test_merchant_reject_returns_ball_to_sheriff():
    g, owner, sh = _mk_inspect(offer=3)
    g.do_counter_bribe(sh, 12)
    ok, ev = g.do_respond_counter(owner, "reject")
    assert ok and ev == ["A rejects the counter-offer"]
    assert g.players[owner].bribe["gold"] == 0
    assert g.players[owner].sheriff_demand is None
    gold_sh = g.players[sh].gold
    ok, ev = g.do_inspect_decision(sh, "pass")
    assert ok
    assert g.players[sh].gold == gold_sh          # no bribe was paid
    assert any("A passes unchecked" in e for e in ev)


def test_counter_round_cap():
    g, owner, sh = _mk_inspect(offer=1)
    assert g.do_counter_bribe(sh, 5)[0]
    assert g.do_respond_counter(owner, "counter", 4)[0]
    assert g.do_counter_bribe(sh, 6)[0]
    assert g.players[owner].bribe_round == game.BRIBE_MAX_ROUNDS
    ok, ev = g.do_respond_counter(owner, "counter", 5)
    assert not ok and "No more counter-offers" in ev[0]
    ok, ev = g.do_respond_counter(owner, "accept")
    assert ok


def test_guard_phase_and_actor():
    g, owner, sh = _mk_inspect(offer=3)
    other = g.order[1]
    ok, _ = g.do_bribe(other, 2)
    assert not ok
    ok, ev = g.do_counter_bribe(owner, 5)
    assert not ok  # only the sheriff may counter
    ok, ev = g.do_respond_counter(sh, "accept")
    assert not ok  # only the merchant may respond
    ok, ev = g.do_inspect_decision(owner, "pass")
    assert not ok  # only the sheriff decides
    # stale inspect while a demand is pending is rejected
    g.do_counter_bribe(sh, 6)
    ok, ev = g.do_inspect_decision(sh, "pass")
    assert not ok and "must respond to the counter-offer" in ev[0]


def test_bot_choose_inspect_returns_tuple():
    g, owner, sh = _mk_inspect(offer=3)
    for lvl in ("easy", "normal", "hard"):
        action, gold = bot.choose_inspect(g, sh, lvl)
        assert action in ("pass", "inspect", "counter")
        if action == "counter":
            assert gold is not None and gold > 3


def test_bot_choose_respond_rules():
    g, owner, sh = _mk_inspect(offer=3)
    g.players[owner].bag = [{"type": "SILK", "value": 8, "fine": 4}]
    g.do_counter_bribe(sh, 6)
    action, gold = bot.choose_respond(g, owner, "normal")
    assert action in ("accept", "reject", "counter")
    if action == "counter":
        assert 3 < gold < 6
    # demand far above the bag value -> a hard bot rejects
    g2, o2, sh2 = _mk_inspect(offer=1)
    g2.players[o2].bag = [{"type": "APPLE", "value": 2, "fine": 2}]
    assert g2.do_counter_bribe(sh2, 9)[0]
    assert all(bot.choose_respond(g2, o2, "hard")[0] == "reject" for _ in range(50))
    # an easy bot accepts the same demand (simple-minded)
    assert bot.choose_respond(g2, o2, "easy")[0] in ("accept", "counter")
