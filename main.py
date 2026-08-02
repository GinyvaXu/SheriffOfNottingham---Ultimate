# -*- coding: utf-8 -*-
"""Entry point: python main.py --host / --join ip:port"""

import argparse
import sys

import mods
import net
import version
from gui import App


def _show_version():
    """Show the version in a message box (works in the windowed exe too)."""
    text = f"Sheriff of Nottingham v{version.__version__}"
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, text, "Version", 0)
    except Exception:
        try:
            print(text)
        except Exception:
            pass


def main():
    if "--version" in sys.argv:
        _show_version()
        return

    # Tell the auto-update batch that the bootloader + Python + pygame all
    # loaded successfully. The batch watches for this marker and retries the
    # launch when it never appears (e.g. the onefile Python-DLL boot failure).
    import updater
    updater.mark_boot_ok()

    loaded_mods, mod_errors = mods.load_mods()

    ap = argparse.ArgumentParser(description="Sheriff of Nottingham - Lite Online")
    ap.add_argument("--host", action="store_true", help="host a room (this machine is the server)")
    ap.add_argument("--players", type=int, default=4, help="max players 2-5, default 4")
    ap.add_argument("--port", type=int, default=net.DEFAULT_PORT, help=f"listen port, default {net.DEFAULT_PORT}")
    ap.add_argument("--name", default="", help="your name")
    ap.add_argument("--join", default="", help="join a room, e.g. 192.168.1.5:5555")
    ap.add_argument("--lang", default="zh", choices=["zh", "en"], help="ui language, default zh")
    ap.add_argument("--no-royal", action="store_true",
                    help="disable royal goods cards (12 high-value contraband, count as x2 legal)")
    ap.add_argument("--no-blackmarket", action="store_true",
                    help="disable black market quests (3 groups x 2 rewards)")
    args = ap.parse_args()
    App(host=args.host, players=args.players, port=args.port, name=args.name,
        join=args.join, lang_name=args.lang,
        royal=not args.no_royal, black_market=not args.no_blackmarket,
        mod_names=[m["name"] for m in loaded_mods],
        mod_errors=mod_errors,
        mod_list=mods.list_all_mods()).run()


if __name__ == "__main__":
    main()
