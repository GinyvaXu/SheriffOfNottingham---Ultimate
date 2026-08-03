# -*- coding: utf-8 -*-
"""Deterministic checks for royal goods cards + black market quests (new house rules)."""

import game


def test_deck():
    rng = game.random.Random(1)
    deck3 = game.make_deck(rng, players=3)
    assert len(deck3) == 162, len(deck3)
    royal3 = [c for c in deck3 if c.get("royal")]
    assert len(royal3) == 6, len(royal3)
    from collections import Counter
    c3 = Counter(c["type"] for c in deck3)
    assert c3["APPLE"] == 48 and c3["CHICKEN"] == 24 and c3["CHEESE"] == 36
    assert c3["BREAD"] == 0
    assert c3["SILK"] == 9 and c3["CROSSBOW"] == 5 and c3["COFFEE"] == 18 and c3["WINE"] == 16
    assert c3["ROYAL_GREEN_APPLE"] == 2 and c3["ROYAL_GOLD_APPLE"] == 1
    assert c3["ROYAL_GOUDA_CHEESE"] == 2 and c3["ROYAL_BLUE_CHEESE"] == 0
    assert c3["ROYAL_RYE_BREAD"] == 0 and c3["ROYAL_COARSE_BREAD"] == 0
    assert c3["ROYAL_CHICKEN"] == 1
    # every card carries its fixed value and per-card fine
    assert all(c["value"] == game.GOODS[c["type"]]["value"] for c in deck3 if not c.get("royal"))
    assert all(c["fine"] == game.GOODS[c["type"]]["fine"] for c in deck3 if not c.get("royal"))
    royal_card = next(c for c in royal3 if c["type"] == "ROYAL_GOLD_APPLE")
    assert royal_card["equals"] == 3 and royal_card["royal_type"] == "APPLE" and royal_card["fine"] == 4

    deck6 = game.make_deck(rng, players=6)
    assert len(deck6) == 216, len(deck6)
    c6 = Counter(c["type"] for c in deck6)
    assert c6["BREAD"] == 36 and c6["SILK"] == 12 and c6["COFFEE"] == 22 and c6["WINE"] == 21
    assert c6["ROYAL_BLUE_CHEESE"] == 1 and c6["ROYAL_RYE_BREAD"] == 2
    assert c6["ROYAL_COARSE_BREAD"] == 1 and c6["ROYAL_CHICKEN"] == 2
    assert len([c for c in deck6 if c.get("royal")]) == 12

    plain = game.make_deck(rng, royal=False, players=3)
    assert len(plain) == 156, len(plain)
    assert not any(c.get("royal") for c in plain)
    print("PASS deck (house numbers: 3p=162/6p=216, royal 6/12)")


def test_quest_auto_submit():
    """Black market: 3 random types x 2 slots, rewards 30-35 / 25-30 shown in
    advance, quests auto-claim on delivery (manual submit button is a backup)."""
    ps = [game.Player("A"), game.Player("B")]
    g = game.Game(ps, rng=game.random.Random(2))
    g.start_round()
    assert g.black_market and len(g.quest_types) == 3
    for t_ in g.quest_types:
        rw = g.quest_rewards[t_]
        assert 30 <= rw[0] <= 35 and 25 <= rw[1] <= 30 and rw[1] < rw[0], (t_, rw)
    t = g.quest_types[0]
    # not enough cards -> no claim yet
    events = []
    for _ in range(2):
        events.extend(g._deliver(ps[0], {"type": t, "value": 8, "fine": 4}))
    assert len(ps[0].stand_contra) == 2
    assert ps[0].gold == 50
    # third card auto-claims slot 0 immediately (works in the final round too)
    events.extend(g._deliver(ps[0], {"type": t, "value": 8, "fine": 4}))
    assert any("auto-completes" in e for e in events)
    assert ps[0].gold == 50 + g.quest_rewards[t][0]
    assert ps[0].black_market_cards == 1
    assert g.quest_claimed[t] == 1 and g.quest_claimers[t][0] == "A"
    assert len(ps[0].stand_contra) == 0
    assert sum(1 for c in g.d1 if c["type"] == t) >= 3
    # manual submit after auto-claim is rejected (cards already claimed)
    ok, err = g.do_black_market_submit(0, t)
    assert not ok and ("already completed" in err or "Need 3" in err), (ok, err)
    # second slot by another player
    events2 = []
    for _ in range(3):
        events2.extend(g._deliver(ps[1], {"type": t, "value": 8, "fine": 4}))
    assert any("auto-completes" in e for e in events2)
    assert ps[1].gold == 50 + g.quest_rewards[t][1]
    assert ps[1].black_market_cards == 1
    assert g.quest_claimed[t] == 2 and g.quest_claimers[t][1] == "B"
    # after both slots claimed, no one can claim again
    for _ in range(3):
        g._deliver(ps[0], {"type": t, "value": 8, "fine": 4})
    assert g.quest_claimed[t] == 2 and ps[0].gold == 50 + g.quest_rewards[t][0]
    print("PASS black market auto submit (rewards 30-35/25-30, claims on delivery)")


def test_royal_scoring():
    ps = [game.Player("A"), game.Player("B")]
    g = game.Game(ps, rng=game.random.Random(3))
    g.quest_types = []
    g.quest_claimed = {}
    g.quest_claimers = {}
    g.quest_rewards = {}
    ps[0].stand_contra.append({"type": "ROYAL_GREEN_APPLE", "value": 4, "fine": 3,
                               "royal": True, "royal_type": "APPLE", "equals": 2})
    rows = g.score()
    a = next(r for r in rows if r["name"] == "A")
    assert a["royal"]["APPLE"] == 2 and a["legal"]["APPLE"] == 0, a["royal"]
    table = g.bonus_table()
    appl = next(x for x in table if x["type"] == "APPLE" and x["kind"] == "king")
    assert appl["awards"][0]["name"] == "A"
    assert appl["awards"][0]["bonus"] == game.KING_BONUS["APPLE"], appl
    # 1 green apple (eff 2) + 1 gold apple (eff 3) = eff 5 beats 4 normal apples
    ps2 = [game.Player("A"), game.Player("B")]
    g2 = game.Game(ps2, rng=game.random.Random(4))
    g2.quest_types = []
    g2.quest_claimed = {}
    g2.quest_claimers = {}
    g2.quest_rewards = {}
    ps2[0].stand_contra.extend([
        {"type": "ROYAL_GREEN_APPLE", "value": 4, "fine": 3, "royal": True, "royal_type": "APPLE", "equals": 2},
        {"type": "ROYAL_GOLD_APPLE", "value": 6, "fine": 4, "royal": True, "royal_type": "APPLE", "equals": 3}])
    ps2[1].stand_legal.extend([{"type": "APPLE", "value": 2, "fine": 2}] * 4)
    t2 = g2.bonus_table()
    a2 = next(x for x in t2 if x["type"] == "APPLE" and x["kind"] == "king")
    assert a2["awards"][0]["name"] == "A", a2
    print("PASS royal scoring (cards count at their face multiplier for king/queen)")


def test_black_market_end_bonus():
    ps = [game.Player("A"), game.Player("B")]
    g = game.Game(ps, rng=game.random.Random(5))
    g.quest_types = []
    g.quest_claimed = {}
    g.quest_claimers = {}
    g.quest_rewards = {}
    ps[0].black_market_cards = 2
    rows = g.score()
    a = rows[0]
    assert a["bonus"] == 2 * game.BLACK_MARKET_CARD_BONUS, a["bonus"]
    assert any(x["type"] == "BLACK_MARKET" and x["count"] == 2 and x["bonus"] == 50
               for x in a["bonus_detail"])
    table = g.bonus_table()
    bm = next(x for x in table if x["kind"] == "blackmarket")
    assert bm["awards"][0]["name"] == "A" and bm["awards"][0]["bonus"] == 50
    print("PASS black market end bonus (+25 per card)")


def test_view_and_messages():
    ps = [game.Player("A"), game.Player("B")]
    g = game.Game(ps, rng=game.random.Random(6))
    bmv = g.black_market_view()
    assert bmv is not None and len(bmv["types"]) == 3
    assert "progress" not in bmv, "smuggling progress must stay secret"
    assert bmv["need"] == 3
    g2 = game.Game(ps, rng=game.random.Random(7), black_market=False, royal=False)
    assert g2.black_market_view() is None
    assert len(g2.deck) + 6 * len(ps) + 10 == 156
    assert g2.quest_types == []
    import lang
    en = "A completes BLACK MARKET quest for Silk (1st reward): +33 gold, +Black Market card"
    zh = lang.translate(en, "zh")
    assert "\u9ed1\u5e02" in zh and "\u4e1d\u7ef8" in zh and "33" in zh, zh
    zh2 = lang.translate(
        "Inspection of Bob: LIE! 2 contraband seized (Silkx1, Winex1), merchant pays 8 gold fine, 1 mismatched legal card(s) detained", "zh")
    assert "\u4e1d\u7ef8" in zh2 and "\u9152" in zh2 and "\u7f5a\u6b3e" in zh2, zh2
    zh3 = lang.translate("Inspection of Bob: LIE! 3 mismatched legal card(s) detained, no fine", "zh")
    assert "\u6263\u7559" in zh3 and "\u4e0d\u7f5a\u6b3e" in zh3, zh3
    zh4 = lang.translate("Alice discarded 3 card(s) (2 legal, 1 contraband). Draw to 6.", "zh")
    assert "\u5408\u6cd5" in zh4 and "\u8fdd\u7981\u54c1" in zh4, zh4
    zh5 = lang.translate("Bob sealed their bag (2 card(s))", "zh")
    assert "\u5df2\u5c01\u888b" in zh5, zh5
    zh6 = lang.translate("A smuggled Green Apple (counts as 2 Apple)", "zh")
    assert "\u9752\u82f9\u679c" in zh6 and "\u76f8\u5f53\u4e8e 2 \u4e2a \u82f9\u679c" in zh6, zh6
    print("PASS views + zh translation")


def test_confiscation_fines():
    """Custom rule: caught lie -> seize contraband/royal (merchant pays fine),
    mismatched legal goods are detained (??) without any fine, declared goods pass."""
    ps = [game.Player("A"), game.Player("B")]
    g = game.Game(ps, rng=game.random.Random(8))
    g.quest_types = []
    g.quest_claimed = {}
    g.quest_claimers = {}
    g.quest_rewards = {}
    ps[0].bag = [{"type": "APPLE", "value": 2, "fine": 2}, {"type": "APPLE", "value": 2, "fine": 2},
                 {"type": "CHICKEN", "value": 4, "fine": 2},
                 {"type": "SILK", "value": 8, "fine": 4},
                 {"type": "ROYAL_GREEN_APPLE", "value": 4, "fine": 3,
                  "royal": True, "royal_type": "APPLE", "equals": 2}]
    ps[0].decl = {"type": "APPLE", "count": 4}
    g.phase = "INSPECT"
    g.sheriff = 1
    g.inspect_idx = 0
    g.order = [0]
    ok, events = g.do_inspect_decision(1, "inspect")
    assert ok, events
    assert len(ps[0].stand_legal) == 2, ps[0].stand_legal        # both apples passed
    assert len(ps[0].stand_contra) == 0, ps[0].stand_contra       # royal was seized too
    d1_types = [c["type"] for c in g.d1]
    assert "SILK" in d1_types and "ROYAL_GREEN_APPLE" in d1_types, d1_types
    assert "CHICKEN" in d1_types, "mismatched legal must be detained, not delivered"
    assert all(c["type"] != "CHICKEN" for c in ps[0].stand_legal)
    assert any("merchant pays 7 gold fine" in e and "Silkx1" in e for e in events), events
    assert any("1 mismatched legal card(s) detained" in e for e in events), events
    assert any("Round 0 complete" in e or "Game over" in e for e in events), events
    assert ps[1].gold == 57 and ps[0].gold == 43                   # silk(4) + royal(3) fine only
    print("PASS confiscation rule (seize contraband/royal + fine, detain mismatched legal, no fine)")


def test_rounds_total_override():
    ps = [game.Player("A"), game.Player("B")]
    g = game.Game(ps, rng=game.random.Random(9), rounds_total=9)
    assert g.rounds_total == 9, g.rounds_total
    g2 = game.Game(ps, rng=game.random.Random(10))
    assert g2.rounds_total == 2 * len(ps), g2.rounds_total
    print("PASS rounds_total override (9 rounds for 3p test, default = n*2)")


def test_hand_cap_and_discard_report():
    ps = [game.Player("A"), game.Player("B")]
    g = game.Game(ps, rng=game.random.Random(11))
    g.start_round()
    p = ps[g.market_current()]
    while len(p.hand) < game.HAND_SIZE:
        p.hand.append(g.deck.pop())
    ok, err = g.do_market_draw(g.market_current(), "deck")
    assert not ok and "already full" in err, (ok, err)            # 7-card bug fixed
    n0 = len(p.hand)
    ok, msg = g.do_market_discard(g.market_current(), [0, 1])
    assert ok and "legal" in msg and "contraband" in msg, msg
    assert len(p.hand) == n0 - 2
    print("PASS hand cap (no 7th card) + discard legal/contraband report")


def test_rename_via_server():
    import net
    srv = net.GameServer(2, port=5597, royal=False, black_market=False)
    try:
        c = net.GameClient("127.0.0.1", 5597, "Alice")
        for _ in range(50):
            for m in c.poll():
                if m.get("t") == "lobby":
                    c.send({"t": "rename", "name": "Alice2"})
                if m.get("t") == "lobby" and any(j["name"] == "Alice2" for j in m.get("joined", [])):
                    c.close()
                    print("PASS rename via server")
                    return
            import time; time.sleep(0.02)
        raise AssertionError("rename did not propagate")
    finally:
        srv.stop()


def test_draw_allowance():
    """Market draw is limited to the number of discarded cards."""
    ps = [game.Player("A"), game.Player("B")]
    g = game.Game(ps, rng=game.random.Random(12))
    g.start_round()
    p = ps[g.market_current()]
    ok, msg = g.do_market_discard(g.market_current(), [0, 1])
    assert ok and len(p.hand) == 4 and g.draw_allow.get(g.market_current()) == 2, (ok, msg)
    ok, _ = g.do_market_draw(g.market_current(), "deck")
    assert ok and len(p.hand) == 5
    ok, _ = g.do_market_draw(g.market_current(), "deck")
    assert ok and len(p.hand) == 6
    ok, err = g.do_market_draw(g.market_current(), "deck")
    assert not ok and ("No more draws left" in err or "already full" in err), (ok, err)
    print("PASS draw allowance (draw limited to discarded count)")


def test_zero_discard_autofinish():
    """Discarding 0 cards ends the market turn immediately (no 7th-card path)."""
    ps = [game.Player("A"), game.Player("B"), game.Player("C")]
    g = game.Game(ps, rng=game.random.Random(13))
    g.start_round()
    first = g.market_current()
    ok, msg = g.do_market_discard(first, [])
    assert ok and msg == ""
    assert g.market_current() != first, "market turn should advance after 0-card discard"
    p = ps[first]
    assert len(p.hand) == game.HAND_SIZE and len(g.discard_hold.get(first, [])) == 0
    ok, err = g.do_market_draw(first, "deck")
    assert not ok, "drawing after 0-discard must be rejected"
    print("PASS zero-discard auto-finish")


if __name__ == "__main__":
    test_deck()
    test_quest_manual_submit()
    test_royal_scoring()
    test_black_market_end_bonus()
    test_view_and_messages()
    test_confiscation_fines()
    test_rounds_total_override()
    test_hand_cap_and_discard_report()
    test_rename_via_server()
    test_draw_allowance()
    test_zero_discard_autofinish()
    print("ALL NEW RULE TESTS PASSED")
