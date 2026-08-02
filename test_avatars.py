# -*- coding: utf-8 -*-
"""Avatar/profile tests.

1. profile.json save/load round trip + avatar payload normalization.
2. gfx renders builtin avatars and round-trips a custom image.
3. Online: the hello message carries the avatar; the lobby "joined" list and
   the in-game player views expose it to every client.

Usage: python test_avatars.py
"""
import io as _io
import os
import tempfile
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402

import gfx  # noqa: E402
import net  # noqa: E402
import profile  # noqa: E402


def _wait_lobby_cond(client, pred, timeout=8):
    deadline = time.time() + timeout
    while time.time() < deadline:
        for m in client.poll():
            if m.get("t") == "lobby" and pred(m):
                return m
        time.sleep(0.05)
    return None


def _drain(client, timeout=1.2):
    time.sleep(timeout)
    return [m for m in client.poll()]


def main():
    ok = True
    # ---- 1. profile round trip ----
    tmp = tempfile.mkdtemp(prefix="sheriff_avatar_")
    old_app = profile.app_dir
    profile.app_dir = lambda: tmp
    profile.load_profile.cache_clear() if hasattr(profile.load_profile, "cache_clear") else None
    p = profile.default_profile()
    p["name"] = "Alice"
    p["avatar"] = "wizard"
    assert profile.save_profile(p)
    loaded = profile.load_profile()
    if loaded["name"] != "Alice" or loaded["avatar"] != "wizard":
        print("FAIL profile round trip:", loaded)
        ok = False
    else:
        print("PASS profile save/load round trip")
    # payload + normalization
    pay = profile.avatar_payload(loaded)
    if pay != {"kind": "builtin", "id": "wizard"}:
        print("FAIL builtin payload:", pay)
        ok = False
    if profile.avatar_from_payload({"kind": "builtin", "id": "bogus"})["id"] != "pig":
        print("FAIL bogus avatar id not normalized")
        ok = False
    if profile.avatar_from_payload({"kind": "custom", "data": "aaaa"})["kind"] != "custom":
        print("FAIL custom payload normalization")
        ok = False
    print("PASS avatar payload normalization")
    profile.app_dir = old_app

    # ---- 2. gfx rendering ----
    pygame.init()
    for k in profile.BUILTIN_AVATARS:
        s = gfx.avatar_surface({"kind": "builtin", "id": k}, 48)
        if s.get_width() != 48:
            print("FAIL builtin avatar render:", k)
            ok = False
            break
    print("PASS gfx renders all builtin avatars")
    surf = pygame.Surface((64, 64), pygame.SRCALPHA)
    pygame.draw.circle(surf, (200, 50, 50), (32, 32), 30)
    data, enc_ok = profile.encode_png(surf, size=128)
    if not enc_ok or not data:
        print("FAIL custom avatar encode")
        ok = False
    else:
        cp = profile.default_profile()
        cp["custom_avatar"] = data
        s2 = gfx.avatar_surface(profile.avatar_payload(cp), 56)
        if s2.get_width() != 56:
            print("FAIL custom avatar render")
            ok = False
        else:
            print("PASS custom avatar encode/render round trip")

    # ---- 3. online flow ----
    srv = net.GameServer(4, port=5606)
    av_h = {"kind": "builtin", "id": "knight"}
    av_g = {"kind": "builtin", "id": "wizard"}
    host = net.GameClient("127.0.0.1", 5606, "Host", avatar=av_h)
    guest = net.GameClient("127.0.0.1", 5606, "Guest", avatar=av_g)
    hl = _wait_lobby_cond(host, lambda m: len(m.get("joined", [])) == 2)
    gl = _wait_lobby_cond(guest, lambda m: len(m.get("joined", [])) == 2)
    if not (hl and gl):
        print("FAIL: players did not reach lobby")
        ok = False
    else:
        by_name = {j["name"]: j.get("avatar") for j in hl.get("joined", [])}
        if by_name.get("Host") != av_h or by_name.get("Guest") != av_g:
            print("FAIL lobby joined avatars:", by_name)
            ok = False
        else:
            print("PASS lobby joined carries avatars")
        host.send({"t": "start_game", "rounds": 2})
        views = _drain(guest, 1.5)
        view = next((m for m in views if m.get("t") == "view"), None)
        if view is None:
            print("FAIL: no view received")
            ok = False
        else:
            plist = view.get("players") or []
            got = {p["name"]: p.get("avatar") for p in plist}
            if got.get("Host") != av_h or got.get("Guest") != av_g:
                print("FAIL in-game player avatars:", got)
                ok = False
            else:
                print("PASS in-game player views carry avatars")
    host.close()
    guest.close()
    srv.stop()

    print("ALL AVATAR TESTS PASSED" if ok else "AVATAR TESTS FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
