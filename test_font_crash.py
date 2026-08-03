# -*- coding: utf-8 -*-
"""Regression: the 6-player "Passed a NULL pointer" crash.

Root cause (v1.7.3): ``_draw_player_panel`` shrank name fonts with
``get_font(font.get_height() - 1)``. The pixel line height is *larger* than
the point size, so the loop actually grew the font (height 20 -> 33 -> 43 ->
...) instead of shrinking it. In 5-6 player rooms the panels are narrow, the
name does not fit, and the loop ramped the size until SDL_ttf refused to
open the font; pygame then returned a Font with a NULL internal pointer and
the next ``size()`` raised ``pygame.error: Passed a NULL pointer``.

Also covered: ``get_font`` must skip corrupt/truncated font files (pygame
creates a broken Font for them silently) instead of handing them out.

Usage: python test_font_crash.py
"""
import io as _io
import os
import tempfile

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402

import gui  # noqa: E402


def _setup():
    pygame.init()
    pygame.display.set_mode((100, 100))
    gui._FONT_CACHE.clear()


def test_fit_name_font_shrinks_and_terminates():
    _setup()
    font, text = gui.fit_name_font("Sheriff-of-Nottingham", 98, 15, 9)
    assert font.get_height() <= gui.get_font(15).get_height(), (
        "font must never grow")
    assert font.size(text)[0] <= 98, (text, font.size(text)[0])


def test_fit_name_font_trims_absurd_names():
    _setup()
    font, text = gui.fit_name_font("x" * 200, 60, 15, 9)
    assert font.size(text)[0] <= 60, (text, font.size(text)[0])
    assert text.endswith("\u2026"), text


def test_fit_name_font_handles_tiny_width():
    _setup()
    font, text = gui.fit_name_font("A", 0, 15, 9)  # must not raise or loop
    assert font.size(text)[0] >= 0


def test_get_font_skips_corrupt_candidates():
    _setup()
    tmp = os.path.join(tempfile.gettempdir(), "corrupt_font_test.ttf")
    with open(tmp, "wb") as fh:
        fh.write(b"garbage-not-a-font" * 20)
    try:
        orig = gui._font_candidates
        gui._font_candidates = lambda: [tmp] + orig()
        gui._FONT_CACHE.clear()
        try:
            f = gui.get_font(16)
            # a usable font must have been found (corrupt file skipped)
            assert f.size("test")[0] > 0
        finally:
            gui._font_candidates = orig
            gui._FONT_CACHE.clear()
    finally:
        os.remove(tmp)


def test_6p_game_draw_long_names_no_crash():
    """Render the real 6-player game screen with long names (the original
    crash repro: narrow panels + long names + every draw frame)."""
    from gui import App, W, H  # noqa: E402
    _setup()
    app = App(lang_name="zh", name="Me")
    app.screen_name = "game"
    app.my_seat = 0
    names = ["Me", "Sheriff-of-Nottingham", "Very Long Player Name Here",
             "Carol", "Dave", "Eve"]
    players = [{"name": names[i],
                "avatar": {"kind": "builtin", "id": "pig"},
                "gold": 30, "hand_count": 6, "bag_size": 3,
                "stand_legal": {"APPLE": 2}, "stand_royal": [],
                "connected": True, "decl": None} for i in range(6)]
    view = {"t": "view", "phase": "INSPECT", "round": 1, "rounds_total": 9,
            "sheriff": 1, "players": players, "deck_count": 12,
            "you": {"hand": [], "bag": [], "stand_contra": [],
                    "black_market_cards": 0},
            "prompt": None, "black_market": None}
    app.view = view
    app.game_lay = None
    app._fade_t = None
    app._present_valid = False
    for _ in range(3):          # several frames, like a live game
        app.draw()
    assert True


if __name__ == "__main__":
    import traceback
    failed = 0
    for fn in [test_fit_name_font_shrinks_and_terminates,
               test_fit_name_font_trims_absurd_names,
               test_fit_name_font_handles_tiny_width,
               test_get_font_skips_corrupt_candidates,
               test_6p_game_draw_long_names_no_crash]:
        try:
            fn()
            print("PASS", fn.__name__)
        except Exception:
            failed += 1
            print("FAIL", fn.__name__)
            traceback.print_exc()
    raise SystemExit(1 if failed else 0)
