# -*- coding: utf-8 -*-
"""pygame UI (minimal button-only version, EN/Chinese bilingual)."""

import os
import sys
import threading
import time

import pygame

import game
import gfx
import lang
import market
import mods
import net
import profile
import updater
import version

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


_TEXT_OUTLINE = (24, 18, 12)   # dark outline behind bright card/goods text


def render_outlined(font, text, color, outline=_TEXT_OUTLINE, width=2):
    """Render text with a dark outline so bright card colors stay readable.

    Returns a surface 2*width px larger on every side; center-blits keep the
    text centered automatically.
    """
    base = font.render(text, True, color)
    w = max(1, int(width))
    out = font.render(text, True, outline)
    s = pygame.Surface((base.get_width() + 2 * w, base.get_height() + 2 * w),
                       pygame.SRCALPHA)
    for dx in (-w, 0, w):
        for dy in (-w, 0, w):
            if dx or dy:
                s.blit(out, (w + dx, w + dy))
    s.blit(base, (w, w))
    return s


def _out_blit(surf, font, text, color, pos, outline=_TEXT_OUTLINE, width=2):
    """Blit outlined text so its visual top-left lands at ``pos`` and return
    the visual advance (the plain-text width, without outline padding)."""
    s = render_outlined(font, text, color, outline, width)
    w = int(width)
    surf.blit(s, (pos[0] - w, pos[1] - w))
    return s.get_width() - 2 * w


class Button:
    def __init__(self, rect, text, cb=None, enabled=True, highlight=False,
                 bg=None, border=None, value=None, sub=None, icon=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.cb = cb
        self.enabled = enabled
        self.highlight = highlight
        self.bg = bg          # fill color override (per-type card tint)
        self.border = border  # border color override (contraband frame)
        self.value = value    # big number near the top (card value)
        self.sub = sub        # small bottom hint (fine / contraband tag)
        self.icon = icon      # optional surface drawn instead of text

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
            t = render_outlined(get_font(26), str(self.value), txt)
            surf.blit(t, t.get_rect(center=(self.rect.centerx, self.rect.y + 32)))
            cy += 16
        t = render_outlined(get_font(17), self.text, txt)
        surf.blit(t, t.get_rect(center=(self.rect.centerx, cy)))
        if self.sub:
            t = render_outlined(get_font(13), self.sub, COLOR_DIM)
            surf.blit(t, t.get_rect(center=(self.rect.centerx, self.rect.bottom - 12)))
        if self.icon is not None:
            ic = self.icon
            if ic.get_width() > self.rect.width - 8 or ic.get_height() > self.rect.height - 8:
                scale = min((self.rect.width - 8) / ic.get_width(),
                            (self.rect.height - 8) / ic.get_height())
                ic = pygame.transform.smoothscale(ic, (int(ic.get_width() * scale),
                                                       int(ic.get_height() * scale)))
            surf.blit(ic, ic.get_rect(center=self.rect.center))


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
                # Paste REPLACES the whole field: appending made copied
                # addresses (e.g. "ip:port") duplicate when pasting twice
                # or into a field that already had content.
                pasted = self._clipboard_text()
                if pasted:
                    self.text = pasted
        return False

    @staticmethod
    def _clipboard_text():
        try:
            raw = pygame.scrap.get(pygame.SCRAP_TEXT)
            if raw:
                for enc in ("utf-8", "utf-16-le", "gbk"):
                    try:
                        text = raw.decode(enc)
                        # Strip NULs, BOM and line breaks that clipboard
                        # formats often append (UTF-16 terminator, CR/LF).
                        return "".join(
                            ch for ch in text
                            if ch not in ("\x00", "\ufeff", "\r", "\n")
                        ).strip()
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
        self.lobby_rules_mods = []
        self.lobby_mods_ok = True
        self.lobby_players_mods = []
        self.lobby_mods_toast = ""
        self.lobby_rmods_conflicts = []
        self.bot_personality = "any"
        self.update_scroll = 0
        self.mods_scroll = 0
        self.market_scroll = 0
        self.lobby_mods_scroll = 0
        self.menu_news_scroll = 0
        self.chat_scroll = 0
        self.chat_max_scroll = 0
        self.chat_drag = False
        self.chat_thumb = None
        self.chat_drag_offset = 0
        self.ready = False
        self.mods_row_buttons = []
        self.market_row_buttons = []
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
        self.profile = profile.load_profile()
        self.avatar_id = self.profile.get("avatar") or profile.DEFAULT_AVATAR
        self.custom_avatar = self.profile.get("custom_avatar")
        self.avatar_toast = ""
        self.avatar_path_input = TextInput((430, 470, 300, 30), "")
        self.avatar_buttons = []
        self.mods_toast = ""
        self.mods_restart_needed = False
        self.market_mods = []
        self.market_error = ""
        self.market_state = "idle"     # idle | loading | installing | ready
        self.market_installing_id = ""
        self.market_toast = ""
        self.update_state = "idle"
        self.update_info = None
        self.update_error = ""
        self.update_progress = 0.0
        self.update_installer = ""
        self.update_banner = ""
        self._update_ui_dirty = False
        if updater.is_frozen():
            self._start_update_check()
        for err in self.mod_errors:
            self._append_chat(self._t("mods_error", s=err), COLOR_RED)
        if self.mod_names:
            self._append_chat(self._t("mods_line", s=", ".join(self.mod_names)), COLOR_GOLD)

        self.name_input = TextInput((300, 262, 300, 36), self._t("ph_name"))
        self.players_input = TextInput((300, 330, 300, 36), self._t("ph_players"))
        self.join_input = TextInput((300, 398, 300, 36), self._t("ph_join"))
        self.rounds_input = TextInput((W // 2 - 260, 545, 110, 36), self._t("ph_rounds"))
        self.wild_input = TextInput((W // 2 - 260, 545, 110, 36), self._t("ph_wild"))
        self.lobby_rename_input = TextInput((W // 2 - 260, 480, 200, 36), self._t("ph_name"))
        self.chat_input = TextInput((910, 730, 250, 30), self._t("ph_chat"))
        self.gold_input = TextInput((40, 668, 110, 32), self._t("ph_gold"))
        self.msg_input = TextInput((170, 668, 300, 32), self._t("ph_note"))
        self.buttons = []
        self.hand_buttons = []

        if self.name and self.name != self._t("default_name"):
            self.name_input.text = self.name
        elif self.profile.get("name"):
            self.name_input.text = self.profile["name"]
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

    def _category_label(self, cat):
        key = "mods_cat_" + str(cat or "other").lower()
        s = lang.UI[self.lang].get(key)
        return s if s else lang.UI[self.lang].get("mods_cat_other", str(cat))

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
        self.avatar_path_input.placeholder = self._t("avatar_path_hint")
        pygame.display.set_caption(self._t("title"))
        if self.screen_name == "menu":
            self._rebuild_menu_ui()
        elif self.screen_name == "mods":
            self._rebuild_mods_ui()
        elif self.screen_name == "market":
            self._rebuild_market_ui()
        elif self.screen_name == "update":
            self._rebuild_update_ui()
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
        self._save_profile_name()
        addr = self.join_input.text.strip()
        if not addr:
            return
        addr = "".join(ch for ch in addr if ch not in ("\x00", "\ufeff", "\r", "\n")).strip()
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
            self.client = net.GameClient(self.host_addr[0], self.host_addr[1], name,
                                         avatar=self._avatar_payload())
            self.screen_name = "lobby"
            self._append_chat(self._t("connected"))
        except OSError as e:
            self._append_chat(self._t("conn_failed", e=e), COLOR_RED)

    # ---------- Events ----------

    def handle_event(self, ev):
        if self.screen_name == "menu":
            self.name_input.handle(ev)
            self.players_input.handle(ev)
            self.join_input.handle(ev)
            self.avatar_path_input.handle(ev)
            for b in self.avatar_buttons:
                b.handle(ev)
            for b in self.buttons:
                b.handle(ev)
            if ev.type == pygame.MOUSEWHEEL:
                news = pygame.Rect(70, 522, 1130, 248)
                if news.collidepoint(pygame.mouse.get_pos()):
                    self.menu_news_scroll = max(0, self.menu_news_scroll - int(ev.y) * 28)
        elif self.screen_name == "lobby":
            self.lobby_rename_input.handle(ev)
            self.rounds_input.handle(ev)
            for b in self.buttons:
                b.handle(ev)
            if ev.type == pygame.MOUSEWHEEL:
                area = pygame.Rect(610, 130, 580, 210)
                if area.collidepoint(pygame.mouse.get_pos()):
                    self.lobby_mods_scroll = max(0, self.lobby_mods_scroll - int(ev.y) * 32)
        elif self.screen_name == "mods":
            if ev.type == pygame.MOUSEWHEEL:
                self.mods_scroll = max(0, self.mods_scroll - int(ev.y) * 36)
                self._rebuild_mods_ui()
            for b in self.buttons:
                b.handle(ev)
            for b in self.mods_row_buttons:
                b.handle(ev)
        elif self.screen_name == "market":
            if ev.type == pygame.MOUSEWHEEL:
                self.market_scroll = max(0, self.market_scroll - int(ev.y) * 36)
                self._rebuild_market_ui()
            for b in self.buttons:
                b.handle(ev)
            for b in self.market_row_buttons:
                b.handle(ev)
        elif self.screen_name == "update":
            if ev.type == pygame.MOUSEWHEEL:
                self.update_scroll = max(0, self.update_scroll - int(ev.y) * 26)
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
            if prompt.get("kind") in ("bribe", "inspect", "counter_bribe"):
                if self.gold_input.handle(ev) == "submit":
                    if prompt.get("kind") == "bribe":
                        self._do_bribe()
                    elif prompt.get("kind") == "inspect":
                        self._sheriff_counter()
                    else:
                        self._merchant_counter()
                if prompt.get("kind") == "bribe":
                    self.msg_input.handle(ev)
            if ev.type == pygame.MOUSEWHEEL:
                # Chat is the only scrollable area in-game; scroll it
                # wherever the wheel is used (also immune to high-DPI
                # mouse-coordinate mismatches) and keep the value an int
                # so fractional touchpad deltas cannot corrupt drawing.
                self.chat_scroll = max(0, int(self.chat_scroll) + int(ev.y))
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                body = pygame.Rect(890, 96, 372, 622)
                bar = pygame.Rect(body.right - 18, body.y, 18, body.height)
                if bar.collidepoint(ev.pos) and self.chat_max_scroll > 0:
                    thumb = self.chat_thumb
                    if thumb is not None and thumb.inflate(8, 0).collidepoint(ev.pos):
                        # grab the handle and drag it
                        self.chat_drag = True
                        self.chat_drag_offset = ev.pos[1] - thumb.y
                    else:
                        # click on the track: page toward the click
                        target = (thumb.y if thumb is not None
                                  else body.y + body.height // 2)
                        if ev.pos[1] < target:
                            self.chat_scroll = max(0, self.chat_scroll - 8)
                        else:
                            self.chat_scroll = min(self.chat_max_scroll,
                                                   self.chat_scroll + 8)
            elif ev.type == pygame.MOUSEMOTION and self.chat_drag:
                body = pygame.Rect(890, 96, 372, 622)
                thumb = self.chat_thumb
                if thumb is not None and thumb.height > 0:
                    new_y = ev.pos[1] - self.chat_drag_offset
                    frac = (new_y - body.y) / max(1, body.height - thumb.height)
                    self.chat_scroll = min(self.chat_max_scroll,
                                           max(0, int(frac * (self.chat_max_scroll + 1))))
                else:
                    frac = (ev.pos[1] - body.y) / max(1, body.height)
                    self.chat_scroll = min(self.chat_max_scroll,
                                           max(0, int(frac * (self.chat_max_scroll + 1))))
            elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                self.chat_drag = False
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
                self.lobby_rules_mods = list(m.get("rules_mods") or [])
                self.lobby_mods_ok = bool(m.get("mods_ok", True))
                self.lobby_players_mods = list(m.get("players_mods") or [])
                self.lobby_rmods_conflicts = list(m.get("rmods_conflicts") or [])
                self.screen_name = "lobby"
                self._rebuild_lobby_ui()
            elif t == "mods_mismatch":
                missing = m.get("missing") or []
                names = ", ".join(str(x.get("name", "?")) for x in missing)
                self._append_chat(self._t("mods_mismatch_chat", names=names), COLOR_RED)
                self._append_chat(self._t("rmods_start_block"), COLOR_RED)
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
            elif t == "intel":
                self._append_chat(self._t("intel_result",
                                          lo=m.get("lo", 0), hi=m.get("hi", 2)),
                                  COLOR_GOLD)
            elif t == "chat":
                self._append_chat(f"{m['from']}: {m['msg']}")
            elif t == "status":
                color = COLOR_RED if "disconnected" in m.get("msg", "") else COLOR_DIM
                self._append_chat("⚑ " + self._msg(m.get("msg", "")), color)
            elif t == "error":
                msg = self._msg(m.get("msg", ""))
                if m.get("code") == "version" and not self.is_host:
                    self._leave_to_menu()
                    self.menu_note = msg
                else:
                    self._append_chat("✗ " + msg, COLOR_RED)
            elif t == "server_closed":
                self._append_chat(self._msg(m.get("msg", "") or self._t("room_closed")), COLOR_RED)
                if self.is_host:
                    self._leave_to_menu()
                else:
                    self.closed = True
                    self.disconnected = True
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

    def _panel(self, surf, rect, title=None, fill=None, title_color=None):
        """Rounded panel with border and optional header text."""
        rect = pygame.Rect(rect)
        pygame.draw.rect(surf, fill or COLOR_PANEL, rect, border_radius=12)
        pygame.draw.rect(surf, (30, 24, 18), rect, 2, border_radius=12)
        if title:
            t = get_font(19).render(title, True, title_color or COLOR_ACCENT)
            surf.blit(t, (rect.x + 16, rect.y + 10))

    def _decor_bg(self):
        """Shared background for menu-like screens (game screen draws its own)."""
        self.screen.fill(COLOR_BG)
        pygame.draw.rect(self.screen, (48, 41, 33), (0, 0, W, 10))
        pygame.draw.rect(self.screen, (48, 41, 33), (0, H - 10, W, 10))
        try:
            b1 = gfx.badge(150).copy()
            b1.set_alpha(13)
            self.screen.blit(b1, (36, 36))
            b2 = gfx.badge(200).copy()
            b2.set_alpha(9)
            self.screen.blit(b2, (W - 230, H - 230))
        except Exception:  # noqa: BLE001 - decoration only
            pass

    def _screen_header(self, title, subtitle=None):
        t = get_font(36).render(title, True, COLOR_ACCENT)
        self.screen.blit(gfx.badge(30), (W // 2 - t.get_width() // 2 - 46, 44))
        self.screen.blit(t, t.get_rect(center=(W // 2, 60)))
        if subtitle:
            s = get_font(15).render(subtitle, True, COLOR_DIM)
            self.screen.blit(s, s.get_rect(center=(W // 2, 96)))

    def _rule_mod_enabled(self, mod_id):
        """True when the room's rule-mod list (or local mods) contains mod_id."""
        for m in (self.lobby_rules_mods or []):
            if str(m.get("id", "")).lower() == mod_id:
                return True
        return False

    def _mod_display_name(self, mod_id):
        for m in (self.lobby_rules_mods or []):
            if str(m.get("id", "")).lower() == mod_id:
                if self.lang == "zh":
                    return m.get("name_zh") or m.get("name") or mod_id
                return m.get("name") or mod_id
        return mod_id

    def _rebuild_menu_ui(self):
        self.buttons = []
        # Game setup panel
        self.name_input.rect = pygame.Rect(90, 246, 300, 34)
        self.players_input.rect = pygame.Rect(90, 316, 300, 34)
        self.join_input.rect = pygame.Rect(90, 386, 300, 34)
        self.buttons.append(Button((400, 386, 66, 34), self._t("btn_paste"), self._paste_join))
        self.buttons.append(Button((90, 440, 190, 40), self._t("btn_create"), self._create_room_click))
        self.buttons.append(Button((290, 440, 176, 40), self._t("btn_join"), self._join_room))
        # Avatar panel
        self.avatar_path_input.rect = pygame.Rect(552, 448, 274, 30)
        self.buttons.append(Button((552, 404, 132, 34), self._t("btn_avatar_upload"),
                                   self._upload_avatar))
        self.buttons.append(Button((694, 404, 132, 34), self._t("btn_avatar_clear"),
                                   self._clear_avatar))
        self.avatar_buttons = []
        for i, key in enumerate(profile.BUILTIN_AVATARS):
            col, row = i % 4, i // 4
            x = 552 + col * 60
            y = 270 + row * 60
            self.avatar_buttons.append(Button(
                (x, y, 56, 56), "",
                lambda k=key: self._pick_avatar(k),
                icon=gfx.avatar_surface({"kind": "builtin", "id": key}, 52),
                highlight=(key == self.avatar_id and not self.custom_avatar)))
        # Tools grid
        for i, (label, cb) in enumerate([
                (self._t("btn_mods"), self._open_mods),
                (self._t("btn_market"), self._open_market),
                (self._t("btn_update"), self._open_update),
                (self._t("btn_quit"), lambda: setattr(self, "done", True))]):
            self.buttons.append(Button((890, 240 + i * 72, 280, 52), label, cb))
        self.buttons.append(Button((W - 170, 20, 140, 40), self._t("btn_lang"), self._toggle_lang))
        self.avatar_path_input.placeholder = self._t("avatar_path_hint")

    def _toggle_lang(self):
        self._set_lang("en" if self.lang == "zh" else "zh")

    def _paste_join(self):
        txt = TextInput._clipboard_text().strip()
        if txt:
            self.join_input.text = txt
            self.menu_note = self._t("paste_done", addr=txt)
        else:
            self.menu_note = ""

    # ---------- Profile & avatars ----------

    def _avatar_payload(self):
        if self.custom_avatar:
            return {"kind": "custom", "data": self.custom_avatar}
        return {"kind": "builtin", "id": self.avatar_id}

    def _save_profile_name(self):
        nm = self.name_input.text.strip()
        if nm:
            self.profile["name"] = nm
            profile.save_profile(self.profile)

    def _pick_avatar(self, key):
        self.avatar_id = key
        self.custom_avatar = None
        self.profile["avatar"] = key
        self.profile["custom_avatar"] = None
        self._save_profile_name()
        profile.save_profile(self.profile)
        self.avatar_toast = self._t("avatar_saved")
        self._rebuild_menu_ui()

    def _pick_image_file(self):
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            try:
                path = filedialog.askopenfilename(
                    title="Select avatar image",
                    filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.gif"), ("All files", "*.*")])
            finally:
                root.destroy()
            return str(path or "").strip()
        except Exception:  # noqa: BLE001 - tkinter missing in some builds
            return self.avatar_path_input.text.strip()

    def _upload_avatar(self):
        path = self._pick_image_file()
        if not path:
            return
        try:
            surf = pygame.image.load(path)
        except Exception as e:  # noqa: BLE001
            self.avatar_toast = self._t("avatar_failed", e=e)
            return
        try:
            if surf.get_width() > 512 or surf.get_height() > 512:
                surf = pygame.transform.smoothscale(surf, (512, 512))
            if surf.get_width() > surf.get_height():
                w, h = 128, int(surf.get_height() * 128 / surf.get_width())
            else:
                h, w = 128, int(surf.get_width() * 128 / surf.get_height())
            surf = pygame.transform.smoothscale(surf, (max(1, w), max(1, h)))
            data, ok = profile.encode_png(surf, size=128)
        except Exception as e:  # noqa: BLE001
            self.avatar_toast = self._t("avatar_failed", e=e)
            return
        if not ok:
            self.avatar_toast = self._t("avatar_failed", e="encode")
            return
        self.custom_avatar = data
        self.profile["custom_avatar"] = data
        self.profile["avatar"] = self.avatar_id
        profile.save_profile(self.profile)
        self.avatar_toast = self._t("avatar_saved")
        self._rebuild_menu_ui()

    def _clear_avatar(self):
        self.custom_avatar = None
        self.profile["custom_avatar"] = None
        profile.save_profile(self.profile)
        self.avatar_toast = self._t("avatar_saved")
        self._rebuild_menu_ui()

    def _copy_lan(self):
        addr = f"{self.server.local_ip}:{self.port}" if self.server else ""
        if addr:
            if self._copy_text(addr):
                self._append_chat(self._t("copied", addr=addr), COLOR_GREEN)
            else:
                self._append_chat(self._t("conn_failed", e="clipboard"), COLOR_RED)

    def _create_room_click(self):
        self._save_profile_name()
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
        # Fixed lobby layout: players card (left), rule-mods card (right).
        self.lobby_host_y = 420
        self.rounds_input.rect = pygame.Rect(610, 466, 110, 28)
        self.wild_input.rect = pygame.Rect(740, 466, 110, 28)
        self.wild_input_visible = self._wild_mod_enabled()
        self.lobby_rename_input.rect = pygame.Rect(90, 632, 300, 30)
        self.buttons.append(Button((400, 632, 140, 30), self._t("btn_rename"),
                                   self._rename_click))
        self.ready = self._my_ready(info)
        # Bottom action bar: Ready toggle for everyone
        self.buttons.append(Button((120, 700, 200, 46),
                                   self._t("btn_not_ready") if self.ready else self._t("btn_ready"),
                                   self._ready_click))
        if self.is_host:
            self.buttons.append(Button((340, 700, 220, 46), self._t("btn_start"),
                                       self._start_game_click, enabled=can_start))
            self.buttons.append(Button((580, 700, 150, 46), self._t("btn_copy"),
                                       self._copy_lan))
            self.buttons.append(Button((750, 700, 150, 46), self._t("btn_leave"),
                                       self._leave_to_menu))
            # Bots: difficulty row
            can_add = len(joined) < int(info.get("max_players", 9))
            for i, lvl in enumerate(("easy", "normal", "hard")):
                self.buttons.append(Button(
                    (610 + i * 108, 524, 100, 28),
                    self._t("btn_add_" + lvl),
                    lambda l=lvl: self._add_bot(l), enabled=can_add))
            self.buttons.append(Button((934, 524, 100, 28), self._t("btn_remove_bot"),
                                       self._remove_bot_click, enabled=bool(bots)))
            # Bots: personality row
            for i, p in enumerate(("any", "paranoid", "greedy", "honest", "reckless")):
                self.buttons.append(Button(
                    (610 + i * 96, 580, 90, 26),
                    self._t("pers_" + p),
                    lambda p=p: self._set_bot_personality(p),
                    highlight=(self.bot_personality == p)))
        else:
            self.buttons.append(Button((340, 700, 340, 46), self._t("btn_leave"),
                                       self._leave_to_menu))
        if not self.is_host and not self.lobby_mods_ok and self.lobby_rules_mods:
            installing = self.market_state in ("loading", "installing")
            self.buttons.append(Button((610, 208, 270, 34),
                                       self._t("btn_install_rule_mods"),
                                       self._install_missing_rule_mods,
                                       enabled=not installing))
        self.buttons.append(Button((W - 170, 20, 140, 40), self._t("btn_lang"), self._toggle_lang))

    def _pm_mods_ok(self, pm):
        """Compare a player's reported rule mods against the room's list."""
        def norm(items):
            return sorted(
                ({"id": str(x.get("id", "")).lower(), "version": str(x.get("version", ""))}
                 for x in items or []),
                key=lambda x: x["id"])
        return norm(pm.get("mods")) == norm(self.lobby_rules_mods)

    def _missing_rule_mod_ids(self):
        """Rule mods the room requires but this client does not have (id+version)."""
        mine = mods.rules_mods()
        have = {(m.get("id", ""), m.get("version", "")) for m in mine}
        return [m.get("id", "") for m in (self.lobby_rules_mods or [])
                if (m.get("id", ""), m.get("version", "")) not in have]

    def _install_missing_rule_mods(self):
        if self.market_state in ("loading", "installing"):
            return
        need = self._missing_rule_mod_ids()
        if not need:
            return
        self.market_state = "loading"
        self.lobby_mods_toast = self._t("market_installing")
        threading.Thread(target=self._thread_install_rule_mods, args=(need,),
                         daemon=True).start()

    def _thread_install_rule_mods(self, need_ids):
        mods_list, err = market.fetch_market()
        by_id = {str(m.get("id", "")).lower(): m for m in (mods_list or [])}
        to_install = [by_id[i] for i in need_ids if i in by_id]
        self.market_state = "ready"
        if not to_install:
            if err:
                self.lobby_mods_toast = self._t("market_load_failed", e=err)
            else:
                self.lobby_mods_toast = self._t("mods_not_on_market")
            self._rebuild_lobby_ui()
            return
        ok_all = True
        msgs = []
        for info in to_install:
            ok, msg = market.install_mod(info)
            if ok:
                # one-click install also enables the mod: restart is still
                # required, but the player no longer has to find it in the
                # Mods screen and toggle it on manually.
                mid = str(info.get("id") or info.get("folder") or "")
                if mid and not mods.set_enabled(mid, True):
                    ok_all = False
                    msgs.append(mid + ": " + self._t("market_enable_failed"))
            else:
                ok_all = False
                msgs.append(msg)
        if ok_all:
            self.lobby_mods_toast = self._t("mods_installed_restart")
            self.mods_restart_needed = True
        else:
            self.lobby_mods_toast = self._t("market_failed", e="; ".join(msgs))
        self._rebuild_lobby_ui()

    def _start_game_click(self):
        r = self._parse_int(self.rounds_input.text, 0)
        wild = None
        if self._wild_mod_enabled():
            wild = self._parse_int(self.wild_input.text, -1)
            if wild < 0:
                self.wild_input.text = "0"
                wild = 0
        self._send({"t": "start_game", "rounds": r if r >= 2 else None, "wild": wild})

    def _wild_mod_enabled(self):
        """True when the Wild Card rule mod is enabled on this client."""
        try:
            return any(str(m.get("id", "")).lower() == "wild_card"
                       for m in mods.rules_mods())
        except Exception:  # noqa: BLE001 - mods may not be loadable
            return False

    def _my_ready(self, info):
        joined = (info or {}).get("joined", [])
        for j in joined:
            if j.get("seat") == self.my_seat:
                return bool(j.get("ready"))
        return self.ready

    def _ready_click(self):
        self._send({"t": "ready"})

    def _rename_click(self):
        new = self.lobby_rename_input.text.strip()
        if new:
            self._send({"t": "rename", "name": new})
            self.name = new
            self.lobby_rename_input.text = ""
            self._append_chat(self._t("rename_done", name=new), COLOR_GREEN)

    def _set_bot_personality(self, p):
        self.bot_personality = p
        self._rebuild_lobby_ui()

    def _add_bot(self, level):
        self._send({"t": "add_bot", "level": level,
                    "personality": self.bot_personality if self.bot_personality != "any" else None})

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
            contra = ct in game.CONTRABAND or royal or bool(c.get("super"))
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

        # Quick chat (left side, below buttons; hidden while the gold input is used)
        kind = prompt.get("kind")
        if kind not in ("bribe", "inspect", "counter_bribe"):
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
            can_counter = (prompt.get("bribe_gold", 0) > 0
                           and prompt.get("round", 0) < prompt.get("max_round", 99))
            self.buttons.append(Button((40, 610, 140, 42), self._t("btn_pass"),
                                       lambda: self._inspect_decision("pass")))
            self.buttons.append(Button((195, 610, 120, 42), self._t("btn_inspect"),
                                       lambda: self._inspect_decision("inspect")))
            self.buttons.append(Button((330, 610, 150, 42), self._t("btn_counter"),
                                       lambda: self._sheriff_counter(), enabled=can_counter))
            intel = v.get("intel") or {}
            if intel.get("available"):
                self.buttons.append(Button(
                    (500, 610, 170, 42),
                    self._t("btn_intel", cost=intel.get("cost", 0)),
                    lambda: self._send({"t": "sheriff_intel"})))
        elif kind == "counter_bribe":
            can_counter = prompt.get("round", 0) < prompt.get("max_round", 99)
            self.buttons.append(Button((40, 610, 140, 42), self._t("btn_accept"),
                                       lambda: self._send({"t": "counter_response", "action": "accept"})))
            self.buttons.append(Button((195, 610, 120, 42), self._t("btn_reject"),
                                       lambda: self._send({"t": "counter_response", "action": "reject"})))
            self.buttons.append(Button((330, 610, 150, 42), self._t("btn_counter"),
                                       lambda: self._merchant_counter(), enabled=can_counter))

        # Black market reward submit buttons (next to each task, grayed until claimable)
        bm = v.get("black_market")
        if bm and bm.get("types"):
            types = bm.get("types") or []
            claimed = bm.get("claimed") or {}
            need = bm.get("need") or game.BLACK_MARKET_NEED
            mine = {}
            for c in (you.get("stand_contra") or []):
                if c.get("type") in types:
                    mine[c["type"]] = mine.get(c["type"], 0) + 1
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

    def _sheriff_counter(self):
        gold = self._parse_int(self.gold_input.text)
        self._send({"t": "counter_bribe", "gold": gold})
        self.gold_input.text = ""

    def _merchant_counter(self):
        gold = self._parse_int(self.gold_input.text)
        self._send({"t": "counter_response", "action": "counter", "gold": gold})
        self.gold_input.text = ""

    def _rebuild_over_ui(self):
        if self.closed:
            self.buttons = [
                Button((W // 2 - 210, 660, 200, 46), self._t("btn_back_menu"),
                       self._leave_to_menu),
                Button((W // 2 + 10, 660, 200, 46), self._t("btn_quit"),
                       lambda: setattr(self, "done", True)),
            ]
        else:
            self.buttons = [
                Button((W // 2 - 210, 660, 200, 46), self._t("btn_back_room"),
                       lambda: self._send({"t": "back_to_lobby"})),
                Button((W // 2 + 10, 660, 200, 46), self._t("btn_quit"),
                       lambda: setattr(self, "done", True)),
            ]

    def _restart_game(self):
        """Restart the game process so mod/profile changes take effect."""
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
            self.client = None
        if self.server:
            try:
                self.server.stop()
            except Exception:
                pass
            self.server = None
        try:
            import subprocess
            if getattr(sys, "frozen", False):
                cmd = [sys.executable] + sys.argv[1:]
            else:
                cmd = [sys.executable, os.path.abspath(sys.argv[0])] + sys.argv[1:]
            subprocess.Popen(cmd, cwd=os.getcwd(), close_fds=True)
        except Exception:
            pass
        self.done = True

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
        if ok:
            self.mods_restart_needed = True
        self.mod_list = mods.list_all_mods()
        self._rebuild_mods_ui()

    def _back_to_menu(self):
        self.screen_name = "menu"
        self._rebuild_menu_ui()

    def _leave_to_menu(self):
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
            self.client = None
        if self.server:
            try:
                self.server.stop()
            except Exception:
                pass
            self.server = None
        self.is_host = False
        self.host_addr = None
        self.lobby = None
        self.view = None
        self.server_info = []
        self.disconnected = False
        self.closed = False
        self.selected = set()
        self.decl_type = None
        self._last_reconnect = 0
        self.reconnect_tries = 0
        self.screen_name = "menu"
        self._rebuild_menu_ui()

    def _rebuild_mods_ui(self):
        self.buttons = []
        self.mods_row_buttons = []
        for i, m in enumerate(self.mod_list):
            label = self._t("mods_disable" if m["enabled"] else "mods_enable")
            self.mods_row_buttons.append(Button(
                (1040, 140 + i * 72 - self.mods_scroll, 150, 36), label,
                lambda mid=m["id"]: self._toggle_mod(mid)))
        self.buttons.append(Button((60, 700, 150, 44), self._t("btn_back"),
                                   self._back_to_menu))
        self.buttons.append(Button((230, 700, 150, 44), self._t("mods_refresh"),
                                   self._refresh_mods))
        if self.mods_restart_needed:
            self.buttons.append(Button((620, 700, 220, 44),
                                       self._t("btn_restart_game"), self._restart_game,
                                       highlight=True))

    def _draw_mods(self):
        self._screen_header(self._t("mods_title"), self._t("mods_hint"))
        path = mods.effective_mods_base()
        ptext = get_font(15).render(self._t("mods_path", s=path), True, COLOR_GOLD)
        self.screen.blit(ptext, (60, 108))
        mlist = self.mod_list
        if not mlist:
            t = get_font(20).render(self._t("mods_none"), True, COLOR_TEXT)
            self.screen.blit(t, (60, 150))
        area = pygame.Rect(60, 140, 1160, 488)
        total_h = max(1, len(mlist)) * 72
        max_scroll = max(0, total_h - area.height + 8)
        self.mods_scroll = min(self.mods_scroll, max_scroll)
        self.screen.set_clip(area)
        y = 140 - self.mods_scroll
        for i, m in enumerate(mlist):
            if y + 66 < area.top or y > area.bottom:
                y += 72
                continue
            pygame.draw.rect(self.screen, COLOR_PANEL, (60, y, 1160, 66), border_radius=8)
            state = self._t("mods_on" if m["enabled"] else "mods_off")
            mname = (m.get("name_zh") or m["name"]) if self.lang == "zh" else m["name"]
            t = get_font(20).render("{0}  v{1}   {2}".format(mname, m["version"], state),
                                    True, COLOR_GOLD if m["enabled"] else COLOR_TEXT)
            self.screen.blit(t, (80, y + 6))
            mdesc = ((m.get("description_zh") or "") or m.get("description", ""))                 if self.lang == "zh" else m.get("description", "")
            cat = self._category_label(m.get("category", "other"))
            if mdesc:
                d = get_font(15).render((cat + "  " + mdesc)[:110], True, COLOR_DIM)
                self.screen.blit(d, (80, y + 34))
            y += 72
        for b in self.mods_row_buttons:
            b.draw(self.screen)
        self.screen.set_clip(None)
        if max_scroll > 0:
            hint = get_font(13).render(self._t("list_scroll_hint"), True, COLOR_DIM)
            self.screen.blit(hint, (60, area.bottom + 6))
        if self.mod_errors:
            t = get_font(15).render(self._t("mods_errors", s="; ".join(self.mod_errors)),
                                    True, COLOR_RED)
            self.screen.blit(t, (60, 650))
        if self.mods_toast:
            t = get_font(15).render(self.mods_toast, True, COLOR_GREEN)
            self.screen.blit(t, (60, 674))
        for b in self.buttons:
            b.draw(self.screen)

    # ---------- Mods Market ----------

    def _open_market(self):
        self.screen_name = "market"
        self.market_toast = ""
        if self.market_state == "idle":
            self._refresh_market()
        else:
            self._rebuild_market_ui()

    def _refresh_market(self):
        if self.market_state in ("loading", "installing"):
            return
        self.market_state = "loading"
        self.market_error = ""
        self._rebuild_market_ui()
        threading.Thread(target=self._thread_market_load, daemon=True).start()

    def _thread_market_load(self):
        mods_list, err = market.fetch_market()
        self.market_mods = list(mods_list or [])
        self.market_error = err or ""
        self.market_state = "ready"
        self._rebuild_market_ui()

    def _install_market_mod(self, info):
        if self.market_state == "installing":
            return
        self.market_state = "installing"
        self.market_installing_id = str(info.get("id") or info.get("folder") or "?")
        self.market_toast = self._t("market_installing")
        self._rebuild_market_ui()
        threading.Thread(target=self._thread_market_install, args=(info,),
                         daemon=True).start()

    def _thread_market_install(self, info):
        ok, msg = market.install_mod(info)
        if ok:
            # installing from the market also enables the mod directly.
            mid = str(info.get("id") or info.get("folder") or "")
            if mid and not mods.set_enabled(mid, True):
                ok, msg = False, self._t("market_enable_failed")
        self.market_state = "ready"
        self.market_installing_id = ""
        if ok:
            self.market_toast = self._t("market_installed")
            self.mods_restart_needed = True
        else:
            self.market_toast = self._t("market_failed", e=msg)
        self._rebuild_market_ui()

    def _market_label(self, info, status, ver):
        mid = str(info.get("id") or info.get("folder") or "?")
        name = info.get("name") or {}
        label = name.get(self.lang) or name.get("en") or mid
        mver = str(info.get("version") or "0")
        if status == "missing":
            return "{0}  v{1}   {2}".format(label, mver, self._t("market_not_installed"))
        if status == "update":
            return "{0}  v{1}   {2}".format(label, mver, self._t("market_update_ready", v=ver))
        return "{0}  v{1}   {2}".format(label, mver, self._t("market_up_to_date", v=ver))

    def _rebuild_market_ui(self):
        self.buttons = []
        self.market_row_buttons = []
        y = 140
        for i, info in enumerate(self.market_mods):
            status, ver = market.local_status(info)
            btn_label = self._t("market_update" if status == "update" else "market_install")
            if status == "installed":
                btn_label = self._t("market_up_to_date", v=ver)
                btn = None
            elif self.market_state == "installing":
                btn = None
            else:
                btn = Button((1040, y + 18 - self.market_scroll, 150, 36), btn_label,
                             lambda inf=info: self._install_market_mod(inf))
            if btn:
                self.market_row_buttons.append(btn)
            y += 72
        self.buttons.append(Button((60, 700, 150, 44), self._t("btn_back"),
                                   self._back_to_menu))
        self.buttons.append(Button((230, 700, 150, 44), self._t("market_check"),
                                   self._refresh_market))
        if self.mods_restart_needed:
            self.buttons.append(Button((620, 700, 220, 44),
                                       self._t("btn_restart_game"), self._restart_game,
                                       highlight=True))

    def _draw_market(self):
        self._screen_header(self._t("market_title"), self._t("market_hint"))
        rh = get_font(15).render(self._t("market_restart_hint"), True, COLOR_GOLD)
        self.screen.blit(rh, rh.get_rect(center=(W // 2, 116)))
        if self.market_state in ("loading",):
            t = get_font(20).render(self._t("market_installing"), True, COLOR_DIM)
            self.screen.blit(t, (60, 150))
        elif self.market_error:
            t = get_font(18).render(self._t("market_load_failed", e=self.market_error),
                                    True, COLOR_RED)
            self.screen.blit(t, (60, 150))
        elif not self.market_mods:
            t = get_font(20).render(self._t("market_no_mods"), True, COLOR_TEXT)
            self.screen.blit(t, (60, 150))
        area = pygame.Rect(60, 140, 1160, 488)
        total_h = max(1, len(self.market_mods)) * 72
        max_scroll = max(0, total_h - area.height + 8)
        self.market_scroll = min(self.market_scroll, max_scroll)
        self.screen.set_clip(area)
        y = 140 - self.market_scroll
        for i, info in enumerate(self.market_mods):
            if y + 66 < area.top or y > area.bottom:
                y += 72
                continue
            status, ver = market.local_status(info)
            pygame.draw.rect(self.screen, COLOR_PANEL, (60, y, 1160, 66), border_radius=8)
            label = self._category_label(info.get("category", "other")) + " " + self._market_label(info, status, ver)
            t = get_font(20).render(label, True, COLOR_TEXT)
            self.screen.blit(t, (80, y + 6))
            desc = (info.get("description") or {})
            dtext = desc.get(self.lang) or desc.get("en") or ""
            if dtext:
                d = get_font(15).render(dtext[:110], True, COLOR_DIM)
                self.screen.blit(d, (80, y + 34))
            if self.market_state == "installing" and                     str(info.get("id") or "") == self.market_installing_id:
                t = get_font(16).render(self._t("market_installing"), True, COLOR_GOLD)
                self.screen.blit(t, (1040, y + 24))
            y += 72
        for b in self.market_row_buttons:
            b.draw(self.screen)
        self.screen.set_clip(None)
        if max_scroll > 0:
            hint = get_font(13).render(self._t("list_scroll_hint"), True, COLOR_DIM)
            self.screen.blit(hint, (60, area.bottom + 6))
        if self.market_toast:
            t = get_font(15).render(self.market_toast, True, COLOR_GREEN)
            self.screen.blit(t, (60, 674))
        for b in self.buttons:
            b.draw(self.screen)

    # ---------- Update ----------

    def _open_update(self):
        self.screen_name = "update"
        self._rebuild_update_ui()
        if self.update_state in ("idle",):
            self._start_update_check()

    def _check_update_click(self):
        self._start_update_check()
        self._rebuild_update_ui()

    def _start_update_check(self):
        if self.update_state in ("checking", "downloading", "installing"):
            return
        self.update_state = "checking"
        self.update_error = ""
        self.update_banner = ""
        self._update_ui_dirty = True
        threading.Thread(target=self._thread_check, daemon=True).start()

    def _error_text(self, code, detail=""):
        if code == "timeout":
            return self._t("update_err_timeout")
        if code == "network":
            return self._t("update_err_network")
        return self._t("update_error", e=detail or code)

    def _thread_check(self):
        info = updater.check_for_update()
        self.update_info = info
        if info.get("error"):
            self.update_state = "error"
            self.update_error = self._error_text(info["error"], info.get("detail", ""))
        elif info.get("available"):
            self.update_state = "available"
            self.update_banner = self._t("update_banner", ver=info["version"])
        else:
            self.update_state = "uptodate"
        self._update_ui_dirty = True

    def _start_download(self):
        if self.update_state not in ("available", "downloaded"):
            return
        info = self.update_info or {}
        url = info.get("url", "")
        if not url:
            self.update_state = "error"
            self.update_error = self._t("update_no_url")
            self._rebuild_update_ui()
            return
        self.update_state = "downloading"
        self.update_progress = 0.0
        self.update_error = ""
        self._rebuild_update_ui()
        threading.Thread(target=self._thread_download, args=(url,), daemon=True).start()

    def _thread_download(self, url):
        def progress(got, total):
            if total:
                self.update_progress = 100.0 * got / total
            self._update_ui_dirty = True
        try:
            self.update_installer = updater.download_installer(url, progress=progress)
            self.update_state = "downloaded"
        except Exception as e:  # noqa: BLE001
            self.update_state = "error"
            self.update_error = self._error_text(updater.error_code(e), str(e))
        self._update_ui_dirty = True

    def _install_update(self):
        if self.update_state != "downloaded" or not self.update_installer:
            return
        if updater.apply_update(self.update_installer):
            self.update_state = "installing"
            self._append_chat(self._t("update_installing"), COLOR_GREEN)
            self.done = True
        else:
            self.update_state = "error"
            self.update_error = self._t("update_apply_failed")
            self._rebuild_update_ui()

    def _rebuild_update_ui(self):
        self.buttons = []
        self.update_scroll = 0
        st = self.update_state
        if st in ("idle", "uptodate", "error"):
            self.buttons.append(Button((60, 700, 180, 44), self._t("update_check"),
                                       self._check_update_click))
        elif st == "available":
            self.buttons.append(Button((60, 700, 220, 44), self._t("update_download"),
                                       self._start_download))
        elif st == "downloaded":
            self.buttons.append(Button((60, 700, 220, 44), self._t("update_install"),
                                       self._install_update))
        self.buttons.append(Button((300, 700, 240, 44), self._t("update_open_page"),
                                   updater.open_release_page))
        self.buttons.append(Button((W - 180, 700, 150, 44), self._t("btn_back"),
                                   self._back_to_menu))

    def _draw_update(self):
        self._screen_header(self._t("update_title"))
        cur = self._t("update_current", v=version.__version__)
        t = get_font(18).render(cur, True, COLOR_TEXT)
        self.screen.blit(t, (W // 2 - 340, 120))
        st = self.update_state
        info = self.update_info or {}
        cx = W // 2 - 340
        if st == "checking":
            t = get_font(24).render(self._t("update_checking"), True, COLOR_DIM)
            self.screen.blit(t, (cx, 170))
        elif st == "uptodate":
            t = get_font(24).render(
                self._t("update_uptodate", v=info.get("current", version.__version__)),
                True, COLOR_GREEN)
            self.screen.blit(t, (cx, 170))
        elif st == "available":
            t = get_font(24).render(self._t("update_available", v=info.get("version", "")),
                                    True, COLOR_ACCENT)
            self.screen.blit(t, (cx, 170))
        elif st == "downloading":
            pct = max(0, min(100, int(self.update_progress)))
            t = get_font(24).render(self._t("update_downloading", p=pct),
                                    True, COLOR_ACCENT)
            self.screen.blit(t, (cx, 170))
            pygame.draw.rect(self.screen, COLOR_PANEL, (cx, 220, 680, 24), border_radius=6)
            if pct > 0:
                pygame.draw.rect(self.screen, COLOR_GOLD, (cx, 220, max(6, int(680 * pct / 100)), 24),
                                 border_radius=6)
        elif st == "downloaded":
            t = get_font(24).render(self._t("update_downloaded"), True, COLOR_GREEN)
            self.screen.blit(t, (cx, 170))
        elif st == "installing":
            t = get_font(24).render(self._t("update_installing"), True, COLOR_GREEN)
            self.screen.blit(t, (cx, 170))
        elif st == "error":
            t = get_font(22).render(self._t("update_error", e=self.update_error),
                                    True, COLOR_RED)
            self.screen.blit(t, (cx, 170))
        if not updater.is_frozen():
            t = get_font(16).render(self._t("update_src_hint"), True, COLOR_DIM)
            self.screen.blit(t, (cx, 262))
        notes = self._update_notes(info or {})
        if notes and st in ("available", "downloaded", "installing"):
            ver = info.get("version", "")
            self._panel(self.screen, (cx, 300, 680, 340))
            hd = get_font(18).render(self._t("update_changelog", v=ver),
                                     True, COLOR_ACCENT)
            self.screen.blit(hd, (cx + 16, 310))
            area = pygame.Rect(cx + 12, 342, 656, 290)
            self.screen.set_clip(area)
            lines = self._wrap_text(notes, get_font(17), area.width - 8)
            total_h = len(lines) * 25
            max_scroll = max(0, total_h - area.height + 6)
            self.update_scroll = min(self.update_scroll, max_scroll)
            yy = area.y + 4 - self.update_scroll
            for ln in lines:
                t = get_font(17).render(ln, True, COLOR_TEXT)
                self.screen.blit(t, (area.x + 4, yy))
                yy += 25
            self.screen.set_clip(None)
            if max_scroll > 0:
                hint = get_font(13).render(self._t("update_scroll_hint"),
                                           True, COLOR_DIM)
                self.screen.blit(hint, (area.right - hint.get_width(), area.bottom + 6))
        for b in self.buttons:
            b.draw(self.screen)

    # ---------- Drawing ----------

    def draw(self):
        if self.screen_name == "game":
            self.screen.fill(COLOR_BG)
        else:
            self._decor_bg()
        if self.screen_name == "menu":
            self._draw_menu()
        elif self.screen_name == "mods":
            self._draw_mods()
        elif self.screen_name == "market":
            self._draw_market()
        elif self.screen_name == "update":
            self._draw_update()
        elif self.screen_name == "lobby":
            self._draw_lobby()
        elif self.screen_name == "game":
            self._draw_game()
        elif self.screen_name == "over":
            self._draw_over()

    def _draw_menu(self):
        title = get_font(46).render(self._t("title"), True, COLOR_ACCENT)
        self.screen.blit(gfx.title_logo(64),
                         (W // 2 - title.get_width() // 2 - 86, 44))
        self.screen.blit(title, title.get_rect(center=(W // 2, 76)))
        sub = get_font(19).render(self._t("subtitle"), True, COLOR_DIM)
        self.screen.blit(sub, sub.get_rect(center=(W // 2, 118)))
        sy = 150
        if self.mod_names:
            t = get_font(14).render(self._t("mods_line", s=", ".join(self.mod_names)),
                                    True, COLOR_GOLD)
            self.screen.blit(t, t.get_rect(center=(W // 2, sy)))
            sy += 18
        if self.mod_errors:
            t = get_font(14).render(self._t("mods_error", s="; ".join(self.mod_errors)),
                                    True, COLOR_RED)
            self.screen.blit(t, t.get_rect(center=(W // 2, sy)))
            sy += 18
        if self.update_banner:
            t = get_font(14).render(self.update_banner, True, COLOR_GREEN)
            self.screen.blit(t, t.get_rect(center=(W // 2, sy)))
        # Three cards: game setup / avatar / tools
        self._panel(self.screen, (70, 196, 420, 300), self._t("menu_entry"))
        self._panel(self.screen, (500, 196, 340, 310), self._t("menu_avatar"))
        self._panel(self.screen, (860, 196, 340, 310), self._t("menu_tools"))
        for lbl, inp in [(self._t("lbl_name"), self.name_input),
                         (self._t("lbl_players"), self.players_input),
                         (self._t("lbl_join"), self.join_input)]:
            t = get_font(18).render(lbl, True, COLOR_TEXT)
            self.screen.blit(t, (90, inp.rect.y - 25))
            inp.draw(self.screen)
        if self.menu_note:
            t = get_font(14).render(self.menu_note, True, COLOR_DIM)
            self.screen.blit(t, (90, 486))
        # Avatar card content
        hint = get_font(14).render(self._t("avatar_hint"), True, COLOR_DIM)
        self.screen.blit(hint, (520, 216))
        preview = gfx.avatar_surface(self._avatar_payload(), 56)
        pygame.draw.circle(self.screen, COLOR_GOLD, (700, 230), 34, 3)
        self.screen.blit(preview, (672, 202))
        for b in self.avatar_buttons:
            b.draw(self.screen)
        self.avatar_path_input.draw(self.screen)
        if self.avatar_toast:
            t = get_font(14).render(self.avatar_toast, True, COLOR_GREEN)
            self.screen.blit(t, (520, 486))
        for b in self.buttons:
            b.draw(self.screen)
        # What's New panel (scrollable)
        self._draw_menu_news()

    def _update_notes(self, info):
        """Release notes for the current UI language (EN fallback), no CR."""
        raw = ""
        if self.lang == "zh":
            raw = str((info or {}).get("notes_zh", "") or "")
        if not raw:
            raw = str((info or {}).get("notes", "") or "")
        return raw.replace("\r", "")

    def _draw_menu_news(self):
        area = pygame.Rect(70, 522, 1130, 248)
        self._panel(self.screen, area, self._t("menu_whatsnew"))
        info = self.update_info or {}
        notes = self._update_notes(info)
        body = pygame.Rect(area.x + 16, area.y + 44, area.width - 32, area.height - 58)
        if self.update_state == "checking":
            t = get_font(17).render(self._t("menu_news_checking"), True, COLOR_DIM)
            self.screen.blit(t, (body.x, body.y))
            return
        if not notes:
            if self.update_state == "uptodate" and info.get("current"):
                t = get_font(17).render(
                    self._t("menu_news_uptodate", v=info.get("current")), True, COLOR_GREEN)
            else:
                t = get_font(17).render(self._t("menu_news_none"), True, COLOR_DIM)
            self.screen.blit(t, (body.x, body.y))
            return
        lines = self._wrap_text(notes, get_font(16), body.width - 8)
        total_h = len(lines) * 22
        max_scroll = max(0, total_h - body.height + 6)
        self.menu_news_scroll = min(self.menu_news_scroll, max_scroll)
        self.screen.set_clip(body)
        yy = body.y + 2 - self.menu_news_scroll
        for ln in lines:
            t = get_font(16).render(ln, True, COLOR_TEXT)
            self.screen.blit(t, (body.x + 4, yy))
            yy += 22
        self.screen.set_clip(None)
        if max_scroll > 0:
            hint = get_font(13).render(self._t("menu_news_hint"), True, COLOR_DIM)
            self.screen.blit(hint, (area.right - hint.get_width() - 14, area.y + 14))

    def _draw_lobby(self):
        self._screen_header(self._t("lobby_title"))
        info = self.lobby or {}
        joined = info.get("joined", [])
        # Left card: players + rename
        self._panel(self.screen, (70, 96, 500, 578), self._t("lobby_players"))
        y = 124
        for i, j in enumerate(joined):
            av = gfx.avatar_surface(j.get("avatar") or self._avatar_payload(), 40)
            self.screen.blit(av, (90, y + 3))
            tag = self._t("host_tag") if j.get("host") else ""
            if j.get("bot"):
                tag += self._t("bot_tag", l=self._t("lvl_" + str(j.get("bot") or "normal")))
            nm = get_font(21).render("{0}. {1}{2}".format(i + 1, tag, j["name"]),
                                     True, COLOR_TEXT)
            self.screen.blit(nm, (140, y + 7))
            p = j.get("personality")
            rx = 140 + nm.get_width() + 8
            rdy = j.get("ready")
            if rdy is not None:
                rt = get_font(14).render(self._t("ready_tag" if rdy else "notready_tag"),
                                         True, COLOR_GREEN if rdy else COLOR_DIM)
                self.screen.blit(rt, (rx, y + 11))
                rx += rt.get_width() + 12
            if p in ("paranoid", "greedy", "honest", "reckless"):
                pt = get_font(14).render(self._t("pers_tag", p=self._t("pers_" + p)),
                                         True, COLOR_GOLD)
                self.screen.blit(pt, (rx, y + 11))
            pygame.draw.line(self.screen, (50, 42, 34), (90, y + 44), (550, y + 44))
            y += 48
        t = get_font(17).render(self._t("joined", n=len(joined),
                                        m=info.get("max_players", "?")), True, COLOR_DIM)
        self.screen.blit(t, (90, y + 6))
        y += 30
        for key, kw in self.server_info:
            t = get_font(15).render(self._t(key, **kw), True, COLOR_DIM)
            self.screen.blit(t, (90, y))
            y += 21
        self._draw_block(self.screen, self._t("rule_hint"), 90, 584,
                         get_font(14), COLOR_GOLD, 470)
        t = get_font(16).render(self._t("lbl_name"), True, COLOR_TEXT)
        self.screen.blit(t, (90, 612))
        self.lobby_rename_input.draw(self.screen)
        # Right card: scrollable rule mods + host settings
        self._panel(self.screen, (600, 96, 600, 578), self._t("lobby_rules"))
        rmods = self.lobby_rules_mods or []
        area = pygame.Rect(610, 130, 580, 210)
        if not rmods:
            t = get_font(15).render(self._t("rmods_none"), True, COLOR_DIM)
            self.screen.blit(t, (610, 140))
        else:
            # Full detail rows: name/version/category line + up to 3 wrapped
            # description lines, so the detailed rules are actually readable.
            f13 = get_font(13)
            rows = []
            for m in rmods:
                desc = ((m.get("description_zh") or m.get("description") or "")
                        if self.lang == "zh" else (m.get("description") or ""))
                dlines = self._wrap_text(desc, f13, area.width - 16) if desc else []
                rows.append((m, dlines[:3]))
            heights = [44 + 17 * max(1, len(dl)) for m, dl in rows]
            total_h = sum(heights)
            max_scroll = max(0, total_h - area.height + 4)
            self.lobby_mods_scroll = min(self.lobby_mods_scroll, max_scroll)
            self.screen.set_clip(area)
            yy = 134 - self.lobby_mods_scroll
            for (m, dlines), row_h in zip(rows, heights):
                if yy + row_h - 4 < area.top or yy > area.bottom:
                    yy += row_h
                    continue
                nm = ((m.get("name_zh") or m.get("name") or m.get("id"))
                      if self.lang == "zh" else (m.get("name") or m.get("id")))
                cat = self._category_label(m.get("category", "rules"))
                t = get_font(16).render("- {0}  v{1}  {2}".format(nm, m.get("version", "?"), cat),
                                        True, COLOR_TEXT)
                self.screen.blit(t, (610, yy))
                dy = yy + 24
                for dl in dlines:
                    d = f13.render(dl, True, COLOR_DIM)
                    self.screen.blit(d, (626, dy))
                    dy += 17
                pygame.draw.line(self.screen, (50, 42, 34), (610, yy + row_h - 6),
                                 (1170, yy + row_h - 6))
                yy += row_h
            self.screen.set_clip(None)
            if max_scroll > 0:
                hint = get_font(13).render(self._t("list_scroll_hint"), True, COLOR_DIM)
                self.screen.blit(hint, (610, area.bottom + 6))
        fy = 354
        if self.lobby_rmods_conflicts:
            names = ", ".join(self._mod_display_name(a) + " x " + self._mod_display_name(b)
                              for a, b in self.lobby_rmods_conflicts)
            t = get_font(13).render(self._t("rmods_conflict", s=names), True, COLOR_RED)
            self.screen.blit(t, (610, fy))
            fy += 17
        for pm in self.lobby_players_mods:
            ok = self._pm_mods_ok(pm)
            col = COLOR_GREEN if ok else COLOR_RED
            txt = "{0}  {1}".format(pm.get("name", "?"),
                                    self._t("rmods_ok") if ok else self._t("rmods_missing"))
            t = get_font(13).render(txt, True, col)
            self.screen.blit(t, (610, fy))
            fy += 17
        if self.lobby_mods_toast:
            t = get_font(13).render(self.lobby_mods_toast, True, COLOR_GOLD)
            self.screen.blit(t, (610, fy))
            fy += 17
        pygame.draw.line(self.screen, (50, 42, 34), (610, 412), (1170, 412), 2)
        hy = getattr(self, "lobby_host_y", 420)
        if self.is_host:
            t = get_font(18).render(self._t("lobby_host"), True, COLOR_ACCENT)
            self.screen.blit(t, (610, hy))
            t = get_font(16).render(self._t("lbl_rounds"), True, COLOR_TEXT)
            self.screen.blit(t, (610, hy + 24))
            self.rounds_input.draw(self.screen)
            if getattr(self, "wild_input_visible", False):
                t = get_font(16).render(self._t("lbl_wild"), True, COLOR_TEXT)
                self.screen.blit(t, (740, hy + 24))
                self.wild_input.draw(self.screen)
            t = get_font(17).render(self._t("bots_title"), True, COLOR_ACCENT)
            self.screen.blit(t, (610, hy + 82))
            t = get_font(13).render(self._t("pers_title"), True, COLOR_TEXT)
            self.screen.blit(t, (610, hy + 140))
        for b in self.buttons:
            b.draw(self.screen)

    def _draw_stall(self, surf, x, y, legal_counts, contra_text):
        px = x
        prefix = get_font(15).render(self._t("stall"), True, COLOR_DIM)
        surf.blit(prefix, (px, y))
        px += prefix.get_width()
        f15 = get_font(15)
        for k, n in (legal_counts or {}).items():
            px += _out_blit(surf, f15, f"{self._tn(k)}x{n} ",
                            TYPE_COLOR.get(k, COLOR_TEXT), (px, y))
        if contra_text:
            px += _out_blit(surf, f15, contra_text, COLOR_CONTRA_TEXT, (px, y))

    def _draw_stall_colored(self, x, y, w, p):
        """Stall row in the player panel: every goods type uses its own color
        (colors come from the goods table, so reskin mods can change them)."""
        font = get_font(14)
        px = x
        prefix = font.render(self._t("stall"), True, COLOR_DIM)
        self.screen.blit(prefix, (px, y))
        px += prefix.get_width()
        for k, cnt in (p.get("stand_legal") or {}).items():
            part_w = font.render(f"{self._tn(k)}x{cnt} ", True,
                                 TYPE_COLOR.get(k, COLOR_TEXT)).get_width()
            if px + part_w > x + w:
                y += 18
                px = x
            px += _out_blit(self.screen, font, f"{self._tn(k)}x{cnt} ",
                            TYPE_COLOR.get(k, COLOR_TEXT), (px, y))
        for rt in (p.get("stand_royal") or []):
            rd = game.ROYAL_GOODS.get(rt)
            if not rd:
                continue
            base = TYPE_COLOR.get(rd["of"], COLOR_TEXT)
            part_txt = f"{self._tn(rt)}(={rd['equals']}{self._tn(rd['of'])}) "
            part_w = font.render(part_txt, True, base).get_width()
            if px + part_w > x + w:
                y += 18
                px = x
            px += _out_blit(self.screen, font, part_txt, base, (px, y))
        return y + 18

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

        # Rule-mod chips: trade route / bribe pot / action timer / guild contracts
        chips = []
        if v.get("route") and self._rule_mod_enabled("trade_caravans"):
            chips.append((self._t("chip_route_bonus", t=self._tn(v["route"]),
                                  g=game.ROUTE_BONUS), COLOR_GOLD))
        if self._rule_mod_enabled("bribe_pot"):
            chips.append((self._t("chip_pot", g=v.get("pot", 0)), COLOR_GOLD))
        tl = v.get("time_left")
        if tl is not None and self._rule_mod_enabled("night_market"):
            chips.append((self._t("chip_time", s=tl),
                          COLOR_RED if tl <= 10 else COLOR_GREEN))
        if self._rule_mod_enabled("guild_contracts"):
            youc = (v.get("you") or {}).get("contracts") or []
            if youc:
                legal = {}
                me_pub = {}
                if self.my_seat is not None and v.get("players"):
                    me_pub = v["players"][self.my_seat] or {}
                for k, cnt in (me_pub.get("stand_legal") or {}).items():
                    legal[k] = cnt
                for c in (v.get("you") or {}).get("stand_contra") or []:
                    if c.get("royal") and c.get("of"):
                        legal[c["of"]] = legal.get(c["of"], 0) + int(c.get("equals") or 2)
                for ct in youc:
                    have = legal.get(ct["type"], 0)
                    chips.append((self._t("contracts_chip", t=self._tn(ct["type"]),
                                          n=min(have, ct["need"]), m=ct["need"]),
                                  COLOR_GREEN if have >= ct["need"] else COLOR_TEXT))
        if chips:
            cx = 864
            for text, col in reversed(chips):
                t = get_font(14).render(text, True, col)
                w = t.get_width() + 16
                cx -= w
                pygame.draw.rect(self.screen, (56, 48, 38), (cx, 38, w, 24),
                                 border_radius=12)
                self.screen.blit(t, (cx + 8, 41))

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
            self.screen.blit(gfx.avatar_surface(p.get("avatar"), 34), (x + pw - 42, py + 8))
            t = get_font(17).render(tag + p["name"], True, col)
            self.screen.blit(t, (nx, py + 6))
            yy = py + 30
            gold = self._t("gold_hand", g=p["gold"], h=p["hand_count"])
            self.screen.blit(gfx.coin(16), (x + 8, yy + 2))
            yy = self._draw_block(self.screen, gold, x + 26, yy, get_font(15),
                                  COLOR_TEXT, max(40, pw - 56)) + 2
            if p.get("bag_size"):
                yy = self._draw_block(self.screen,
                                      self._t("bag_sealed", n=p["bag_size"]),
                                      x + 8, yy, get_font(14), COLOR_GOLD, pw - 16) + 2
            if self._rule_mod_enabled("merchant_reputation") and p.get("reputation"):
                t = get_font(13).render(self._t("rep_chip", n=p["reputation"]),
                                        True, COLOR_GOLD)
                self.screen.blit(t, (x + pw - t.get_width() - 6, py + 70))
            if self._rule_mod_enabled("royal_favor") and p.get("royal_favor"):
                t = get_font(13).render(self._t("favor_chip", n=p["royal_favor"]),
                                        True, COLOR_GOLD)
                self.screen.blit(t, (x + pw - t.get_width() - 6, py + 88))
            if not p.get("connected", True):
                t = get_font(15).render(self._t("offline_tag"), True, COLOR_RED)
                self.screen.blit(t, (x + 8, yy)); yy += 20
            if p.get("decl"):
                d = p["decl"]
                _out_blit(self.screen, get_font(15),
                          self._t("declared", t=self._tn(d["type"]), c=d["count"]),
                          TYPE_COLOR.get(d["type"], COLOR_GREEN), (x + 8, yy))
                yy += 20
            yy = self._draw_stall_colored(x + 8, yy, pw - 16, p) + 4
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
                if prompt.get("bribe_gold", 0) > 0 and \
                        prompt.get("round", 0) < prompt.get("max_round", 99):
                    instr += self._t("counter_left",
                                     n=prompt.get("max_round", 99) - prompt.get("round", 0))
            else:
                instr = self._t("instr_inspect", name=prompt.get("owner", "?"))
        elif kind == "counter_bribe":
            instr = self._t("instr_counter_bribe",
                            d=prompt.get("demand", 0),
                            o=prompt.get("last_offer", 0),
                            n=prompt.get("max_round", 99) - prompt.get("round", 0))
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
                "market_discard": self._t("instr_waiting_market"),
                "market_draw": self._t("instr_waiting_market"),
                "load": self._t("instr_waiting_load"),
                "declare": self._t("instr_waiting_declare_all"),
                "bribe": self._t("instr_waiting_bribe", name=acting),
                "counter_bribe": self._t("instr_waiting_counter_bribe", name=acting),
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

        # Chat panel (scrollable history)
        pygame.draw.rect(self.screen, COLOR_PANEL, (880, 60, 390, 680), border_radius=8)
        t = get_font(18).render(self._t("chat_title"), True, COLOR_ACCENT)
        self.screen.blit(t, (890, 66))
        body = pygame.Rect(890, 96, 372, 622)
        font = get_font(16)
        lines = []
        for text, col in self.chat_log:
            for ln in self._wrap_text(text, font, 360):
                lines.append((ln, col))
        line_h = 20
        visible = max(1, body.height // line_h)
        max_scroll = max(0, len(lines) - visible)
        self.chat_max_scroll = max_scroll
        self.chat_scroll = min(int(self.chat_scroll), max_scroll)
        start = max(0, len(lines) - visible - self.chat_scroll)
        self.screen.set_clip(body)
        y = body.bottom - 4
        for i in range(len(lines) - 1, start - 1, -1):
            text, col = lines[i]
            rt = font.render(text, True, col or COLOR_TEXT)
            y -= line_h
            if y < body.top:
                break
            self.screen.blit(rt, (body.x, y))
        self.screen.set_clip(None)
        if max_scroll > 0:
            # scrollbar: wider track + visible knob + track-click paging.
            track = pygame.Rect(body.right - 13, body.y, 10, body.height)
            pygame.draw.rect(self.screen, (42, 36, 28), track, border_radius=4)
            hh = max(26, int(body.height * visible / max(1, len(lines))))
            frac = self.chat_scroll / max(1, max_scroll)
            hy = body.y + int(frac * (body.height - hh))
            knob = pygame.Rect(track.x + 1, hy, track.width - 2, hh)
            pygame.draw.rect(self.screen, COLOR_ACCENT, knob, border_radius=4)
            pygame.draw.rect(self.screen, (46, 36, 24), knob, 1, border_radius=4)
            self.chat_thumb = knob
            hint = get_font(13).render(self._t("chat_scroll_hint"), True, COLOR_DIM)
            self.screen.blit(hint, (880 + 390 - hint.get_width() - 24, 70))
        else:
            self.chat_thumb = None
        self.chat_input.draw(self.screen)

        pk = (prompt or {}).get("kind")
        if pk in ("bribe", "inspect", "counter_bribe"):
            label = self._t("bribe_gold") if pk == "bribe" else self._t("lbl_counter_amount")
            t = get_font(16).render(label, True, COLOR_TEXT)
            self.screen.blit(t, (40, 646))
            self.gold_input.draw(self.screen)
            if pk == "bribe":
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
        pygame.draw.rect(self.screen, COLOR_PANEL, (20, 268, 860, 36 + n_groups * 44),
                         border_radius=8)
        t = get_font(16).render(self._t("bm_title"), True, COLOR_ACCENT)
        self.screen.blit(t, (30, 276))
        y = 292
        for t_ in types:
            _out_blit(self.screen, get_font(15), self._tn(t_),
                      TYPE_COLOR.get(t_, COLOR_TEXT), (30, y))
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
            # Progress stays secret: nobody sees who is close to a quest.
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
                self.screen.blit(gfx.avatar_surface(r.get("avatar"), 40), (34, y - 2))
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
                    elif e["kind"] == "pot":
                        for a in e["awards"]:
                            parts.append(f"{a['name']}+{a['bonus']}")
                        head = self._t("over_pot")
                    else:  # black market cards
                        for a in e["awards"]:
                            parts.append(f"{a['name']}+{a['bonus']}")
                        head = self._t("bm_tag")
                    line = f"{head}: " + ", ".join(parts)
                    _out_blit(self.screen, get_font(17), line,
                              TYPE_COLOR.get(e["type"], COLOR_TEXT), (640, ty))
                    ty += 26
        for b in self.buttons:
            b.draw(self.screen)

    def _wrap_text(self, text, font, max_w):
        """Split text into lines that fit max_w pixels (CJK-safe, newline-aware:
        every line break in the source becomes a paragraph break)."""
        lines = []
        for para in str(text).split("\n"):
            if not para.strip():
                lines.append("")
                continue
            cur = ""
            for w in para.split(" "):
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
            lines.append("")
        while lines and lines[-1] == "":
            lines.pop()
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
            if self._update_ui_dirty:
                self._update_ui_dirty = False
                if self.screen_name == "update":
                    self._rebuild_update_ui()
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
