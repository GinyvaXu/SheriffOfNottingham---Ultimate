# -*- coding: utf-8 -*-
"""Parallel market/declare, ready-to-start gating and black-market secrecy."""

import time

import game
import net


def _mk_game(n=3, seed=42):
    ps = [game.Player(chr(65 + i)) for i in range(n)]
    return game.Game(ps, rng=game.random.Random(seed), royal=False, black_market=True)


def test_parallel_market_all_merchants_act():
    g = _mk_game()
    g.start_round()
    assert g.phase == "MARKET"
    pending = g.market_pending()
    assert len(pending) == g.n - 1, pending
    # every merchant can discard independently, not just the first one
    for seat in pending:
        ok, msg = g.do_market_discard(seat, [])
        assert ok, msg
    assert not g.market_pending()
    assert g.phase == "LOAD"


def test_parallel_market_draw_independent():
    g = _mk_game()
    g.start_round()
    seats = g.market_pending()
    a, b = seats[0], seats[1]
    ok, _ = g.do_market_discard(a, [0, 1])
    assert ok
    # b may discard while a still draws
    ok, _ = g.do_market_discard(b, [0])
    assert ok
    assert g.phase == "MARKET"
    ok, _ = g.do_market_draw(a, "deck")
    assert ok
    g.finish_market_turn(a)
    g.finish_market_turn(b)
    assert g.phase == "LOAD"


def test_parallel_declare_all_then_inspect():
    g = _mk_game()
    g.start_round()
    g.phase = "LOAD"
    for i, p in enumerate(g.players):
        if i != g.sheriff:
            p.bag = [{"type": "APPLE", "value": 2, "fine": 2}]
            p.bag_loaded = True
    g.phase = "DECLARE"
    seats = [i for i in g.order]
    ok, _ = g.do_declare(seats[0], "APPLE")
    assert ok and g.phase == "DECLARE"      # others may still declare
    ok, _ = g.do_declare(seats[1], "BREAD")
    assert ok
    assert g.phase == "INSPECT"             # only when ALL declared
    assert g.inspect_idx == 0


def test_ready_gate_blocks_start():
    srv = net.GameServer(2, port=58731, royal=False, black_market=False)
    try:
        h = net.GameClient("127.0.0.1", 58731, "Host")
        g2 = net.GameClient("127.0.0.1", 58731, "Guest")
        try:
            for _ in range(60):
                for c in (h, g2):
                    for m in c.poll():
                        if m.get("t") == "lobby":
                            pass
                time.sleep(0.02)
            h.send({"t": "start_game", "rounds": 2})
            errs = []
            for _ in range(60):
                for m in h.poll():
                    if m.get("t") == "error":
                        errs.append(m["msg"])
                if errs:
                    break
                time.sleep(0.02)
            assert any("ready" in e.lower() for e in errs), errs
            assert srv.game is None
            # both ready -> starts
            h.send({"t": "ready"})
            g2.send({"t": "ready"})
            time.sleep(0.2)
            h.send({"t": "start_game", "rounds": 2})
            for _ in range(80):
                if srv.game is not None:
                    break
                time.sleep(0.02)
            assert srv.game is not None, "game should start when everyone is ready"
        finally:
            h.close(); g2.close()
    finally:
        srv.stop()


def test_black_market_view_has_no_progress():
    g = _mk_game()
    bm = g.black_market_view()
    assert bm is not None
    assert "progress" not in bm


def test_reject_restores_first_offer():
    g = _mk_game(n=2)
    g.start_round()
    g.phase = "INSPECT"
    sh = g.sheriff
    owner = g.order[0]
    ok, _ = g.do_bribe(owner, 3)
    assert ok
    ok, _ = g.do_counter_bribe(sh, 8)
    assert ok
    ok, _ = g.do_respond_counter(owner, "reject")
    assert ok
    assert g.players[owner].bribe["gold"] == 3
    gold0 = g.players[sh].gold
    ok, ev = g.do_inspect_decision(sh, "pass")
    assert ok
    assert g.players[sh].gold == gold0 + 3
    assert any("bribes the Sheriff 3 gold" in e for e in ev)


if __name__ == "__main__":
    import sys
    sys.exit(0)
