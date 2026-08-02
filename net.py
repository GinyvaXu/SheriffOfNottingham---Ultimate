# -*- coding: utf-8 -*-
"""Network layer: host server + client (TCP + newline-delimited JSON, plaintext, trust mode)"""

import json
import re
import socket
import threading
import queue
import time

import bot
import game

DEFAULT_PORT = 5555
BOT_DELAY = 0.5   # pause between autonomous bot actions so humans can follow


def _send(conn, obj):
    try:
        conn.sendall((json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8"))
        return True
    except OSError:
        return False


class LineReader:
    """Read JSON line by line. End of list = top of pile (same as game.py)."""

    def __init__(self, conn):
        self.conn = conn
        self.buf = b""

    def next_line(self, timeout=None):
        """Return (ok, msg): ok=False means the connection is closed; msg=None means timeout."""
        self.conn.settimeout(timeout)
        while b"\n" not in self.buf:
            try:
                chunk = self.conn.recv(65536)
            except socket.timeout:
                return True, None
            except OSError:
                return False, None
            if not chunk:
                return False, None
            self.buf += chunk
        line, _, self.buf = self.buf.partition(b"\n")
        try:
            return True, json.loads(line.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return True, {"t": "bad_msg"}


class GameServer:
    """Host server: lobby -> game -> results; on disconnect wait for same-name reconnect."""

    def __init__(self, max_players, port=DEFAULT_PORT, rng=None, royal=True, black_market=True,
                 rounds_total=None):
        self.max_players = max_players
        self.port = port
        self.rng = rng
        self.royal = royal
        self.black_market = black_market
        self.rounds_total = rounds_total
        self.game = None
        self.seats = [None] * max_players  # dict(name, conn, reader, seat, game_seat)
        self.lock = threading.RLock()
        self.started = False
        self.stopped = False
        self._discarded = {}    # game_seat -> whether this round's discard is done
        self._seen_round = 0
        self.bot_levels = {}    # game_seat -> bot difficulty level
        self.srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.srv.bind(("0.0.0.0", port))
        self.srv.listen(16)
        self.thread = threading.Thread(target=self._accept_loop, daemon=True)
        self.thread.start()
        self.local_ip = self._get_local_ip()

    # ---------- Basics ----------

    def _get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except OSError:
            return "127.0.0.1"

    def stop(self):
        self.stopped = True
        try:
            self.srv.close()
        except OSError:
            pass
        with self.lock:
            for s in self.seats:
                if s and s["conn"] is not None:
                    try:
                        s["conn"].close()
                    except OSError:
                        pass

    def _broadcast(self, obj):
        for s in self.seats:
            if s and s["conn"] is not None:
                _send(s["conn"], obj)

    def _broadcast_status(self, text):
        self._broadcast({"t": "status", "msg": text})

    def _broadcast_chat(self, name, text):
        self._broadcast({"t": "chat", "from": name, "msg": text})

    # ---------- Connection management ----------

    def _accept_loop(self):
        while not self.stopped:
            try:
                conn, addr = self.srv.accept()
            except OSError:
                break
            threading.Thread(target=self._handle_conn, args=(conn, addr), daemon=True).start()

    def _handle_conn(self, conn, addr):
        reader = LineReader(conn)
        ok, msg = reader.next_line(15)
        if not ok or not msg or msg.get("t") != "hello":
            conn.close()
            return
        name = str(msg.get("name", "")).strip()
        if not name:
            _send(conn, {"t": "error", "msg": "Name cannot be empty"})
            conn.close()
            return
        with self.lock:
            if any(s and s["name"] == name and s["conn"] is not None for s in self.seats):
                _send(conn, {"t": "error", "msg": "Name already in use"})
                conn.close()
                return
            if not self.started:
                seat = next((i for i, s in enumerate(self.seats) if s is None), None)
                if seat is None:
                    _send(conn, {"t": "error", "msg": "Room is full"})
                    conn.close()
                    return
                self.seats[seat] = {"name": name, "conn": conn, "reader": reader,
                                    "seat": seat, "game_seat": None}
                _send(conn, {"t": "welcome", "seat": seat, "name": name, "host": seat == 0})
                self._broadcast_lobby()
            else:
                seat = None
                for i, s in enumerate(self.seats):
                    if s and s["name"] == name and s["conn"] is None:
                        seat = i
                        break
                if seat is None:
                    _send(conn, {"t": "error", "msg": "Game already started; only same-name reconnect is allowed"})
                    conn.close()
                    return
                s = self.seats[seat]
                s["conn"] = conn
                s["reader"] = reader
                self.game.players[s["game_seat"]].connected = True
                _send(conn, {"t": "welcome", "seat": seat, "name": name, "host": seat == 0,
                             "reconnected": True})
                self._broadcast_status(f"{name} reconnected, game continues")
                self._broadcast_views()
        self._read_loop(seat)

    def _read_loop(self, seat):
        s = self.seats[seat]
        conn = s["conn"]
        reader = s["reader"]
        while True:
            ok, msg = reader.next_line(30)
            if not ok:
                break
            if msg is None:
                if self.seats[seat] and self.seats[seat]["conn"] is conn:
                    _send(conn, {"t": "pong"})
                continue
            self._dispatch(seat, msg)
        with self.lock:
            s = self.seats[seat]
            if s is None or s["conn"] is not conn:
                return  # already replaced by a reconnect
            try:
                conn.close()
            except OSError:
                pass
            s["conn"] = None
            if self.started:
                self.game.players[s["game_seat"]].connected = False
                self._broadcast_status(f"{s['name']} disconnected, waiting for reconnect...")
                self._broadcast_views()
            else:
                self.seats[seat] = None
                self._broadcast_lobby()

    # ---------- Lobby / game dispatch ----------

    def _broadcast_lobby(self):
        joined = [{"seat": i, "name": s["name"], "host": i == 0,
                   "bot": s.get("bot")}
                  for i, s in enumerate(self.seats) if s is not None]
        for i, s in enumerate(self.seats):
            if s and s["conn"] is not None:
                _send(s["conn"], {"t": "lobby", "max_players": self.max_players,
                                  "joined": joined, "can_start": len(joined) >= 2 and i == 0})

    def _dispatch(self, seat, msg):
        t = msg.get("t")
        with self.lock:
            s = self.seats[seat]
            if s is None:
                return
            if t == "chat":
                self._broadcast_chat(s["name"], str(msg.get("msg", ""))[:200])
                return
            if t == "ping":
                return
            if t == "rename":
                ok, err = self._rename(seat, msg.get("name"))
                if ok:
                    self._after_rename()
                else:
                    _send(s["conn"], {"t": "error", "msg": err})
                return
            if not self.started:
                if t == "start_game" and seat == 0:
                    joined = [i for i, x in enumerate(self.seats) if x is not None]
                    if len(joined) < 2:
                        _send(s["conn"], {"t": "error", "msg": "Need at least 2 players to start"})
                        return
                    self._start_game(joined, msg.get("rounds"))
                elif t == "add_bot" and seat == 0:
                    self._add_bot(str(msg.get("level", "normal")).lower())
                elif t == "remove_bot" and seat == 0:
                    self._remove_bot(msg.get("seat"))
                return
            if t == "host_quit":
                self._broadcast({"t": "server_closed", "msg": "Host closed the room"})
                self.stop()
                return
            self._handle_game_action(seat, t, msg)

    def _start_game(self, joined, rounds=None):
        players = [game.Player(self.seats[i]["name"]) for i in joined]
        self.game = game.Game(players, rng=self.rng, royal=self.royal,
                              black_market=self.black_market,
                              rounds_total=rounds or self.rounds_total)
        self.bot_levels = {}
        for gi, si in enumerate(joined):
            self.seats[si]["game_seat"] = gi
            if self.seats[si].get("bot"):
                self.bot_levels[gi] = self.seats[si]["bot"]
        self.game.start_round()
        self.started = True
        self._discarded = {}
        self._seen_round = self.game.round_no
        self._broadcast({"t": "game_start", "msg": "Game started!"})
        self._broadcast_views()
        self._drive_bots()

    def _handle_game_action(self, seat, t, msg):
        g = self.game
        s = self.seats[seat]
        gseat = s.get("game_seat")
        if gseat is None:
            return
        if not all(p.connected for p in g.players):
            _send(s["conn"], {"t": "error", "msg": "A player is disconnected, waiting for reconnect"})
            return
        ok = False
        banner = ""
        events = []
        if t == "market_discard":
            ok, banner = g.do_market_discard(gseat, msg.get("cards", []))
            if ok:
                self._discarded[gseat] = True
                if not banner:
                    # discarded 0 cards: game already ended this market turn
                    banner = ""
        elif t == "market_draw":
            ok, banner = g.do_market_draw(gseat, msg.get("from", "deck"))
            if not ok and banner == "Your hand is already full":
                ok, banner = True, ""          # hand full => market turn auto-ends
                g.finish_market_turn(gseat)
            elif ok and (len(g.players[gseat].hand) >= game.HAND_SIZE
                         or g.draw_allow.get(gseat, 0) <= 0):
                g.finish_market_turn(gseat)
        elif t == "market_done":
            ok = True
            g.finish_market_turn(gseat)
            banner = "Stop drawing"
        elif t == "load_bag":
            ok, banner = g.do_load(gseat, msg.get("cards", []))
        elif t == "declare":
            ok, banner = g.do_declare(gseat, msg.get("type"))
        elif t == "bribe":
            ok, banner = g.do_bribe(gseat, msg.get("gold", 0), msg.get("msg", ""))
            if ok:
                b = g.players[gseat].bribe or {}
                if b.get("gold") or b.get("msg"):
                    pub = f"{s['name']} offers a bribe of {b['gold']} gold"
                    if b.get("msg"):
                        pub += f": {b['msg']}"
                    banner = pub
        elif t == "inspect_decision":
            ok, res = g.do_inspect_decision(gseat, msg.get("action"))
            if ok:
                events = res
            else:
                banner = res[0] if res else "Action failed"
        elif t == "black_market_submit":
            ok, banner = g.do_black_market_submit(gseat, msg.get("type"), msg.get("slot"))
        if not ok:
            _send(s["conn"], {"t": "error", "msg": banner or "Action failed"})
            return
        for e in events:
            self._broadcast({"t": "banner", "msg": e})
        if banner:
            pub = banner
            if t == "market_discard":
                pub = banner.replace("You ", f"{s['name']} ", 1)
            elif t == "load_bag":
                m = re.search(r"\((\d+) card", banner)
                pub = f"{s['name']} sealed their bag ({m.group(1)} card(s))" if m else banner
            self._broadcast({"t": "banner", "msg": pub})
        self._broadcast_views()
        self._drive_bots()

    # ---------- Bots ----------

    def _is_bot(self, gseat):
        return gseat in self.bot_levels

    def _bot_level(self, gseat):
        return self.bot_levels.get(gseat, "normal")

    def _add_bot(self, level):
        if level not in bot.LEVELS:
            level = "normal"
        seat = next((i for i, s in enumerate(self.seats) if s is None), None)
        if seat is None:
            return
        self.seats[seat] = {"name": bot.bot_name(level), "conn": None, "reader": None,
                            "seat": seat, "game_seat": None, "bot": level}
        self._broadcast_lobby()

    def _remove_bot(self, seat):
        try:
            seat = int(seat)
        except (TypeError, ValueError):
            return
        if not (0 <= seat < len(self.seats)):
            return
        s = self.seats[seat]
        if s is None or not s.get("bot"):
            return
        self.seats[seat] = None
        self._broadcast_lobby()

    def _drive_bots(self):
        """Play every bot seat that is waiting to act (host-server thread)."""
        g = self.game
        if g is None or not self.bot_levels or g.phase in ("LOBBY", "GAME_OVER"):
            return
        for _ in range(80):
            with self.lock:
                g = self.game
                if g is None or g.phase in ("LOBBY", "GAME_OVER"):
                    return
                acted = False
                if g.phase == "MARKET":
                    seat = g.market_current()
                    if not self._is_bot(seat):
                        return
                    acted = self._bot_market(seat)
                elif g.phase == "LOAD":
                    pending = [i for i, p in enumerate(g.players)
                               if i != g.sheriff and not p.bag_loaded and self._is_bot(i)]
                    if not pending:
                        return
                    acted = self._bot_load_bags(pending)
                elif g.phase == "DECLARE":
                    seat = g.declare_current()
                    if not self._is_bot(seat):
                        return
                    acted = self._bot_declare(seat)
                elif g.phase == "INSPECT":
                    target = g.inspect_current()
                    if self._is_bot(target) and g.players[target].bribe is None:
                        acted = self._bot_bribe(target)
                    elif g.players[target].bribe is not None and self._is_bot(g.sheriff):
                        acted = self._bot_inspect_decision()
                    else:
                        return
                bm_acted = self._bot_black_market()
            if not acted and not bm_acted:
                return
            time.sleep(BOT_DELAY)
        self._broadcast_views()

    def _bot_market(self, seat):
        g = self.game
        p = g.players[seat]
        idx = bot.choose_discard(g, seat, self._bot_level(seat))
        ok, msg = g.do_market_discard(seat, idx)
        if not ok:
            return False
        if msg:
            self._broadcast({"t": "banner", "msg": msg.replace("You ", f"{p.name} ", 1)})
        for _ in range(8):
            if len(p.hand) >= game.HAND_SIZE or g.draw_allow.get(seat, 0) <= 0:
                break
            if g.phase != "MARKET" or g.market_current() != seat:
                break
            ok2, _ = g.do_market_draw(seat, "deck")
            if not ok2:
                break
        if g.phase == "MARKET" and g.market_current() == seat:
            g.finish_market_turn(seat)
        self._broadcast_views()
        return True

    def _bot_load_bags(self, pending):
        g = self.game
        acted = False
        for si in pending:
            p = g.players[si]
            idx = bot.choose_load(g, si, self._bot_level(si))
            ok, msg = g.do_load(si, idx)
            if ok:
                acted = True
                m = re.search(r"\((\d+) card", msg)
                pub = f"{p.name} sealed their bag ({m.group(1)} card(s))" if m else msg
                self._broadcast({"t": "banner", "msg": pub})
        self._broadcast_views()
        return acted

    def _bot_declare(self, seat):
        g = self.game
        ctype = bot.choose_declare(g, seat, self._bot_level(seat))
        ok, _ = g.do_declare(seat, ctype)
        self._broadcast_views()
        return ok

    def _bot_bribe(self, target):
        g = self.game
        gold, msg = bot.choose_bribe(g, target, self._bot_level(target))
        ok, _ = g.do_bribe(target, gold, msg)
        if ok and (gold or msg):
            pub = f"{g.players[target].name} offers a bribe of {gold} gold"
            if msg:
                pub += f": {msg}"
            self._broadcast({"t": "banner", "msg": pub})
        self._broadcast_views()
        return ok

    def _bot_inspect_decision(self):
        g = self.game
        action = bot.choose_inspect(g, g.sheriff, self._bot_level(g.sheriff))
        ok, events = g.do_inspect_decision(g.sheriff, action)
        if ok:
            for e in events:
                self._broadcast({"t": "banner", "msg": e})
        self._broadcast_views()
        return ok

    def _bot_black_market(self):
        g = self.game
        acted = False
        for gseat, lvl in list(self.bot_levels.items()):
            pick = bot.choose_black_market(g, gseat, lvl)
            if pick is None:
                continue
            ctype, slot = pick
            ok, msg = g.do_black_market_submit(gseat, ctype, slot)
            if ok:
                acted = True
                self._broadcast({"t": "banner", "msg": msg})
        if acted:
            self._broadcast_views()
        return acted

    # ---------- Views ----------

    def _private_view(self, gseat):
        g = self.game
        p = g.players[gseat]
        def _card(c):
            return {"type": c["type"], "value": c["value"],
                    "fine": c.get("fine", c["value"]),
                    "equals": c.get("equals"), "of": c.get("royal_type")}
        return {
            "hand": [_card(c) for c in p.hand],
            "bag": [_card(c) for c in p.bag],
            "stand_contra": [_card(c) for c in p.stand_contra],
            "black_market_cards": p.black_market_cards,
        }

    def _prompt_for(self, gseat):
        g = self.game
        p = g.players[gseat]
        if g.phase == "MARKET" and gseat == g.market_current():
            if not self._discarded.get(gseat):
                return {"kind": "market_discard", "max_discard": min(game.DISCARD_MAX, len(p.hand))}
            return {"kind": "market_draw", "hand": len(p.hand),
                    "draw_left": g.draw_allow.get(gseat, 0)}
        if g.phase == "LOAD" and gseat != g.sheriff and not p.bag_loaded:
            return {"kind": "load_bag"}
        if g.phase == "DECLARE" and gseat == g.declare_current():
            return {"kind": "declare", "bag_count": len(p.bag)}
        if g.phase == "INSPECT":
            target = g.players[g.inspect_current()]
            if gseat == g.inspect_current() and target.bribe is None:
                return {"kind": "bribe", "gold": target.gold}
            if gseat == g.sheriff and target.bribe is not None:
                return {"kind": "inspect", "owner": target.name,
                        "bribe_gold": target.bribe.get("gold", 0),
                        "bribe_msg": target.bribe.get("msg", "")}
        return None

    def _acting_name(self):
        g = self.game
        if g.phase == "MARKET":
            return g.players[g.market_current()].name
        if g.phase == "LOAD":
            return "Waiting for merchants to load bags"
        if g.phase == "DECLARE":
            return g.players[g.declare_current()].name
        if g.phase == "INSPECT":
            t = g.inspect_current()
            if g.players[t].bribe is None:
                return g.players[t].name
            return g.players[g.sheriff].name
        return None

    def _acting_phase(self):
        g = self.game
        if g.phase == "MARKET":
            if not self._discarded.get(g.market_current()):
                return "market_discard"
            return "market_draw"
        if g.phase == "LOAD":
            return "load"
        if g.phase == "DECLARE":
            return "declare"
        if g.phase == "INSPECT":
            if g.players[g.inspect_current()].bribe is None:
                return "bribe"
            return "inspect"
        return None

    def _rename(self, seat, new_name):
        new_name = str(new_name or "").strip()
        if not new_name:
            return False, "Name cannot be empty"
        with self.lock:
            if any(s and s["name"] == new_name and s["seat"] != seat
                   for s in self.seats):
                return False, "Name already in use"
            self.seats[seat]["name"] = new_name
            if self.game is not None and self.seats[seat]["game_seat"] is not None:
                self.game.players[self.seats[seat]["game_seat"]].name = new_name
        return True, ""

    def _after_rename(self):
        if self.game is not None:
            self._broadcast_views()
        else:
            self._broadcast_lobby()

    def _view_for(self, gseat):
        g = self.game
        pub = {
            "t": "view",
            "phase": g.phase,
            "round": g.round_no,
            "rounds_total": g.rounds_total,
            "sheriff": g.sheriff,
            "players": [p.view_public() for p in g.players],
            "deck_count": len(g.deck),
            "acting": self._acting_name(),
            "acting_phase": self._acting_phase(),
            "black_market": g.black_market_view(),
        }
        if g.phase == "GAME_OVER":
            pub["scores"] = g.score()
            pub["bonus_table"] = g.bonus_table()
            pub["prompt"] = None
        else:
            pub["you"] = self._private_view(gseat)
            pub["prompt"] = self._prompt_for(gseat)
        return pub

    def _broadcast_views(self):
        if self.game is None:
            return
        g = self.game
        if g.round_no != self._seen_round:
            self._discarded = {}
            self._seen_round = g.round_no
        with self.lock:
            for s in self.seats:
                if s is None or s["game_seat"] is None or s["conn"] is None:
                    continue
                _send(s["conn"], self._view_for(s["game_seat"]))


class GameClient:
    """Client: background reader thread + message queue; emits a disconnected event on drop."""

    def __init__(self, host, port, name):
        self.name = name
        self.sock = socket.create_connection((host, port), timeout=10)
        self.sock.settimeout(None)
        self.q = queue.Queue()
        self.send_lock = threading.Lock()
        self.alive = True
        self.send({"t": "hello", "name": name})
        self.thread = threading.Thread(target=self._read_loop, daemon=True)
        self.thread.start()

    def _read_loop(self):
        reader = LineReader(self.sock)
        while self.alive:
            ok, msg = reader.next_line(5)
            if not ok:
                self.q.put({"t": "disconnected"})
                return
            if msg is None:
                self.send({"t": "ping"})
                continue
            self.q.put(msg)

    def send(self, obj):
        with self.send_lock:
            try:
                self.sock.sendall((json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8"))
                return True
            except OSError:
                self.alive = False
                return False

    def poll(self):
        out = []
        while True:
            try:
                out.append(self.q.get_nowait())
            except queue.Empty:
                break
        return out

    def close(self):
        self.alive = False
        try:
            self.sock.close()
        except OSError:
            pass
