# -*- coding: utf-8 -*-
"""Mod loader tests: temp mods add card types / patch engine, then state is restored.

Usage: python test_mods.py
"""
import json
import os
import random
import shutil
import sys
import tempfile

import game
import gui  # noqa: F401  (mods registers colors into gui)
import lang
import mods


def _snapshot():
    return {
        "LEGAL": list(game.LEGAL),
        "CONTRABAND": list(game.CONTRABAND),
        "ROYAL_TYPES": list(game.ROYAL_TYPES),
        "ROYAL_TYPE_OF": dict(game.ROYAL_TYPE_OF),
        "ALL_TYPES": list(game.ALL_TYPES),
        "GOODS": dict(game.GOODS),
        "ROYAL_GOODS": dict(game.ROYAL_GOODS),
        "TYPE_EN": dict(game.TYPE_EN),
        "TYPE_ZH": dict(game.TYPE_ZH),
        "LANG_ZH": dict(lang.TYPE_ZH),
        "COLOR": dict(gui.TYPE_COLOR),
        "KING": dict(game.KING_BONUS),
        "QUEEN": dict(game.QUEEN_BONUS),
        "HAND_SIZE": game.HAND_SIZE,
    }


def _restore(snap):
    game.LEGAL[:] = snap["LEGAL"]
    game.CONTRABAND[:] = snap["CONTRABAND"]
    game.ROYAL_TYPES[:] = snap["ROYAL_TYPES"]
    game.ROYAL_TYPE_OF.clear(); game.ROYAL_TYPE_OF.update(snap["ROYAL_TYPE_OF"])
    game.ALL_TYPES[:] = snap["ALL_TYPES"]
    game.GOODS.clear(); game.GOODS.update(snap["GOODS"])
    game.ROYAL_GOODS.clear(); game.ROYAL_GOODS.update(snap["ROYAL_GOODS"])
    game.TYPE_EN.clear(); game.TYPE_EN.update(snap["TYPE_EN"])
    game.TYPE_ZH.clear(); game.TYPE_ZH.update(snap["TYPE_ZH"])
    lang.TYPE_ZH.clear(); lang.TYPE_ZH.update(snap["LANG_ZH"])
    gui.TYPE_COLOR.clear(); gui.TYPE_COLOR.update(snap["COLOR"])
    game.KING_BONUS.clear(); game.KING_BONUS.update(snap["KING"])
    game.QUEEN_BONUS.clear(); game.QUEEN_BONUS.update(snap["QUEEN"])
    game.HAND_SIZE = snap["HAND_SIZE"]
    lang.rebuild_names()


def _write_mod(base, name, enabled, py=""):
    folder = os.path.join(base, name)
    os.makedirs(folder, exist_ok=True)
    manifest = {"id": name, "name": name.title(), "version": "0.1.0",
                "enabled": enabled}
    with open(os.path.join(folder, "mod.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f)
    if py:
        with open(os.path.join(folder, "mod.py"), "w", encoding="utf-8") as f:
            f.write(py)


def main():
    snap = _snapshot()
    old_env = os.environ.get("SHERIFF_MODS_DIR")
    tmp = tempfile.mkdtemp(prefix="sheriff_mods_")
    try:
        base = os.path.join(tmp, "mods")
        os.makedirs(base)
        # enabled mod: adds TEA contraband, PEAR legal, patches HAND_SIZE
        _write_mod(base, "tea_mod", True, '''
def register(api):
    api.add_contraband("TEA", "Tea", "\\u8336\\u53f6", value=5, fine=3,
                       cnt3=8, cnt6=12, color=(96, 156, 120))
    api.add_legal("PEAR", "Pear", "\\u68a8\\u5b50", value=2, fine=2,
                  cnt3=10, cnt6=14, king_bonus=10, queen_bonus=5)
    api.patch("game", "HAND_SIZE", 7)
''')
        # disabled mod must be skipped
        _write_mod(base, "off_mod", False, '''
def register(api):
    api.add_contraband("SALT", "Salt", "\\u76d0", value=4, fine=2)
''')
        # broken mod must not crash the loader
        _write_mod(base, "bad_mod", True, 'raise RuntimeError("boom")')

        os.environ["SHERIFF_MODS_DIR"] = base
        loaded, errors = mods.load_mods()

        assert [m["id"] for m in loaded] == ["tea_mod"], loaded
        assert any("bad_mod" in e for e in errors), errors
        print("load ok:", loaded, "| errors:", errors)

        assert "TEA" in game.CONTRABAND and "TEA" in game.GOODS
        assert "PEAR" in game.LEGAL and "PEAR" in game.GOODS
        assert "SALT" not in game.CONTRABAND, "disabled mod should be skipped"
        assert game.GOODS["TEA"] == {"value": 5, "fine": 3, "cnt3": 8, "cnt6": 12}
        assert game.KING_BONUS.get("PEAR") == 10
        assert game.HAND_SIZE == 7, "patch should change HAND_SIZE"
        assert lang.TYPE_ZH.get("TEA") == "\u8336\u53f6"
        assert gui.TYPE_COLOR.get("TEA") == (96, 156, 120)
        assert "PEAR" in game.ALL_TYPES
        print("PASS content registration + patch")

        # deck built after mod load contains the new cards
        g = game.Game([game.Player("A"), game.Player("B")],
                      rng=random.Random(7), black_market=False)
        deck_types = [c["type"] for c in g.deck]
        assert "TEA" in deck_types and "PEAR" in deck_types, "deck missing mod cards"
        print("PASS deck contains mod cards")

        # declare flow accepts the new legal type
        g2 = game.Game([game.Player("A"), game.Player("B")],
                       rng=random.Random(8), black_market=False)
        g2.start_round()
        g2.phase = "DECLARE"
        seat = g2.declare_current()
        g2.players[seat].bag = [{"type": "PEAR", "value": 2, "fine": 2}]
        ok, err = g2.do_declare(seat, "PEAR")
        assert ok, err
        print("PASS declare mod legal type")
        # ---- regression: toggle enabled on a BOM-prefixed mod.json ----
        bom_folder = os.path.join(base, "bom_mod")
        os.makedirs(bom_folder, exist_ok=True)
        bom_path = os.path.join(bom_folder, "mod.json")
        with open(bom_path, "w", encoding="utf-8-sig") as f:  # writes a UTF-8 BOM
            json.dump({"id": "bom_mod", "name": "Bom Mod", "version": "0.1.0",
                       "enabled": False}, f)
        assert mods.set_enabled("bom_mod", True), "toggle on with BOM mod.json failed"
        with open(bom_path, encoding="utf-8-sig") as f:
            assert json.load(f)["enabled"] is True
        assert mods.set_enabled("bom_mod", False), "toggle off with BOM mod.json failed"
        print("PASS toggle enabled with BOM mod.json")

        # ---- regression: read-only mod.json is made writable before saving ----
        ro_folder = os.path.join(base, "ro_mod")
        os.makedirs(ro_folder, exist_ok=True)
        ro_path = os.path.join(ro_folder, "mod.json")
        with open(ro_path, "w", encoding="utf-8") as f:
            json.dump({"id": "ro_mod", "name": "Ro Mod", "version": "0.1.0",
                       "enabled": False}, f)
        if sys.platform.startswith("win"):
            os.chmod(ro_path, 0o444)  # set the read-only attribute
        assert mods.set_enabled("ro_mod", True), "toggle read-only mod.json failed"
        with open(ro_path, encoding="utf-8") as f:
            assert json.load(f)["enabled"] is True
        print("PASS toggle read-only mod.json")

        # ---- regression: per-user fallback base + mod migration ----
        fb_src = os.path.join(tmp, "fb_src")
        fb_dst = os.path.join(tmp, "fb_dst")
        os.makedirs(os.path.join(fb_src, "fb_mod"))
        os.makedirs(os.path.join(fb_src, "plain_dir"))
        with open(os.path.join(fb_src, "fb_mod", "mod.json"), "w",
                  encoding="utf-8") as f:
            json.dump({"id": "fb_mod", "enabled": True}, f)
        with open(os.path.join(fb_src, "plain_dir", "notes.txt"), "w") as f:
            f.write("x")
        assert mods._migrate_mods(fb_src, fb_dst), "migration failed"
        assert os.path.isfile(os.path.join(fb_dst, "fb_mod", "mod.json"))
        assert not os.path.isdir(os.path.join(fb_dst, "plain_dir")),             "folders without mod.json must not migrate"
        assert mods._is_writable_dir(fb_dst)
        assert mods.set_enabled("fb_mod", False, base=fb_dst), "toggle in fallback base failed"
        with open(os.path.join(fb_dst, "fb_mod", "mod.json"), encoding="utf-8") as f:
            assert json.load(f)["enabled"] is False
        print("PASS per-user fallback base + migration")

    finally:
        _restore(snap)
        mods.reset_mods_base_cache()
        if old_env is None:
            os.environ.pop("SHERIFF_MODS_DIR", None)
        else:
            os.environ["SHERIFF_MODS_DIR"] = old_env
        shutil.rmtree(tmp, ignore_errors=True)

    assert "TEA" not in game.CONTRABAND, "state not restored"
    assert game.HAND_SIZE == 6, "HAND_SIZE not restored"
    print("PASS state restored after tests")
    print("ALL MOD TESTS PASSED")


if __name__ == "__main__":
    main()
