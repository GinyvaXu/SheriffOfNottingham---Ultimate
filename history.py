# -*- coding: utf-8 -*-
"""Match history: every finished game (time, players, scores, ranking).

Records live in %APPDATA%/SheriffOfNottingham/history.json and are shown on
the History screen in the menu. Only the final results are stored - no per
move data - so the file stays tiny.
"""

import io
import json
import os
import time

import profile

HISTORY_FILE = "history.json"
MAX_RECORDS = 50


def history_path():
    return os.path.join(profile.app_dir(), HISTORY_FILE)


def load_history():
    """Return the list of finished-game records (newest first)."""
    try:
        with io.open(history_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and isinstance(data.get("records"), list):
            return [r for r in data["records"] if isinstance(r, dict)]
    except (OSError, ValueError):
        pass
    return []


def _rank_line(s, rank):
    """One score dict -> a compact record line (no localization here)."""
    return {
        "name": str(s.get("name", "?")),
        "rank": int(rank),
        "final": int(s.get("final", 0) or 0),
        "gold": int(s.get("gold", 0) or 0),
        "value": int(s.get("value", 0) or 0),
        "bonus": int(s.get("bonus", 0) or 0),
    }


def add_record(scores, rounds=0, n_players=0):
    """Append a finished game; ``scores`` is the ranked score list."""
    scores = scores or []
    if not scores:
        return False
    recs = load_history()
    rec = {
        "ts": time.strftime("%Y-%m-%d %H:%M"),
        "players": [_rank_line(s, i + 1) for i, s in enumerate(scores)],
        "rounds": int(rounds or 0),
        "n": int(n_players or len(scores)),
        "winner": str(scores[0].get("name", "?")),
    }
    recs.insert(0, rec)
    del recs[MAX_RECORDS:]
    try:
        with io.open(history_path(), "w", encoding="utf-8", newline="") as f:
            json.dump({"records": recs}, f, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False


def clear_history():
    try:
        with io.open(history_path(), "w", encoding="utf-8", newline="") as f:
            json.dump({"records": []}, f, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False
