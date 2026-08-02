# -*- coding: utf-8 -*-
"""Reskin mod tests: every bundled reskin mod renames goods + chat messages,
and the mod market installs zips from a manifest.

Usage: python test_reskin_mods.py
"""
import io
import json
import os
import shutil
import tempfile

import game
import gui  # noqa: F401  (mods registers colors into gui)
import lang
import market
import mods

RESKIN_MODS = ["cyberpunk_mod", "medieval_mod", "starlight_mod",
               "steampunk_mod", "arcane_mod"]


def _snapshot():
    return {
        "TYPE_EN": dict(game.TYPE_EN), "TYPE_ZH": dict(game.TYPE_ZH),
        "LZH": dict(lang.TYPE_ZH), "COLOR": dict(gui.TYPE_COLOR),
        "PHASES": {k: dict(v) for k, v in lang.PHASES.items()},
        "UI": {k: dict(v) for k, v in lang.UI.items()},
        "RENAME_MAP": dict(lang.RENAME_MAP),
    }


def _restore(snap):
    game.TYPE_EN.clear(); game.TYPE_EN.update(snap["TYPE_EN"])
    game.TYPE_ZH.clear(); game.TYPE_ZH.update(snap["TYPE_ZH"])
    lang.TYPE_ZH.clear(); lang.TYPE_ZH.update(snap["LZH"])
    gui.TYPE_COLOR.clear(); gui.TYPE_COLOR.update(snap["COLOR"])
    lang.PHASES = {k: dict(v) for k, v in snap["PHASES"].items()}
    lang.UI = {k: dict(v) for k, v in snap["UI"].items()}
    lang.RENAME_MAP.clear(); lang.RENAME_MAP.update(snap["RENAME_MAP"])
    lang.rebuild_names()


def _set_enabled(base, folder, enabled):
    mpath = os.path.join(base, folder, "mod.json")
    with io.open(mpath, encoding="utf-8") as f:
        m = json.load(f)
    m["enabled"] = enabled
    with io.open(mpath, "w", encoding="utf-8") as f:
        json.dump(m, f)


def main():
    snap = _snapshot()
    old_env = os.environ.get("SHERIFF_MODS_DIR")
    tmp = tempfile.mkdtemp(prefix="sheriff_reskin_")
    try:
        base = os.path.join(tmp, "mods")
        for folder in RESKIN_MODS:
            shutil.copytree(os.path.join("mods", folder), os.path.join(base, folder))
        os.environ["SHERIFF_MODS_DIR"] = base

        for folder in RESKIN_MODS:
            for other in RESKIN_MODS:
                _set_enabled(base, other, other == folder)
            loaded, errors = mods.load_mods()
            assert len(loaded) == 1, (folder, [m["id"] for m in loaded])
            assert not errors, errors
            en, zh = game.TYPE_EN["APPLE"], game.TYPE_ZH["APPLE"]
            assert en != "Apple" and zh != "\u82f9\u679c", (folder, en, zh)
            assert "Apple" in lang.RENAME_MAP and "Silk" in lang.RENAME_MAP
            apple_en, apple_zh = lang.RENAME_MAP["Apple"]
            silk_en, silk_zh = lang.RENAME_MAP["Silk"]
            t_zh = lang.translate("Inspected 2 Apple, 1 Silk, fine 4 gold", "zh")
            assert apple_zh in t_zh and "Apple" not in t_zh, (folder, apple_zh, t_zh)
            t_en = lang.translate("Inspected 2 Apple, 1 Silk, fine 4 gold", "en")
            assert apple_en in t_en, (folder, apple_en, t_en)
            t_x = lang.translate("seized (Silkx2, Wine)", "zh")
            assert silk_zh in t_x, (folder, silk_zh, t_x)
            assert game.TYPE_EN["ROYAL_CHICKEN"] != "Royal Chicken"
            print("PASS reskin:", folder)
            _restore(snap)
        print("PASS all reskin mods")

        # ---- mod market: local file:// install + status ----
        market_base = os.path.join(tmp, "market_mods")
        os.makedirs(market_base)
        for key, folder in [("cyberpunk", "cyberpunk_mod"),
                            ("medieval", "medieval_mod")]:
            info = {"id": key, "folder": folder, "version": "9.9.9",
                    "url": "file:///" + os.path.abspath(
                        os.path.join("mods_pack", folder + ".zip")).replace("\\", "/")}
            st, _ = market.local_status(info, market_base)
            assert st == "missing", (folder, st)
            ok, msg = market.install_mod(info, market_base)
            assert ok, (folder, msg)
            assert os.path.isfile(os.path.join(market_base, folder, "mod.json"))
            st, ver = market.local_status(info, market_base)
            assert st == "update" and ver, (folder, st, ver)
            mpath = os.path.join(market_base, folder, "mod.json")
            with io.open(mpath, encoding="utf-8") as f:
                m = json.load(f)
            m["version"] = "10.0.0"
            with io.open(mpath, "w", encoding="utf-8") as f:
                json.dump(m, f)
            st, ver = market.local_status(info, market_base)
            assert st == "installed" and ver == "10.0.0", (folder, st, ver)
            print("PASS market install:", folder)
        bad = {"id": "bad", "folder": "bad_mod",
               "url": "file:///" + os.path.abspath("mods_pack/README.md").replace("\\", "/")}
        ok, msg = market.install_mod(bad, market_base)
        assert not ok and msg, "bad zip should fail"
        print("PASS market rejects invalid zip")
    finally:
        _restore(snap)
        if old_env is None:
            os.environ.pop("SHERIFF_MODS_DIR", None)
        else:
            os.environ["SHERIFF_MODS_DIR"] = old_env
        shutil.rmtree(tmp, ignore_errors=True)

    assert game.TYPE_EN["APPLE"] == "Apple", "state not restored"
    assert lang.RENAME_MAP == {}, "RENAME_MAP not restored"
    print("PASS state restored")
    print("ALL RESKIN + MARKET TESTS PASSED")


if __name__ == "__main__":
    main()
