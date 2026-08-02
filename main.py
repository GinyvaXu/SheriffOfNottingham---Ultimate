# -*- coding: utf-8 -*-
"""Entry point: python main.py --host / --join ip:port"""

import argparse

import net
import version
from gui import App


def main():
    ap = argparse.ArgumentParser(description="Sheriff of Nottingham - Lite Online")
    ap.add_argument("--host", action="store_true", help="host a room (this machine is the server)")
    ap.add_argument("--players", type=int, default=4, help="max players 2-5, default 4")
    ap.add_argument("--port", type=int, default=net.DEFAULT_PORT, help=f"listen port, default {net.DEFAULT_PORT}")
    ap.add_argument("--name", default="", help="your name")
    ap.add_argument("--join", default="", help="join a room, e.g. 192.168.1.5:5555")
    ap.add_argument("--lang", default="zh", choices=["zh", "en"], help="ui language, default zh")
    ap.add_argument("--version", action="version",
                    version=f"SheriffOfNottingham {version.__version__}")
    ap.add_argument("--no-royal", action="store_true",
                    help="disable royal goods cards (12 high-value contraband, count as x2 legal)")
    ap.add_argument("--no-blackmarket", action="store_true",
                    help="disable black market quests (3 groups x 2 rewards)")
    args = ap.parse_args()
    App(host=args.host, players=args.players, port=args.port, name=args.name,
        join=args.join, lang_name=args.lang,
        royal=not args.no_royal, black_market=not args.no_blackmarket).run()


if __name__ == "__main__":
    main()
