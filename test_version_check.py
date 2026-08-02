# -*- coding: utf-8 -*-
"""Test: join-version check - host rejects clients whose version differs.

Usage: python test_version_check.py
"""
import json
import socket

import net
import version


def _raw_hello(port, name, ver):
    s = socket.create_connection(("127.0.0.1", port), timeout=5)
    hello = {"t": "hello", "name": name, "mods": [], "avatar": None, "ver": ver}
    s.sendall((json.dumps(hello, ensure_ascii=False) + "\n").encode("utf-8"))
    s.settimeout(5)
    data = b""
    try:
        while b"\n" not in data:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
    except OSError:
        pass
    s.close()
    if not data:
        return None
    return json.loads(data.split(b"\n")[0])


def main():
    port = 58733
    srv = net.GameServer(4, port=port)
    try:
        m = _raw_hello(port, "OldGuy", "0.9.9")
        if not m or m.get("t") != "error" or m.get("code") != "version":
            print("FAIL: old-version client was not rejected:", m)
            return 1
        print("version mismatch rejected OK:", m.get("msg"))

        m = _raw_hello(port, "NewGuy", version.__version__)
        if not m or m.get("t") != "welcome":
            print("FAIL: same-version client not welcomed:", m)
            return 1
        print("same-version welcome OK, seat:", m.get("seat"))

        m = _raw_hello(port, "Ancient", "")
        if not m or m.get("t") != "error" or m.get("code") != "version":
            print("FAIL: empty-version client was not rejected:", m)
            return 1
        print("empty-version rejected OK")
    finally:
        srv.stop()
    print("PASS: version check")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
