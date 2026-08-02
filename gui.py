# -*- coding: utf-8 -*-
"""pygame UI (minimal button-only version, EN/Chinese bilingual)."""

import os
import sys
import time

import pygame

import game
import gfx
import lang
import mods
import net

W, H = 1280, 800
COLOR_BG = (42, 36, 30)
COLOR_PANEL = (72, 60, 46)
COLOR_BTN = (112, 94, 68)
COLOR_BTN_HOVER = (142, 120, 86)
COLOR_BTN_DIS = (72, 64, 54)
COLOR_TEXT = (236, 226, 206)
COLOR_ACCENT = (222, 172, 62)
COLOR_DIM = (150, 140, 122)
COLOR_RED = (205, 92, 72)
COLOR_GREEN = (116, 182, 116)
COLOR_GOLD = (226, 168, 52)
COLOR_CONTRA_TEXT = (208, 128, 96)
COLOR_SELECT = (250, 250, 250)
COLOR_BORDER_LEGAL = (84, 138, 92)
COLOR_BORDER_CONTRA = (186, 74, 64)
COLOR_BORDER_ROYAL = (226, 168, 52)

TYPE_COLOR = {
    "APPLE": (156, 72, 62),
    "CHEESE": (172, 142, 58),
    "BREAD": (156, 116, 74),
    "CHICKEN": (178, 104, 52),
    "SILK": (150, 84, 148),
    "CROSSBOW": (92, 104, 128),
    "COFFEE": (120, 96, 66),
    "WINE": (140, 60, 90),
    "ROYAL_GREEN_APPLE": (112, 52, 45),
    "ROYAL_GOLD_APPLE": (150, 105, 40),
    "ROYAL_GOUDA_CHEESE": (124, 102, 42),
    "ROYAL_BLUE_CHEESE": (84, 98, 128),
    "ROYAL_RYE_BREAD": (112, 84, 53),
    "ROYAL_COARSE_BREAD": (96, 72, 46),
    "ROYAL_CHICKEN": (128, 75, 37),
    "BLACK_MARKET": (222, 172, 62),
}

_FONT_CACHE = {}
_SYS_FONT_PATHS = [
    r"C:\Windows\Fonts\msyh.ttc",       # Microsoft YaHei
    r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\simhei.ttf",     # SimHei
    r"C:\Windows\Fonts\simsun.ttc",     # SimSun
    r"C:\Windows\Fonts\Deng.ttf",       # DengXian
    r"C:\Windows\Fonts\msyhl.ttc",
    "/System/Library/Fonts/PingFang.ttc",          # macOS
    "/System/Library/Fonts/STHeiti Light.ttc",     # macOS
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",   # Linux
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",           # Linux
]

_FONT_FILES = ["NotoSansCJKsc-Regular.otf", "msyh.ttc", "msyhbd.ttc"]


def _font_candidates():
    cands = []
    base_dirs = []
    meipass = getattr(sys, "_MEIPASS", None)  # PyInstaller extraction directory
    if meipass:
        base_dirs.append(meipass)
    base_dirs.append(os.path.dirname(os.path.abspath(__file__)))
    for d in base_dirs:
        for name in _FONT_FILES:
            cands.append(os.path.join(d, "assets", name))
    cands += _SYS_FONT_PATHS
    return [p for p in cands if os.path.exists(p)]


def get_font(size):
    if size in _FONT_CACHE:
        return _FONT_CACHE[size]
    f = None
    for p in _font_candidates():
        try:
            f = pygame.font.Font(p, size)
            break
        except Exception:
            continue
    if f is None:
        try:
            f = pygame.font.SysFont("arial", size)
        except Exception:
            f = pygame.font.Font(None, size)
    _FONT_CACHE[size] = f
    return f


class Button:
    def __init__(self, rect, text, cb=None, enabled=True, highlight=False,
                 bg=None, border=None, value=None, sub=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.cb = cb
        self.enabled = enabled
        self.highlight = highlight
        self.bg = bg          # fill color override (per-type card tint)
        self.border = border  # border color override (contraband frame)
        self.value = value    # big number near the top (card value)
        self.sub = sub        # small bottom hint (fine / contraband tag)

    def handle(self, ev):
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.enabled and self.rect.collidepoint(ev.pos):
                if self.cb:
                    self.cb()
                return True
        return False

    def draw(self, surf):
        hover = self.enabled and self.rect.collidepoint(pygame.mouse.get_pos())
        if self.bg is not None:
            if hover and self.enabled:
                color = tuple(min(255, c + 26) for c in self.bg)
            elif not self.enabled:
                color = tuple(max(40, c - 30) for c in self.bg)
            else:
                color = self.bg
        else:
            color = COLOR_BTN_HOVER if (hover and self.enabled) else (COLOR_BTN if self.enabled else COLOR_BTN_DIS)
        pygame.draw.rect(surf, color, self.rect, border_radius=6)
        if self.highlight:
            pygame.draw.rect(surf, COLOR_SELECT, self.rect.inflate(10, 10), 4, border_radius=11)
        if self.border is not None:
            pygame.draw.rect(surf, self.border, self.rect, 3, border_radius=6)
        else:
            pygame.draw.rect(surf, (30, 24, 18), self.rect, 1, border_radius=6)
        if self.border == COLOR_BORDER_ROYAL:
            pygame.draw.rect(surf, COLOR_BORDER_ROYAL, self.rect.inflate(-8, -8), 1, border_radius=5)
        txt = COLOR_TEXT if self.enabled else COLOR_DIM
        cy = self.rect.centery
        if self.value is not None:
            t = get_font(26).render(str(self.value), True, txt)
            surf.blit(t, t.get_rect(center=(self.rect.centerx, self.rect.y + 32)))
            cy += 16
        t = get_font(17).render(self.text, True, txt)
        surf.blit(t, t.get_rect(center=(self.rect.centerx, cy)))
        if self.sub:
            t = get_font(13).render(self.sub, True, COLOR_DIM)
            surf.blit(t, t.get_rect(center=(self.rect.centerx, self.rect.bottom - 12)))


class TextInput:
    def __init__(self, rect, placeholder=""):
        self.rect = pygame.Rect(rect)
        self.text = ""
        self.placeholder = placeholder
        self.active = False

    def handle(self, ev):
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            self.active = self.rect.collidepoint(ev.pos)
            return False
        if not self.active:
            return False
        if ev.type == pygame.TEXTINPUT:
            self.text += ev.text
            return False
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif ev.key == pygame.K_RETURN:
                return "submit"
            elif ev.key == pygame.K_v and (ev.mod & pygame.KMOD_CTRL):
                self.text += self._clipboard_text()
        return False

    @staticmethod
    def _clipboard_text():
        try:
            raw = pygame.scrap.get(pygame.SCRAP_TEXT)
            if raw:
                for enc in ("utf-8", "utf-16-le", "gbk"):
                    try:
                        return raw.decode(enc).replace("\x00", "")
                    except (UnicodeDecodeError, ValueError):
                        continue
        except Exception:
            pass
        return ""

    def draw(self, surf):
        pygame.draw.rect(surf, (30, 24, 18), self.rect, border_radius=4)
        pygame.draw.rect(surf, COLOR_ACCENT if self.active else COLOR_DIM, self.rect, 1, border_radius=4)
        txt = self.text if self.text else self.placeholder
        t = get_font(18).render(txt, True, COLOR_TEXT if self.text else COLOR_DIM)
        surf.blit(t, (self.rect.x + 6, self.rect.centery - t.get_height() // 2))


class App:
    def __init__(self, host=False, players=4, port=net.DEFAULT_PORT, name="", join="",
                 lang_name="zh", royal=True, black_market=True,
                 mod_names=None, mod_errors=None, mod_list=None):
        pygame.init()
        pygame.display.set_caption(lang.UI.get(lang_name, lang.UI["zh"])["title"])
        self.screen = pygame.display.set_mode((W, H))
        try:
            icon_path = gfx.asset_path("icon.png")
            if icon_path:
                pygame.display.set_icon(pygame.image.load(icon_path))
        except Exception:
            pass
        self.clock = pygame.time.Clock()
        try:
            pygame.scrap.init()  # clipboard support
        except Exception:
            pass
        pygame.key.start_text_input()  # IME text input (Chinese support)
        self.lang = lang_name if lang_name in lang.UI else "zh"
        self.server = None
        self.client = None
        self.my_seat = None
        self.is_host = False
        self.host_addr = None
        self.name = name or self._t("default_name")
        self.port = port
        self.players = max(2, min(5, players))
        self.royal = royal
        self.black_market = black_market
        self.screen_name = "menu"
        self.view = None
        self.lobby = None
        self.chat_log = []
        self.banners = []
        self.selected = set()
        self.decl_type = None
        self.disconnected = False
        self.closed = False
        self._last_reconnect = 0
        self.reconnect_tries = 0
        self.done = False
        self.server_info = []   # list of (ui_key, kwargs) rendered per language
        self.menu_note = ""
        self.mod_names = list(mod_names or [])
        self.mod_errors = list(mod_errors or [])
        self.mod_list = list(mod_list or [])
        self.mods_toast = ""
        for err in self.mod_errors:
            self._append_chat(self._t("mods_error", s=err), COLOR_RED)
        if self.mod_names:
            self._append_chat(self._t("mods_line", s=", ".join(self.mod_names)), COLOR_GOLD)

        self.name_input = TextInput((300, 180, 300, 36), self._t("ph_name"))
        self.players_input = TextInput((300, 240, 300, 36), self._t("ph_players"))
        self.join_input = TextInput((300, 300, 300, 36), self._t("ph_join"))
        self.rounds_input = TextInput((W // 2 - 260, 545, 110, 36), self._t("ph_rounds"))
        self.lobby_rename_input = TextInput((W // 2 - 260, 480, 200, 36), self._t("ph_name"))
        self.chat_input = TextInput((910, 730, 250, 30), self._t("ph_chat"))
        self.gold_input = TextInput((40, 668, 110, 32), self._t("ph_gold"))
        self.msg_input = TextInput((170, 668, 300, 32), self._t("ph_note"))
        self.buttons = []
        self.hand_buttons = []

        if self.name and self.name != self._t("default_name"):
            self.name_input.text = self.name
        self.players_input.text = str(self.players)
        if host:
            self._create_room(self.players, port, self.name)
        elif join:
            self.join_input.text = join
            self._join_room()

    # ---------- Utilities ----------

    def _t(self, key, **kw):
        s = lang.UI[self.lang][key]
        return s.format(**kw) if kw else s

    def _tn(self, t):
        return lang.tname(t, self.lang)

    def _msg(self, text):
        return lang.translate(text, self.lang)

    def _append_chat(self, text, color=None):
        self.chat_log.append((text, color))
        self.chat_log = self.chat_log[-80:]

    def _send(self, obj):
        if self.client:
            self.client.send(obj)

    def _parse_int(self, s, default=0):
        try:
            return int(s.strip())
        except ValueError:
            return default

    def _toggle_hand(self, i):
        if i in self.selected:
            self.selected.discard(i)
        else:
            self.selected.add(i)
        self._rebuild_game_ui()

    def _copy_text(self, text):
        try:
            pygame.scrap.put(pygame.SCRAP_TEXT, text.encode("utf-8"))
            return True
        except Exception:
            return False

    def _set_lang(self, lng):
        if lng not in lang.UI:
            return
        self.lang = lng
        self.name_input.placeholder = self._t("ph_name")
        self.players_input.placeholder = self._t("ph_players")
        self.join_input.placeholder = self._t("ph_join")
        self.chat_input.placeholder = self._t("ph_chat")
        self.gold_input.placeholder = self._t("ph_gold")
        self.msg_input.placeholder = self._t("ph_note")
        self.rounds_input.placeholder = self._t("ph_rounds")
        self.lobby_rename_input.placeholder = self._t("ph_name")
        pygame.display.set_caption(self._t("title"))
        if self.screen_name == "menu":
            self._rebuild_menu_ui()
        elif self.screen_name == "mods":
            self._rebuild_mods_ui()
        elif self.screen_name == "lobby":
            self._rebuild_lobby_ui()
        elif self.screen_name == "game":
            self._rebuild_game_ui()

    # ---------- Room ----------

    def _create_room(self, players, port, name):
        self.server = net.GameServer(players, port=port, royal=self.royal,
                                     black_market=self.black_market)
        self.host_addr = ("127.0.0.1", port)
        self.name = name or self._t("default_name")
        self.server_info = [
            ("room_created", {"n": players}),
            ("lan_addr", {"addr": f"{self.server.local_ip}:{port}"}),
            ("online_1", {}),
            ("online_2", {"port": port}),
        ]
        self._append_chat(self._t("room_created_chat", port=port))
        self._connect(self.name)

    def _join_room(self):
        addr = self.join_input.text.strip()
        if not addr:
            return
        if ":" in addr:
            h, _, p = addr.rpartition(":")
            try:
                port = int(p)
            except ValueError:
                port = net.DEFAULT_PORT
        else:
            h, port = addr, net.DEFAULT_PORT
        self.host_addr = (h.strip(), port)
        self._connect(self.name_input.text.strip() or self._t("default_name"))

    def _connect(self, name):
        try:
            self.name = name
            self.client = net.GameClient(self.host_addr[0], self.host_addr[1], name)
            self.screen_name = "lobby"
            self._append_chat(self._t("connected"))
        except OSError as e:
            self._append_chat(self._t("conn_failed", e=e), COLOR_RED)

    # ---------- Events ----------

    def handle_event(self, ev):
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
            self.done = True
            return
        if self.screen_name == "menu":
            self.name_input.handle(ev)
            self.players_input.handle(ev)
            self.join_input.handle(ev)
            for b in self.buttons:
                b.handle(ev)
        elif self.screen_name == "lobby":
            self.lobby_rename_input.handle(ev)
            self.rounds_input.handle(ev)
            for b in self.buttons:
                b.handle(ev)
        elif self.screen_name == "mods":
            for b in self.buttons:
                b.handle(ev)
        elif self.screen_name == "game":
            for b in self.buttons:
                b.handle(ev)
            for b in self.hand_buttons:
                b.handle(ev)
            if self.chat_input.handle(ev) == "submit":
                self._send_chat()
            prompt = (self.view or {}).get("prompt") or {}
            if prompt.get("kind") == "bribe":
                self.gold_input.handle(ev)
                self.msg_input.handle(ev)
        elif self.screen_name == "over":
            for b in self.buttons:
                b.handle(ev)

    def _send_chat(self):
        text = self.chat_input.text.strip()
        if text:
            self._send({"t": "chat", "msg": text[:200]})
            self.chat_input.text = ""

    def _quick_chat(self, text):
        self._send({"t": "chat", "msg": text})

    # ---------- Network message handling ----------

    def process_client_msgs(self):
        if not self.client:
            return
        for m in self.client.poll():
            t = m.get("t")
            if t == "welcome":
                self.my_seat = m.get("seat")
                self.is_host = bool(m.get("host"))
            elif t == "lobby":
                self.lobby = m
                self.screen_name = "lobby"
                self._rebuild_lobby_ui()
            elif t == "game_start":
                self._append_chat(self._msg(m.get("msg", "Game started!")), COLOR_ACCENT)
            elif t == "view":
                prev = self.view or {}
                prev_kind = (prev.get("prompt") or {}).get("kind")
                new_kind = (m.get("prompt") or {}).get("kind")
                if new_kind != prev_kind or m.get("round") != prev.get("round") or new_kind is None:
                    self.selected = set()
                    self.decl_type = None
                self.view = m
                if m.get("phase") == "GAME_OVER":
                    self.screen_name = "over"
                    self._rebuild_over_ui()
                else:
                    self.screen_name = "game"
                    self._rebuild_game_ui()
            elif t == "banner":
                self._append_chat("◆ " + self._msg(m.get("msg", "")), COLOR_ACCENT)
            elif t == "chat":
                self._append_chat(f"{m['from']}: {m['msg']}")
            elif t == "status":
                color = COLOR_RED if "disconnected" in m.get("msg", "") else COLOR_DIM
                self._append_chat("⚑ " + self._msg(m.get("msg", "")), color)
            elif t == "error":
                self._append_chat("✗ " + self._msg(m.get("msg", "")), COLOR_RED)
            elif t == "server_closed":
                self.closed = True
                self.disconnected = True
                self._append_chat(self._msg(m.get("msg", "") or self._t("room_closed")), COLOR_RED)
                self.screen_name = "over"
                self._rebuild_over_ui()
        if self.disconnected and not self.closed and self.host_addr and not self.done:
            now = time.time()
            if now - self._last_reconnect > 3:
                self._last_reconnect = now
                self._try_reconnect()

    def _try_reconnect(self):
        try:
            c = net.GameClient(self.host_addr[0], self.host_addr[1], self.name)
            if self.client:
                self.client.close()
            self.client = c
            self.disconnected = False
            self.reconnect_tries = 0
            self._append_chat(self._t("reconnected_wait"), COLOR_GREEN)
        except OSError:
            self.reconnect_tries += 1
            if self.reconnect_tries % 3 == 0:
                self._append_chat(self._t("reconnect_failed"), COLOR_DIM)

    # ---------- UI building ----------

    def _rebuild_menu_ui(self):
        self.buttons = [
            Button((300, 380, 150, 44), self._t("btn_create"), self._create_room_click),
            Button((470, 380, 150, 44), self._t("btn_join"), self._join_room),
            Button((640, 380, 100, 44), self._t("btn_quit"), lambda: setattr(self, "done", True)),
            Button((300, 440, 150, 44), self._t("btn_mods"), self._open_mods),
            Button((610, 300, 90, 36), self._t("btn_paste"), self._paste_join),
            Button((W - 170, 20, 140, 40), self._t("btn_lang"), self._toggle_lang),
        ]

    def _toggle_lang(self):
        self._set_lang("en" if self.lang == "zh" else "zh")

    def _paste_join(self):
        txt = TextInput._clipboard_text().strip()
        if txt:
            self.join_input.text = txt
            self.menu_note = self._t("paste_done", addr=txt)
        else:
            self.menu_note = ""

    def _copy_lan(self):
        addr = f"{self.server.local_ip}:{self.port}" if self.server else ""
        if addr:
            if self._copy_text(addr):
                self._append_chat(self._t("copied", addr=addr), COLOR_GREEN)
            else:
                self._append_chat(self._t("conn_failed", e="clipboard"), COLOR_RED)

    def _create_room_click(self):
        name = self.name_input.text.strip() or self._t("default_name")
        players = self._parse_int(self.players_input.text, 4)
        players = max(2, min(5, players))
        self._create_room(players, self.port, name)

    def _rebuild_lobby_ui(self):
        self.buttons = []
        info = self.lobby or {}
        joined = info.get("joined", [])
        can_start = bool(info.get("can_start")) and self.is_host
        if self.is_host and not self.rounds_input.text.strip():
            n = max(len(joined), 2)
            self.rounds_input.text = str(n * (3 if n == 3 else 2))
        if not self.lobby_rename_input.text.strip() and self.name:
            self.lobby_rename_input.text = self.name
        bots = [j for j in joined if j.get("bot")]
        if self.is_host:
            self.buttons.append(Button((W // 2 - 130, 610, 260, 46), self._t("btn_start"),
                                       self._start_game_click, enabled=can_start))
            self.buttons.append(Button((W // 2 - 130, 665, 260, 44), self._t("btn_copy"), self._copy_lan))
            bx = W // 2 + 120
            can_add = len(joined) < int(info.get("max_players", 9))
            self.buttons.append(Button((bx, 350, 180, 36), self._t("btn_add_easy"),
                                       lambda: self._add_bot("easy"), enabled=can_add))
            self.buttons.append(Button((bx, 394, 180, 36), self._t("btn_add_normal"),
                                       lambda: self._add_bot("normal"), enabled=can_add))
            self.buttons.append(Button((bx, 438, 180, 36), self._t("btn_add_hard"),
                                       lambda: self._add_bot("hard"), enabled=can_add))
            self.buttons.append(Button((bx, 482, 180, 36), self._t("btn_remove_bot"),
                                       self._remove_bot_click, enabled=bool(bots)))
        self.buttons.append(Button((W // 2 - 130, 610 if not self.is_host else 720, 260, 44),
                                   self._t("btn_leave"), lambda: setattr(self, "done", True)))
        self.buttons.append(Button((W // 2 - 50, 480, 120, 40), self._t("btn_rename"), self._rename_click))
        self.buttons.append(Button((W - 170, 20, 140, 40), self._t("btn_lang"), self._toggle_lang))

    def _start_game_click(self):
        r = self._parse_int(self.rounds_input.text, 0)
        self._send({"t": "start_game", "rounds": r if r >= 2 else None})

    def _rename_click(self):
        new = self.lobby_rename_input.text.strip()
        if new:
            self._send({"t": "rename", "name": new})
            self.name = new
            self.lobby_rename_input.text = ""
            self._append_chat(self._t("rename_done", name=new), COLOR_GREEN)

    def _add_bot(self, level):
        self._send({"t": "add_bot", "level": level})

    def _remove_bot_click(self):
        joined = (self.lobby or {}).get("joined", [])
        bots = [j for j in joined if j.get("bot")]
        if bots:
            self._send({"t": "remove_bot", "seat": bots[-1]["seat"]})

    def _rebuild_game_ui(self):
        self.buttons = []
        self.hand_buttons = []
        v = self.view or {}
        prompt = v.get("prompt") or {}
        kind = prompt.get("kind")
        you = v.get("you") or {}
        hand = you.get("hand", [])

        sel_enabled = kind in ("market_discard", "load_bag")
        # Hand buttons
        for i, c in enumerate(hand):
            rect = pygame.Rect(40 + (i % 6) * 132, 470 + (i // 6) * 116, 124, 104)
            sel = i in self.selected
            ct = c["type"]
            royal = ct in game.ROYAL_TYPES
            contra = ct in game.CONTRABAND or royal
            if royal:
                eq = c.get("equals") or game.ROYAL_GOODS.get(ct, {}).get("equals", 2)
                of = self._tn(c.get("of") or game.ROYAL_TYPE_OF.get(ct, ""))
                label = "★ " + self._tn(ct)
                sub = (self._t("royal_tag") + f"={eq}" + of + " · " +
                       self._t("ctag_fine", f=c.get("fine", c["value"])))
            elif contra:
                label = self._tn(ct)
                sub = self._t("ctag") + " · " + self._t("ctag_fine", f=c.get("fine", c["value"]))
            else:
                label = self._tn(ct)
                sub = self._t("fine_tag", f=c.get("fine", c["value"]))
            if royal:
                border = COLOR_BORDER_ROYAL
            elif contra:
                border = COLOR_BORDER_CONTRA
            else:
                border = COLOR_BORDER_LEGAL
            b = Button(rect, label, lambda i=i: self._toggle_hand(i), sel_enabled, sel,
                       bg=TYPE_COLOR.get(ct), border=border,
                       value=c["value"], sub=sub)
            self.hand_buttons.append(b)

        # Quick chat (left side, below buttons; hidden during bribe)
        kind = prompt.get("kind")
        if kind != "bribe":
            for i, ph in enumerate(lang.UI[self.lang]["phrases"]):
                x = 40 + (i % 2) * 190
                y = 668 + (i // 2) * 36
                self.buttons.append(Button((x, y, 182, 30), ph, lambda ph=ph: self._quick_chat(ph)))

        kind = prompt.get("kind")
        if kind == "market_discard":
            self.buttons.append(Button((40, 620, 160, 42), self._t("btn_discard_sel"),
                                       lambda: self._market_discard()))
            self.buttons.append(Button((215, 620, 200, 42), self._t("btn_discard_0"),
                                       lambda: self._market_discard(empty=True)))
        elif kind == "market_draw":
            self.buttons.append(Button((40, 610, 230, 42),
                                       self._t("btn_deck", n=v.get("deck_count", 0)),
                                       lambda: self._market_draw("deck")))
            self.buttons.append(Button((285, 610, 150, 42), self._t("btn_stop_draw"),
                                       lambda: self._send({"t": "market_done"})))
        elif kind == "load_bag":
            n = len(self.selected)
            self.buttons.append(Button((40, 610, 240, 42), self._t("btn_seal", n=n),
                                       lambda: self._load_bag(), enabled=1 <= n <= 5))
        elif kind == "declare":
            n_leg = len(game.LEGAL)
            step = min(150, (W - 80) // max(n_leg + 1, 1))
            for i, t in enumerate(game.LEGAL):
                self.buttons.append(Button((40 + i * step, 610, step - 10, 42), self._tn(t),
                                           lambda t=t: self._pick_decl(t), highlight=self.decl_type == t))
            self.buttons.append(Button((40 + n_leg * step, 610, 220, 42),
                                       self._t("btn_confirm_decl", n=prompt.get("bag_count", 0)),
                                       lambda: self._do_declare(), enabled=self.decl_type is not None))
        elif kind == "bribe":
            self.buttons.append(Button((40, 610, 150, 42), self._t("btn_submit_bribe"), lambda: self._do_bribe()))
            self.buttons.append(Button((205, 610, 130, 42), self._t("btn_no_bribe"), lambda: self._do_bribe(none=True)))
        elif kind == "inspect":
            self.buttons.append(Button((40, 610, 150, 42), self._t("btn_pass"),
                                       lambda: self._inspect_decision("pass")))
            self.buttons.append(Button((205, 610, 150, 42), self._t("btn_inspect"),
                                       lambda: self._inspect_decision("inspect")))

        # Black market reward submit buttons (next to each task, grayed until claimable)
        bm = v.get("black_market")
        if bm and bm.get("types"):
            types = bm.get("types") or []
            claimed = bm.get("claimed") or {}
            need = bm.get("need") or game.BLACK_MARKET_NEED
            prog = bm.get("progress") or {}
            mine = {}
            if self.my_seat is not None:
                mine = (prog.get(self.my_seat) or prog.get(str(self.my_seat)) or {})
            for i, t_ in enumerate(types):
                ry = 292 + i * 44
                for slot in range(claimed.get(t_, 0), 2):
                    can = (slot == claimed.get(t_, 0) and (mine.get(t_, 0) or 0) >= need)
                    self.buttons.append(Button(
                        (250 + slot * 280, ry, 96, 22),
                        self._t("bm_submit"),
                        lambda t_=t_, slot=slot: self._bm_submit(t_, slot),
                        enabled=can))
        if self.is_host and not self.disconnected:
            self.buttons.append(Button((W - 170, 8, 160, 40), self._t("btn_close_room"),
                                       lambda: self._send({"t": "host_quit"})))
        if self.disconnected:
            self.buttons.append(Button((40, 700, 260, 36), self._t("btn_reconnecting"), enabled=False))

    def _market_discard(self, empty=False):
        cards = [] if empty else sorted(self.selected)
        self._send({"t": "market_discard", "cards": cards})
        self.selected = set()

    def _market_draw(self, src):
        self._send({"t": "market_draw", "from": src})

    def _load_bag(self):
        cards = sorted(self.selected)
        if 1 <= len(cards) <= 5:
            self._send({"t": "load_bag", "cards": cards})
            self.selected = set()

    def _bm_submit(self, t_, slot):
        self._send({"t": "black_market_submit", "type": t_, "slot": slot})

    def _pick_decl(self, t):
        self.decl_type = t
        self._rebuild_game_ui()

    def _do_declare(self):
        if self.decl_type:
            self._send({"t": "declare", "type": self.decl_type})
            self.decl_type = None

    def _do_bribe(self, none=False):
        if none:
            self._send({"t": "bribe", "gold": 0, "msg": ""})
        else:
            gold = self._parse_int(self.gold_input.text)
            msg = self.msg_input.text.strip()
            self._send({"t": "bribe", "gold": gold, "msg": msg})
        self.gold_input.text = ""
        self.msg_input.text = ""

    def _inspect_decision(self, action):
        self._send({"t": "inspect_decision", "action": action})

    def _rebuild_over_ui(self):
        if self.closed:
            self.buttons = [Button((W // 2 - 100, 660, 200, 46), self._t("btn_close"),
                                   lambda: setattr(self, "done", True))]
        else:
            self.buttons = [
                Button((W // 2 - 210, 660, 200, 46), self._t("btn_back_room"),
                       lambda: self._send({"t": "back_to_lobby"})),
                Button((W // 2 + 10, 660, 200, 46), self._t("btn_quit"),
                       lambda: setattr(self, "done", True)),
            ]

    # ---------- Mods management ----------

    def _open_mods(self):
        self.screen_name = "mods"
        self._refresh_mods()

    def _refresh_mods(self):
        self.mod_list = mods.list_all_mods()
        self.mods_toast = ""
        self._rebuild_mods_ui()

    def _toggle_mod(self, mod_id):
        info = next((m for m in self.mod_list if m["id"] == mod_id), None)
        if info is None:
            return
        ok = mods.set_enabled(mod_id, not info["enabled"])
        self.mods_toast = self._t("mods_saved" if ok else "mods_save_failed")
        self.mod_list = mods.list_all_mods()
        self._rebuild_mods_ui()

    def _back_to_menu(self):
        self.screen_name = "menu"
        self._rebuild_menu_ui()

    def _rebuild_mods_ui(self):
        self.buttons = []
        for i, m in enumerate(self.mod_list[:7]):
            label = self._t("mods_disable" if m["enabled"] else "mods_enable")
            self.buttons.append(Button((1040, 138 + i * 80, 150, 36), label,
                                       lambda mid=m["id"]: self._toggle_mod(mid)))
        self.buttons.append(Button((60, 700, 150, 44), self._t("btn_back"),
                                   self._back_to_menu))
        self.buttons.append(Button((230, 700, 150, 44), self._t("mods_refresh"),
                                   self._refresh_mods))

    def _draw_mods(self):
        title = get_font(36).render(self._t("mods_title"), True, COLOR_ACCENT)
        self.screen.blit(title, title.get_rect(center=(W // 2, 60)))
        hint = get_font(15).render(self._t("mods_hint"), True, COLOR_DIM)
        self.screen.blit(hint, hint.get_rect(center=(W // 2, 94)))
        mlist = self.mod_list
        if not mlist:
            t = get_font(20).render(self._t("mods_none"), True, COLOR_TEXT)
            self.screen.blit(t, (60, 140))
        y = 126
        for i, m in enumerate(mlist[:7]):
            pygame.draw.rect(self.screen, COLOR_PANEL, (60, y, 1160, 72), border_radius=8)
            state = self._t("mods_on" if m["enabled"] else "mods_off")
            t = get_font(20).render("{0}  v{1}   {2}".format(m["name"], m["version"], state),
                                    True, COLOR_GOLD if m["enabled"] else COLOR_TEXT)
            self.screen.blit(t, (80, y + 8))
            if m["description"]:
                d = get_font(15).render(m["description"], True, COLOR_DIM)
                self.screen.blit(d, (80, y + 38))
            y += 80
        if len(mlist) > 7:
            t = get_font(15).render(self._t("mods_more", n=len(mlist) - 7),
                                    True, COLOR_DIM)
            self.screen.blit(t, (60, y + 6))
        if self.mod_errors:
            t = get_font(15).render(self._t("mods_errors", s="; ".join(self.mod_errors)),
                                    True, COLOR_RED)
            self.screen.blit(t, (60, 636))
        if self.mods_toast:
            t = get_font(15).render(self.mods_toast, True, COLOR_GREEN)
            self.screen.blit(t, (60, 664))
        for b in self.buttons:
            b.draw(self.screen)

    # ---------- Drawing ----------

    def draw(self):
        self.screen.fill(COLOR_BG)
        if self.screen_name == "menu":
            self._draw_menu()
        elif self.screen_name == "mods":
            self._draw_mods()
        elif self.screen_name == "lobby":
            self._draw_lobby()
        elif self.screen_name == "game":
            self._draw_game()
        elif self.screen_name == "over":
            self._draw_over()

    def _draw_menu(self):
        title = get_font(44).render(self._t("title"), True, COLOR_ACCENT)
        self.screen.blit(gfx.title_logo(56),
                         (W // 2 - title.get_width() // 2 - 76, 100 - 30))
        self.screen.blit(title, title.get_rect(center=(W // 2, 100)))
        sub = get_font(20).render(self._t("subtitle"), True, COLOR_DIM)
        self.screen.blit(sub, sub.get_rect(center=(W // 2, 142)))
        if self.mod_names:
            t = get_font(16).render(self._t("mods_line", s=", ".join(self.mod_names)),
                                    True, COLOR_GOLD)
            self.screen.blit(t, t.get_rect(center=(W // 2, 176)))
        if self.mod_errors:
            t = get_font(15).render(self._t("mods_error", s="; ".join(self.mod_errors)),
                                    True, COLOR_RED)
            self.screen.blit(t, t.get_rect(center=(W // 2, 200)))
        for lbl, inp in [(self._t("lbl_name"), self.name_input),
                         (self._t("lbl_players"), self.players_input),
                         (self._t("lbl_join"), self.join_input)]:
            t = get_font(20).render(lbl, True, COLOR_TEXT)
            self.screen.blit(t, (160, inp.rect.y - 26))
            inp.draw(self.screen)
        if self.menu_note:
            t = get_font(16).render(self.menu_note, True, COLOR_DIM)
            self.screen.blit(t, (160, 344))
        for b in self.buttons:
            b.draw(self.screen)

    def _draw_lobby(self):
        title = get_font(36).render(self._t("lobby_title"), True, COLOR_ACCENT)
        self.screen.blit(title, title.get_rect(center=(W // 2, 70)))
        info = self.lobby or {}
        joined = info.get("joined", [])
        for i, j in enumerate(joined):
            tag = self._t("host_tag") if j.get("host") else ""
            if j.get("bot"):
                tag += self._t("bot_tag", l=self._t("lvl_" + str(j["bot"]))) + " "
            t = get_font(24).render(f"{i + 1}. {tag}{j['name']}", True, COLOR_TEXT)
            self.screen.blit(t, (W // 2 - 200, 120 + i * 40))
        cnt = self._t("joined", n=len(joined), m=info.get("max_players", "?"))
        t = get_font(20).render(cnt, True, COLOR_DIM)
        self.screen.blit(t, (W // 2 - 200, 120 + max(len(joined), 1) * 40 + 8))
        y = 320
        for idx, (key, kw) in enumerate(self.server_info):
            t = get_font(18).render(self._t(key, **kw), True, COLOR_DIM)
            self.screen.blit(t, (W // 2 - 200, y + idx * 24))
            y2 = y + idx * 24 + 24
        hint = get_font(15).render(self._t("rule_hint"), True, COLOR_GOLD)
        self.screen.blit(hint, (W // 2 - 200, y + len(self.server_info) * 24 + 6))
        # rename
        t = get_font(18).render(self._t("lbl_name"), True, COLOR_TEXT)
        self.screen.blit(t, (W // 2 - 260, 446))
        self.lobby_rename_input.draw(self.screen)
        # rounds (host only)
        if self.is_host:
            t = get_font(18).render(self._t("lbl_rounds"), True, COLOR_TEXT)
            self.screen.blit(t, (W // 2 - 260, 512))
            self.rounds_input.draw(self.screen)
            t = get_font(20).render(self._t("bots_title"), True, COLOR_ACCENT)
            self.screen.blit(t, (W // 2 + 120, 300))
            t = get_font(14).render(self._t("bots_hint"), True, COLOR_DIM)
            self.screen.blit(t, (W // 2 + 120, 326))
        for b in self.buttons:
            b.draw(self.screen)

    def _draw_stall(self, surf, x, y, legal_counts, contra_text):
        px = x
        prefix = get_font(15).render(self._t("stall"), True, COLOR_DIM)
        surf.blit(prefix, (px, y))
        px += prefix.get_width()
        for k, n in (legal_counts or {}).items():
            t = get_font(15).render(f"{self._tn(k)}x{n} ", True, TYPE_COLOR.get(k, COLOR_TEXT))
            surf.blit(t, (px, y))
            px += t.get_width()
        if contra_text:
            t = get_font(15).render(contra_text, True, COLOR_CONTRA_TEXT)
            surf.blit(t, (px, y))

    def _draw_game(self):
        v = self.view or {}
        phase = lang.PHASES[self.lang].get(v.get("phase"), "?")
        sheriff_name = (v.get("players") or [{}])[v.get("sheriff", 0)].get("name", "?") if v.get("players") else "?"
        head = self._t("head", phase=phase, r=v.get("round", 0), t=v.get("rounds_total", 0), name=sheriff_name)
        t = get_font(24).render(head, True, COLOR_ACCENT)
        self.screen.blit(t, (20, 16))

        # Deck info only (discard piles are hidden and cannot be drawn from)
        t = get_font(16).render(self._t("deck_info", n=v.get("deck_count", 0)),
                                True, COLOR_DIM)
        self.screen.blit(gfx.card_back(36, 52), (20, 42))
        self.screen.blit(t, (64, 46))

        # Player panels (multi-line nameplates)
        plist = v.get("players", [])
        n = len(plist)
        pw = min(215, 860 // max(n, 1) - 10)
        you = v.get("you") or {}
        py, ph = 78, 152
        for i, p in enumerate(plist):
            x = 20 + i * (pw + 10)
            pygame.draw.rect(self.screen, COLOR_PANEL, (x, py, pw, ph), border_radius=8)
            tag = self._t("sheriff_tag") if i == v.get("sheriff") else ""
            col = COLOR_ACCENT if i == v.get("sheriff") else COLOR_TEXT
            nx = x + 8
            if i == v.get("sheriff"):
                self.screen.blit(gfx.badge(20), (nx, py + 8))
                nx += 24
            t = get_font(17).render(tag + p["name"], True, col)
            self.screen.blit(t, (nx, py + 6))
            yy = py + 30
            gold = self._t("gold_hand", g=p["gold"], h=p["hand_count"])
            if p.get("bag_size"):
                gold += "  " + self._t("bag_sealed", n=p["bag_size"])
            self.screen.blit(gfx.coin(16), (x + 8, yy + 2))
            t = get_font(15).render(gold, True, COLOR_TEXT)
            self.screen.blit(t, (x + 26, yy)); yy += 20
            if not p.get("connected", True):
                t = get_font(15).render(self._t("offline_tag"), True, COLOR_RED)
                self.screen.blit(t, (x + 8, yy)); yy += 20
            if p.get("decl"):
                d = p["decl"]
                t = get_font(15).render(self._t("declared", t=self._tn(d["type"]), c=d["count"]), True,
                                        TYPE_COLOR.get(d["type"], COLOR_GREEN))
                self.screen.blit(t, (x + 8, yy)); yy += 20
            stall_parts = [f"{self._tn(k)}x{cnt}" for k, cnt in (p.get("stand_legal") or {}).items()]
            for rt in (p.get("stand_royal") or []):
                rd = game.ROYAL_GOODS.get(rt)
                if rd:
                    stall_parts.append(f"{self._tn(rt)}(={rd['equals']}{self._tn(rd['of'])})")
            legal_txt = self._t("stall") + " ".join(stall_parts)
            yy = self._draw_block(self.screen, legal_txt, x + 8, yy, get_font(14), COLOR_TEXT, pw - 16) + 4
            if i == self.my_seat:
                mine = you.get("stand_contra") or []
                counts = {}
                for c in mine:
                    if c["type"] not in game.ROYAL_TYPES:
                        counts[c["type"]] = counts.get(c["type"], 0) + 1
                contra_text = (" ".join(f"{self._tn(t)}x{n}" for t, n in counts.items())
                               if counts else self._t("empty"))
                contra_txt = self._t("smuggle_own", s=contra_text)
            else:
                contra_txt = self._t("smuggle_secret", n=p.get("smuggle_count", 0))
            self._draw_block(self.screen, contra_txt, x + 8, yy, get_font(14), COLOR_CONTRA_TEXT, pw - 16)

        # Instruction line
        prompt = v.get("prompt") or {}
        kind = prompt.get("kind")
        instr = None
        if kind == "inspect":
            if prompt.get("bribe_gold", 0) > 0 or prompt.get("bribe_msg"):
                note = f": {prompt['bribe_msg']}" if prompt.get("bribe_msg") else ""
                instr = self._t("instr_inspect_bribe", name=prompt.get("owner", "?"),
                                g=prompt.get("bribe_gold", 0), note=note)
            else:
                instr = self._t("instr_inspect", name=prompt.get("owner", "?"))
        elif kind == "load_bag":
            instr = self._t("instr_load_bag") + "   " + self._t("selected_n", n=len(self.selected))
        elif kind:
            instr = {
                "market_discard": self._t("instr_market_discard") + "   " +
                    self._t("selected_n", n=len(self.selected)),
                "market_draw": self._t("instr_market_draw", n=prompt.get("hand", 0),
                                       d=prompt.get("draw_left", 0)),
                "declare": self._t("instr_declare", n=prompt.get("bag_count", 0)),
                "bribe": self._t("instr_bribe"),
            }.get(kind)
        if instr is None:
            acting = v.get("acting") or "?"
            ap = v.get("acting_phase")
            instr = {
                "market_discard": self._t("instr_waiting_market_discard", name=acting),
                "market_draw": self._t("instr_waiting_market_draw", name=acting),
                "load": self._t("instr_waiting_load"),
                "declare": self._t("instr_waiting_declare", name=acting),
                "bribe": self._t("instr_waiting_bribe", name=acting),
                "inspect": self._t("instr_waiting_inspect"),
            }.get(ap) or self._t("instr_waiting", name=acting)
        t = get_font(20).render(instr, True, COLOR_GREEN if kind else COLOR_DIM)
        self.screen.blit(t, (20, 236))

        self._draw_black_market()

        # Bag info
        you = v.get("you") or {}
        bag = you.get("bag", [])
        contra_n = len(you.get("stand_contra", []))
        types = " ".join(self._tn(c["type"]) for c in bag) or self._t("empty")
        bag_t = self._t("bag_info", n=len(bag), types=types, c=contra_n)
        t = get_font(18).render(bag_t, True, COLOR_TEXT)
        bm = v.get("black_market")
        bm_h = (36 + len(bm.get("types") or []) * 44) if (bm and bm.get("types")) else 0
        bag_y = 268 + bm_h + 10 if bm_h else 424
        self.screen.blit(t, (40, bag_y))
        # Hand & buttons
        for b in self.hand_buttons:
            b.draw(self.screen)
        for b in self.buttons:
            b.draw(self.screen)

        # Chat panel (wrapped, full messages)
        pygame.draw.rect(self.screen, COLOR_PANEL, (880, 60, 390, 680), border_radius=8)
        t = get_font(18).render(self._t("chat_title"), True, COLOR_ACCENT)
        self.screen.blit(t, (890, 66))
        y = 726
        for text, col in reversed(self.chat_log[-24:]):
            y = self._draw_wrapped(self.screen, text, 890, y, get_font(16),
                                   col or COLOR_TEXT, 360)
            if y < 100:
                break
        self.chat_input.draw(self.screen)

        if (prompt or {}).get("kind") == "bribe":
            t = get_font(16).render(self._t("bribe_gold"), True, COLOR_TEXT)
            self.screen.blit(t, (40, 646))
            self.gold_input.draw(self.screen)
            self.msg_input.draw(self.screen)

    def _draw_black_market(self):
        v = self.view or {}
        bm = v.get("black_market")
        if not bm:
            return
        types = bm.get("types") or []
        if not types:
            return
        n_groups = len(types)
        need = bm.get("need") or game.BLACK_MARKET_NEED
        rewards = bm.get("rewards") or {}
        claimed = bm.get("claimed") or {}
        claimers = bm.get("claimers") or {}
        progress = bm.get("progress") or {}
        plist = v.get("players", [])
        pygame.draw.rect(self.screen, COLOR_PANEL, (20, 268, 860, 36 + n_groups * 44),
                         border_radius=8)
        t = get_font(16).render(self._t("bm_title"), True, COLOR_ACCENT)
        self.screen.blit(t, (30, 276))
        y = 292
        for t_ in types:
            head = get_font(15).render(self._tn(t_), True, TYPE_COLOR.get(t_, COLOR_TEXT))
            self.screen.blit(head, (30, y))
            cl = claimers.get(t_, [None, None]) or [None, None]
            c = claimed.get(t_, 0)
            rw = rewards.get(t_, [0, 0]) or [0, 0]
            for si in range(2):
                tx = 110 + si * 280
                if si < c and cl[si]:
                    tt = get_font(14).render(
                        self._t("bm_done1" if si == 0 else "bm_done2", n=cl[si]),
                        True, COLOR_GREEN)
                else:
                    tt = get_font(14).render(
                        self._t("bm_slot1" if si == 0 else "bm_slot2", g=rw[si]),
                        True, COLOR_TEXT)
                self.screen.blit(tt, (tx, y))
            segs = []
            for i, p in enumerate(plist):
                n = ((progress.get(i) or progress.get(str(i)) or {})).get(t_, 0)
                if n <= 0:
                    continue
                col = COLOR_ACCENT if i == self.my_seat else COLOR_DIM
                segs.append((f"{p['name']} {n}/{need}", col))
            px = 30
            py = y + 24
            if not segs:
                tt = get_font(13).render("-", True, COLOR_DIM)
                self.screen.blit(tt, (px, py))
            else:
                for txt, col in segs:
                    tt = get_font(13).render(txt, True, col)
                    if px > 30:
                        sep = get_font(13).render("  ·  ", True, COLOR_DIM)
                        self.screen.blit(sep, (px, py))
                        px += sep.get_width()
                    self.screen.blit(tt, (px, py))
                    px += tt.get_width()
            y += 44


    def _draw_over(self):
        title = get_font(40).render(self._t("over_title"), True, COLOR_ACCENT)
        self.screen.blit(title, title.get_rect(center=(W // 2, 70)))
        v = self.view or {}
        if v.get("phase") == "CLOSED":
            t = get_font(24).render(v.get("msg", ""), True, COLOR_RED)
            self.screen.blit(t, t.get_rect(center=(W // 2, 200)))
        else:
            scores = v.get("scores") or []
            y = 130
            for i, r in enumerate(scores):
                line = self._t("score_line", i=i + 1, name=r["name"], final=r["final"],
                                g=r["value"] - r["gold"], gold=r["gold"], bonus=r["bonus"])
                t = get_font(22).render(line, True, COLOR_TEXT)
                self.screen.blit(t, (90, y))
                y += 27
                detail = r.get("bonus_detail") or []
                if detail:
                    d = " ".join(
                        (f"{self._tn(x['type'])}x{x['count']}+{x['bonus']}" if x.get("count")
                         else f"{self._tn(x['type'])}+{x['bonus']}") for x in detail)
                    t = get_font(15).render(self._t("bonus_detail", d=d), True, COLOR_DIM)
                    self.screen.blit(t, (110, y))
                    y += 22
                y += 20
            if scores:
                winner = scores[0]
                t = get_font(26).render(self._t("winner", name=winner["name"]), True, COLOR_ACCENT)
                self.screen.blit(t, (110, y + 4))
            table = v.get("bonus_table") or []
            if table:
                t = get_font(22).render(self._t("over_bonus_title"), True, COLOR_ACCENT)
                self.screen.blit(t, (640, 130))
                ty = 168
                for e in table:
                    parts = []
                    if e["kind"] == "king":
                        for k, a in enumerate(e["awards"]):
                            tag = self._t("place1" if k == 0 else "place2")
                            parts.append(f"{tag} {a['name']}+{a['bonus']}")
                        head = self._tn(e["type"])
                    else:  # black market cards
                        for a in e["awards"]:
                            parts.append(f"{a['name']}+{a['bonus']}")
                        head = self._t("bm_tag")
                    line = f"{head}: " + ", ".join(parts)
                    t = get_font(17).render(line, True, TYPE_COLOR.get(e["type"], COLOR_TEXT))
                    self.screen.blit(t, (640, ty))
                    ty += 26
        for b in self.buttons:
            b.draw(self.screen)

    def _wrap_text(self, text, font, max_w):
        """Split text into lines that fit max_w pixels (CJK-safe: breaks long runs)."""
        lines = []
        cur = ""
        for w in text.split(" "):
            if not w:
                continue
            trial = (cur + " " + w).strip()
            if font.size(trial)[0] <= max_w:
                cur = trial
            elif font.size(w)[0] <= max_w:
                if cur:
                    lines.append(cur)
                cur = w
            else:
                if cur:
                    lines.append(cur)
                cur = ""
                for ch in w:
                    trial2 = cur + ch
                    if font.size(trial2)[0] <= max_w:
                        cur = trial2
                    else:
                        if cur:
                            lines.append(cur)
                        cur = ch
        if cur:
            lines.append(cur)
        return lines

    def _draw_block(self, surf, text, x, y_top, font, color, max_w):
        """Draw wrapped text top-down; returns the y below the block."""
        y = y_top
        for ln in self._wrap_text(text, font, max_w):
            t = font.render(ln, True, color)
            surf.blit(t, (x, y))
            y += t.get_height() + 2
        return y

    def _draw_wrapped(self, surf, text, x, y, font, color, max_w):
        """Draw text wrapped to max_w pixels, bottom-up; returns new baseline y."""
        for ln in self._wrap_text(text, font, max_w):
            t = font.render(ln, True, color)
            surf.blit(t, (x, y - t.get_height()))
            y -= t.get_height() + 2
        return y

    # ---------- Main loop ----------

    def run(self):
        self._rebuild_menu_ui()
        if self.screen_name in ("lobby", "game", "over"):
            self._append_chat(self._t("connected"))
        while not self.done:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.done = True
                else:
                    self.handle_event(ev)
            self.process_client_msgs()
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)
        self.cleanup()

    def cleanup(self):
        if self.client:
            self.client.close()
        if self.server:
            self.server.stop()
        try:
            pygame.key.stop_text_input()
        except Exception:
            pass
        pygame.quit()
