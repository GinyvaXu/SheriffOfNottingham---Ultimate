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
import profile
import version

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
        self.bot_levels = {}            # game_seat -> bot difficulty level
        self.bot_personalities = {}     # game_seat -> bot personality tag (optional)
        self._last_action_ts = time.time()
        self._timeout_thread = threading.Thread(target=self._tick_timeouts, daemon=True)
        self._timeout_thread.start()
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
        rules = self._norm_mods(msg.get("mods"))
        avatar = profile.avatar_from_payload(msg.get("avatar"))
        ver = str(msg.get("ver", "")).strip()
        if ver != version.__version__:
            _send(conn, {"t": "error", "code": "version",
                         "msg": "Version mismatch: host is v{0}, you are v{1}".format(
                             version.__version__, ver or "?")})
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
                                    "seat": seat, "game_seat": None, "ready": False,
                                    "rules_mods": rules, "avatar": avatar}
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
                s["rules_mods"] = rules
                s["avatar"] = avatar
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

    @staticmethod
    def _norm_mods(raw):
        """Normalize a client-reported rule-mod list to [{"id","version"}] sorted."""
        out = []
        for m in raw or []:
            if not isinstance(m, dict):
                continue
            mid = str(m.get("id", "")).strip()
            if not mid:
                continue
            out.append({"id": mid.lower(), "version": str(m.get("version", "")).strip()})
        out.sort(key=lambda x: x["id"])
        return out

    def _seat_mods_ok(self, s):
        """True when a seat's rule mods match the host's (bots always match)."""
        if s is None:
            return True
        if s.get("bot"):
            return True  # bots run inside the host process -> always in sync
        host_mods = self.seats[0]["rules_mods"] if self.seats[0] else []
        return self._norm_mods(s.get("rules_mods")) == host_mods

    def _mods_check(self):
        """List of seats whose rule mods differ from the host's (humans only)."""
        host_mods = self.seats[0]["rules_mods"] if self.seats[0] else []
        missing = []
        for i, s in enumerate(self.seats):
            if s is None or s.get("bot") or s["conn"] is None:
                continue
            have = self._norm_mods(s.get("rules_mods"))
            if have != host_mods:
                missing.append({"seat": i, "name": s["name"],
                                "have": have, "need": host_mods})
        return missing

    def _broadcast_lobby(self):
        joined = [{"seat": i, "name": s["name"], "host": i == 0,
                   "bot": s.get("bot"), "avatar": s.get("avatar"),
                   "personality": s.get("personality"),
                   "ready": bool(s.get("ready"))}
                  for i, s in enumerate(self.seats) if s is not None]
        conflicts = []
        try:
            import mods as _mods
            for a, b in _mods.enabled_rule_mods_compat():
                conflicts.append([a.get("id"), b.get("id")])
        except Exception:  # noqa: BLE001 - conflicts are advisory
            conflicts = []
        host_mods = self.seats[0]["rules_mods"] if self.seats[0] else []
        players_mods = []
        for i, s in enumerate(self.seats):
            if s is None:
                continue
            players_mods.append({"seat": i, "name": s["name"],
                                 "mods": host_mods if s.get("bot") else s.get("rules_mods", [])})
        mods_ok = all(self._seat_mods_ok(s) for s in self.seats if s is not None)
        all_ready = len(joined) >= 2 and all(j.get("ready") for j in joined)
        for i, s in enumerate(self.seats):
            if s and s["conn"] is not None:
                _send(s["conn"], {"t": "lobby", "max_players": self.max_players,
                                  "joined": joined, "can_start": all_ready and i == 0,
                                  "rules_mods": host_mods, "players_mods": players_mods,
                                  "mods_ok": mods_ok, "rmods_conflicts": conflicts})

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
            if t == "ready":
                if not self.started:
                    s["ready"] = not bool(s.get("ready"))
                    self._broadcast_lobby()
                return
            if not self.started:
                if t == "start_game" and seat == 0:
                    joined = [i for i, x in enumerate(self.seats) if x is not None]
                    if len(joined) < 2:
                        _send(s["conn"], {"t": "error", "msg": "Need at least 2 players to start"})
                        return
                    bad = self._mods_check()
                    if bad:
                        names = ", ".join(x["name"] for x in bad)
                        _send(s["conn"], {"t": "error", "msg": "Rule mods mismatch - " + names})
                        self._broadcast({"t": "mods_mismatch", "missing": bad})
                        return
                    try:
                        import mods as _mods
                        conflicts = _mods.enabled_rule_mods_compat()
                    except Exception:  # noqa: BLE001
                        conflicts = []
                    if conflicts:
                        names = ", ".join(f"{a['name']} x {b['name']}" for a, b in conflicts)
                        _send(s["conn"], {"t": "error",
                                          "msg": "Incompatible rule mods: " + names})
                        self._broadcast({"t": "mods_incompatible", "names": names})
                        return
                    if not all(self.seats[i].get("ready") for i in joined):
                        _send(s["conn"], {"t": "error",
                                          "msg": "All players must be ready to start"})
                        return
                    self._start_game(joined, msg.get("rounds"), msg.get("wild"))
                elif t == "add_bot" and seat == 0:
                    self._add_bot(str(msg.get("level", "normal")).lower(),
                                  msg.get("personality") or None)
                elif t == "remove_bot" and seat == 0:
                    self._remove_bot(msg.get("seat"))
                return
            if t == "back_to_lobby":
                self._back_to_lobby()
                return
            if t == "host_quit":
                self._broadcast({"t": "server_closed", "msg": "Host closed the room"})
                self.stop()
                return
            self._handle_game_action(seat, t, msg)

    def _back_to_lobby(self):
        """After a finished game, return everyone to the lobby of the same room."""
        with self.lock:
            if self.game is None or self.game.phase != "GAME_OVER":
                return
            self.game = None
            self.started = False
            self._discarded = {}
            self._seen_round = 0
            self.bot_levels = {}
            for i, s in enumerate(self.seats):
                if s is None:
                    continue
                s["game_seat"] = None
                s["ready"] = bool(s.get("bot"))
                # drop human ghosts who never reconnected; bots stay in the room
                if not s.get("bot") and s["conn"] is None:
                    self.seats[i] = None
        self._broadcast_lobby()

    def _start_game(self, joined, rounds=None, wild=None):
        if wild is not None:
            game.WILD_CARDS = max(0, int(wild or 0))
        players = [game.Player(self.seats[i]["name"],
                               avatar=self.seats[i].get("avatar")) for i in joined]
        self.game = game.Game(players, rng=self.rng, royal=self.royal,
                              black_market=self.black_market,
                              rounds_total=rounds or self.rounds_total)
        self.bot_levels = {}
        self.bot_personalities = {}
        for gi, si in enumerate(joined):
            self.seats[si]["game_seat"] = gi
            if self.seats[si].get("bot"):
                self.bot_levels[gi] = self.seats[si]["bot"]
                if self.seats[si].get("personality"):
                    self.bot_personalities[gi] = self.seats[si]["personality"]
        self.game.start_round()
        self.started = True
        self._last_action_ts = time.time()
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
        elif t == "counter_bribe":
            ok, res = g.do_counter_bribe(gseat, msg.get("gold", 0))
            if ok:
                events = res
            else:
                banner = res[0] if res else "Action failed"
        elif t == "counter_response":
            ok, res = g.do_respond_counter(gseat, msg.get("action", ""), msg.get("gold", 0))
            if ok:
                events = res
            else:
                banner = res[0] if res else "Action failed"
        elif t == "inspect_decision":
            ok, res = g.do_inspect_decision(gseat, msg.get("action"))
            if ok:
                events = res
            else:
                banner = res[0] if res else "Action failed"
        elif t == "sheriff_intel":
            ok, res = g.do_sheriff_intel(gseat)
            if ok:
                self._broadcast({"t": "banner", "msg":
                                 "{0} pays {1} gold for sheriff intel".format(
                                     s["name"], res["cost"])})
                _send(s["conn"], {"t": "intel", "lo": res["lo"], "hi": res["hi"]})
                banner = ""
            else:
                banner = res[0] if isinstance(res, (list, tuple)) else res
        elif t == "black_market_submit":
            ok, banner = g.do_black_market_submit(gseat, msg.get("type"), msg.get("slot"))
        if not ok:
            _send(s["conn"], {"t": "error", "msg": banner or "Action failed"})
            return
        self._last_action_ts = time.time()
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

    def _bot_personality(self, gseat):
        return self.bot_personalities.get(gseat)

    def _add_bot(self, level, personality=None):
        if level not in bot.LEVELS:
            level = "normal"
        if personality not in bot.PERSONALITIES:
            personality = None
        seat = next((i for i, s in enumerate(self.seats) if s is None), None)
        if seat is None:
            return
        n = sum(1 for s in self.seats if s and s.get("bot") == level
                and s.get("personality") == personality)
        self.seats[seat] = {"name": bot.bot_name(level, n + 1, personality),
                            "conn": None, "reader": None,
                            "seat": seat, "game_seat": None, "bot": level,
                            "personality": personality, "ready": True,
                            "avatar": {"kind": "builtin",
                                       "id": bot.bot_avatar(level, n + 1)}}
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
                try:
                    if g.phase == "MARKET":
                        pending = [i for i in g.order
                                   if not g.market_done.get(i) and self._is_bot(i)]
                        if not pending:
                            return
                        acted = any(self._bot_market(seat) for seat in pending)
                    elif g.phase == "LOAD":
                        pending = [i for i, p in enumerate(g.players)
                                   if i != g.sheriff and not p.bag_loaded and self._is_bot(i)]
                        if not pending:
                            return
                        acted = self._bot_load_bags(pending)
                    elif g.phase == "DECLARE":
                        pending = [i for i in g.order
                                   if g.players[i].decl is None and self._is_bot(i)]
                        if not pending:
                            return
                        acted = any(self._bot_declare(seat) for seat in pending)
                    elif g.phase == "INSPECT":
                        target = g.inspect_current()
                        tp = g.players[target]
                        if self._is_bot(target) and tp.bribe is None:
                            acted = self._bot_bribe(target)
                        elif self._is_bot(target) and tp.sheriff_demand is not None:
                            acted = self._bot_counter_response(target)
                        elif tp.bribe is not None and tp.sheriff_demand is None and self._is_bot(g.sheriff):
                            acted = self._bot_inspect_decision()
                        else:
                            return
                    bm_acted = self._bot_black_market()
                except Exception:  # noqa: BLE001 - one bad bot decision must never freeze the server
                    import traceback
                    traceback.print_exc()
                    return
            if not acted and not bm_acted:
                return
            time.sleep(BOT_DELAY)
        self._broadcast_views()

    def _bot_market(self, seat):
        g = self.game
        p = g.players[seat]
        idx = bot.choose_discard(g, seat, self._bot_level(seat), self._bot_personality(seat))
        ok, msg = g.do_market_discard(seat, idx)
        if not ok:
            return False
        if msg:
            self._broadcast({"t": "banner", "msg": msg.replace("You ", f"{p.name} ", 1)})
        for _ in range(8):
            if len(p.hand) >= game.HAND_SIZE or g.draw_allow.get(seat, 0) <= 0:
                break
            if g.phase != "MARKET" or g.market_done.get(seat):
                break
            ok2, _ = g.do_market_draw(seat, "deck")
            if not ok2:
                break
        if g.phase == "MARKET" and not g.market_done.get(seat):
            g.finish_market_turn(seat)
        self._broadcast_views()
        return True

    def _bot_load_bags(self, pending):
        g = self.game
        acted = False
        for si in pending:
            p = g.players[si]
            idx = bot.choose_load(g, si, self._bot_level(si), self._bot_personality(si))
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
        ctype = bot.choose_declare(g, seat, self._bot_level(seat), self._bot_personality(seat))
        ok, _ = g.do_declare(seat, ctype)
        self._broadcast_views()
        return ok

    def _bot_bribe(self, target):
        g = self.game
        gold, msg = bot.choose_bribe(g, target, self._bot_level(target), self._bot_personality(target))
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
        action, gold = bot.choose_inspect(g, g.sheriff, self._bot_level(g.sheriff),
                                          self._bot_personality(g.sheriff))
        if action == "counter":
            ok, events = g.do_counter_bribe(g.sheriff, gold or 0)
        else:
            ok, events = g.do_inspect_decision(g.sheriff, action)
        if ok:
            for e in events:
                self._broadcast({"t": "banner", "msg": e})
        self._broadcast_views()
        return ok

    def _bot_counter_response(self, target):
        g = self.game
        action, gold = bot.choose_respond(g, target, self._bot_level(target),
                                          self._bot_personality(target))
        ok, events = g.do_respond_counter(target, action, gold or 0)
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
                    "equals": c.get("equals"), "of": c.get("royal_type"),
                    "super": c.get("super")}
        return {
            "hand": [_card(c) for c in p.hand],
            "bag": [_card(c) for c in p.bag],
            "stand_contra": [_card(c) for c in p.stand_contra],
            "black_market_cards": p.black_market_cards,
            "contracts": [dict(ct) for ct in p.contracts],
            "reputation": p.reputation,
            "royal_favor": p.royal_favor,
        }

    def _prompt_for(self, gseat):
        g = self.game
        p = g.players[gseat]
        if g.phase == "MARKET" and gseat in g.order and not g.market_done.get(gseat):
            if not self._discarded.get(gseat):
                return {"kind": "market_discard", "max_discard": min(game.DISCARD_MAX, len(p.hand))}
            return {"kind": "market_draw", "hand": len(p.hand),
                    "draw_left": g.draw_allow.get(gseat, 0)}
        if g.phase == "LOAD" and gseat != g.sheriff and not p.bag_loaded:
            return {"kind": "load_bag"}
        if g.phase == "DECLARE" and gseat in g.order and p.decl is None:
            return {"kind": "declare", "bag_count": len(p.bag)}
        if g.phase == "INSPECT":
            target = g.players[g.inspect_current()]
            if gseat == g.inspect_current() and target.bribe is None:
                return {"kind": "bribe", "gold": target.gold}
            if gseat == g.inspect_current() and target.sheriff_demand is not None:
                return {"kind": "counter_bribe", "owner": target.name,
                        "demand": target.sheriff_demand,
                        "last_offer": target.bribe.get("gold", 0) if target.bribe else 0,
                        "round": target.bribe_round, "max_round": game.BRIBE_MAX_ROUNDS}
            if gseat == g.sheriff and target.bribe is not None and target.sheriff_demand is None:
                return {"kind": "inspect", "owner": target.name,
                        "bribe_gold": target.bribe.get("gold", 0),
                        "bribe_msg": target.bribe.get("msg", ""),
                        "round": target.bribe_round, "max_round": game.BRIBE_MAX_ROUNDS}
        return None

    def _acting_name(self):
        g = self.game
        if g.phase in ("MARKET", "DECLARE"):
            return None  # merchants act simultaneously
        if g.phase == "LOAD":
            return "Waiting for merchants to load bags"
        if g.phase == "INSPECT":
            t = g.inspect_current()
            tp = g.players[t]
            if tp.bribe is None or tp.sheriff_demand is not None:
                return tp.name
            return g.players[g.sheriff].name
        return None

    def _acting_phase(self):
        g = self.game
        if g.phase == "MARKET":
            cur = g.market_current()
            if cur is None or not self._discarded.get(cur):
                return "market_discard"
            return "market_draw"
        if g.phase == "LOAD":
            return "load"
        if g.phase == "DECLARE":
            return "declare"
        if g.phase == "INSPECT":
            tp = g.players[g.inspect_current()]
            if tp.bribe is None:
                return "bribe"
            if tp.sheriff_demand is not None:
                return "counter_bribe"
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
            "route": g.route_type,
            "intel": self._intel_view(g),
            "pot": g.pot,
            "time_left": self._time_left(),
        }
        if g.phase == "GAME_OVER":
            pub["scores"] = g.score()
            pub["bonus_table"] = g.bonus_table()
            pub["prompt"] = None
        else:
            pub["you"] = self._private_view(gseat)
            pub["prompt"] = self._prompt_for(gseat)
        return pub

    def _intel_view(self, g):
        """Sheriff Intel mod: what the sheriff may buy this moment (or None)."""
        try:
            on = bool(game.SHERIFF_INTEL)
        except AttributeError:
            on = False
        if not on or g.phase != "INSPECT":
            return None
        pending = g.order[g.inspect_idx:]
        return {
            "used": bool(g.intel_used),
            "cost": sum(len(g.players[i].bag) for i in pending),
            "available": (len(pending) >= 2 and not g.intel_used),
            "remaining": len(pending),
        }

    def _time_left(self):
        """Seconds left on the current action (Night Market mod) or None."""
        try:
            timeout = game.ACTION_TIMEOUT
        except AttributeError:
            timeout = 0
        if not timeout or self.game is None or self.game.phase in ("LOBBY", "GAME_OVER"):
            return None
        return max(0, int(timeout - (time.time() - self._last_action_ts)))

    def _force_action(self, seat, t, msg):
        """Night Market: auto-play a default action for an idle human player."""
        g = self.game
        s = self.seats[seat]
        gseat = s.get("game_seat")
        if gseat is None:
            return
        if not all(p.connected for p in g.players):
            return  # someone is disconnected: keep waiting for reconnect
        ok = False
        banner = ""
        events = []
        if t == "market_discard":
            ok, banner = g.do_market_discard(gseat, msg.get("cards", []))
        elif t == "market_draw":
            ok, banner = g.do_market_draw(gseat, msg.get("from", "deck"))
            if not ok and banner == "Your hand is already full":
                ok, banner = True, ""
                g.finish_market_turn(gseat)
            elif ok and (len(g.players[gseat].hand) >= game.HAND_SIZE
                         or g.draw_allow.get(gseat, 0) <= 0):
                g.finish_market_turn(gseat)
        elif t == "load_bag":
            ok, banner = g.do_load(gseat, msg.get("cards", []))
        elif t == "declare":
            ok, banner = g.do_declare(gseat, msg.get("type"))
        elif t == "bribe":
            ok, banner = g.do_bribe(gseat, msg.get("gold", 0), "")
        elif t == "counter_response":
            ok, res = g.do_respond_counter(gseat, msg.get("action", "accept"), msg.get("gold", 0))
            if ok:
                events = res
            else:
                banner = res[0] if res else "Action failed"
        elif t == "inspect_decision":
            ok, res = g.do_inspect_decision(gseat, msg.get("action", "pass"))
            if ok:
                events = res
            else:
                banner = res[0] if res else "Action failed"
        if not ok:
            return
        self._last_action_ts = time.time()
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

    def _tick_timeouts(self):
        """Night Market: auto-play default actions when the action timer elapses."""
        while not self.stopped:
            time.sleep(0.5)
            try:
                timeout = game.ACTION_TIMEOUT
            except AttributeError:
                timeout = 0
            if not timeout:
                continue
            with self.lock:
                g = self.game
                if g is None or g.phase in ("LOBBY", "GAME_OVER"):
                    continue
                if time.time() - self._last_action_ts < timeout:
                    continue
                if not all(p.connected for p in g.players):
                    continue
                gseat = None
                if g.phase == "MARKET":
                    pending = [i for i in g.order
                               if not g.market_done.get(i) and not self._is_bot(i)]
                    gseat = pending[0] if pending else None
                elif g.phase == "LOAD":
                    pending = [i for i, p in enumerate(g.players)
                               if i != g.sheriff and not p.bag_loaded and not self._is_bot(i)]
                    gseat = pending[0] if pending else None
                elif g.phase == "DECLARE":
                    pending = [i for i in g.order
                               if g.players[i].decl is None and not self._is_bot(i)]
                    gseat = pending[0] if pending else None
                elif g.phase == "INSPECT":
                    cur = g.inspect_current()
                    p = g.players[cur]
                    if p.bribe is None and not self._is_bot(cur):
                        # merchant did not offer a bribe -> auto no-bribe
                        seat_i = next((i for i, s in enumerate(self.seats)
                                       if s is not None and s.get("game_seat") == cur), None)
                        if seat_i is not None:
                            self._force_action(seat_i, "bribe", {"gold": 0})
                            continue
                    if p.sheriff_demand is not None and not self._is_bot(cur):
                        # merchant must answer the sheriff's counter-offer -> auto accept
                        seat_i = next((i for i, s in enumerate(self.seats)
                                       if s is not None and s.get("game_seat") == cur), None)
                        if seat_i is not None:
                            self._force_action(seat_i, "counter_response",
                                               {"action": "accept", "gold": 0})
                            continue
                    if p.bribe is not None and p.sheriff_demand is None and not self._is_bot(g.sheriff):
                        gseat = g.sheriff
                if gseat is None:
                    continue
                seat = next((i for i, s in enumerate(self.seats)
                             if s is not None and s.get("game_seat") == gseat), None)
                if seat is None:
                    continue
                if g.phase == "MARKET":
                    if not self._discarded.get(gseat):
                        self._force_action(seat, "market_discard", {"cards": []})
                    elif g.draw_allow.get(gseat, 0) <= 0:
                        g.finish_market_turn(gseat)
                        self._last_action_ts = time.time()
                        self._broadcast_views()
                        self._drive_bots()
                    else:
                        self._force_action(seat, "market_draw", {"from": "deck"})
                elif g.phase == "LOAD":
                    hand = g.players[gseat].hand
                    idx = [i for i, c in enumerate(hand)
                           if not game.is_contraband(c)]
                    pick = idx[:1] if idx else [0]
                    self._force_action(seat, "load_bag", {"cards": pick})
                elif g.phase == "DECLARE":
                    bag = g.players[gseat].bag
                    counts = {}
                    for c in bag:
                        if c["type"] in game.LEGAL:
                            counts[c["type"]] = counts.get(c["type"], 0) + 1
                    ctype = (max(counts, key=counts.get) if counts
                             else g.rng.choice(game.LEGAL))
                    self._force_action(seat, "declare", {"type": ctype})
                elif g.phase == "INSPECT":
                    self._force_action(seat, "inspect_decision", {"action": "pass"})
            # release the lock before the next loop iteration

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

    def __init__(self, host, port, name, rules=None, avatar=None):
        self.name = name
        self.sock = socket.create_connection((host, port), timeout=10)
        self.sock.settimeout(None)
        self.q = queue.Queue()
        self.send_lock = threading.Lock()
        self.alive = True
        if rules is None:
            import mods  # local import avoids a net->mods->gui->net cycle
            rules = mods.rules_mods()
        if avatar is None:
            avatar = profile.avatar_payload(profile.load_profile())
        self.send({"t": "hello", "name": name, "mods": rules, "avatar": avatar,
                         "ver": version.__version__})
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
