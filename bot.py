# -*- coding: utf-8 -*-
"""Bot AI module: easy / normal / hard decision logic.

Bots live on the host server and share the Game object, so they see the full
state. They may freely use their OWN hand/bag, but decisions about OTHER
players (sheriff inspection) only use public information, mirroring what a
human can see.
"""

import game

LEVELS = ("easy", "normal", "hard")


def bot_name(level, num=None):
    """Wire name for a bot seat (num differentiates same-level bots)."""
    base = "Bot-" + level.capitalize()
    return base if num is None else f"{base} {num}"


def _public_smuggle(p):
    """Public contraband count (royal cards are public and excluded)."""
    return sum(1 for c in p.stand_contra if not c.get("royal"))


# ---------- Market: discard choice ----------

def choose_discard(g, seat, level):
    """Return hand indices (0-5) to discard; the bot redraws the same count."""
    hand = g.players[seat].hand
    quest = set(g.quest_types)

    def score(i):
        c = hand[i]
        s = c["value"]
        if c.get("royal"):
            s += 8
        if c["type"] in game.CONTRABAND:
            s += 3
        if level == "hard" and c["type"] in quest:
            s += 6
        return s

    limit = {"easy": 3, "normal": 4, "hard": 5}[level]
    idx = sorted(range(len(hand)), key=score)
    return idx[:limit]


# ---------- Load bag: which hand cards go into the bag ----------

def choose_load(g, seat, level):
    """Return hand indices (1-5) to smuggle this round."""
    hand = g.players[seat].hand
    rng = g.rng
    quest = set(g.quest_types)
    legal = [i for i, c in enumerate(hand) if not game.is_contraband(c)]
    contra = [i for i, c in enumerate(hand) if game.is_contraband(c)]

    def ckey(i):
        c = hand[i]
        s = c["value"] + (8 if c.get("royal") else 0)
        if level == "hard" and c["type"] in quest:
            s += 6
        return -s

    contra.sort(key=ckey)
    legal.sort(key=lambda i: -hand[i]["value"])

    max_contra = {"easy": 1, "normal": 2, "hard": 4}[level]
    p_smuggle = {"easy": 0.15, "normal": 0.55, "hard": 0.80}[level]
    want = {"easy": rng.randint(1, 3), "normal": rng.randint(2, 4),
            "hard": rng.randint(3, 5)}[level]
    if not contra:
        p_smuggle = 0.0

    n_c = 0
    if rng.random() < p_smuggle:
        n_c = min(max_contra, len(contra), want)

    chosen = list(contra[:n_c])

    # Fill the rest with legal cards of a single (most common) type so the
    # declaration stays plausible.
    by_type = {}
    for i in legal:
        by_type.setdefault(hand[i]["type"], []).append(i)
    fill = []
    if by_type:
        best = max(by_type.values(),
                   key=lambda v: (len(v), sum(hand[i]["value"] for i in v)))
        fill = best
    target = min(max(len(chosen), want), 5)
    if len(chosen) < target:
        chosen.extend(fill[:target - len(chosen)])
    if not chosen:
        chosen = [legal[0]] if legal else contra[:1]
    return chosen[:5]


# ---------- Declare ----------

def choose_declare(g, seat, level):
    """Pick the legal type to declare (count is forced to the bag size)."""
    bag = g.players[seat].bag
    counts = {}
    for c in bag:
        if c["type"] in game.LEGAL:
            counts[c["type"]] = counts.get(c["type"], 0) + 1
    if counts:
        return max(counts, key=counts.get)
    return g.rng.choice(["APPLE", "BREAD", "CHEESE", "CHICKEN"])


# ---------- Bribe ----------

def choose_bribe(g, seat, level):
    """Return (gold, msg) the merchant offers; gold 0 means no bribe."""
    p = g.players[seat]
    rng = g.rng
    has_contra = any(game.is_contraband(c) for c in p.bag)
    gold = 0
    if level == "easy":
        if has_contra and rng.random() < 0.30:
            gold = rng.randint(1, 3)
        elif rng.random() < 0.10:
            gold = rng.randint(1, 2)
    elif level == "normal":
        if has_contra:
            if rng.random() < 0.60:
                gold = rng.randint(3, 8)
        elif rng.random() < 0.30:
            gold = rng.randint(1, 4)
    else:
        if has_contra:
            val = sum(c["value"] for c in p.bag if game.is_contraband(c))
            if rng.random() < 0.85:
                gold = rng.randint(min(6, val + 1), min(18, val + 6))
        elif rng.random() < 0.40:
            gold = rng.randint(2, 6)
    gold = max(0, min(gold, p.gold))
    return gold, ""


# ---------- Sheriff: inspect or pass ----------

def choose_inspect(g, sheriff_seat, level):
    """Sheriff decision for the current merchant (public info only)."""
    target = g.players[g.inspect_current()]
    bribe = (target.bribe or {}).get("gold", 0)
    bag_n = len(target.bag)
    rng = g.rng
    if level == "easy":
        if bag_n >= 3 and bribe <= 1:
            return "inspect"
        return "pass"

    score = bag_n * 1.5
    if bribe == 0:
        score += 1.0
    elif bribe >= 10:
        score += 2.5
    elif bribe >= 4:
        score += 1.3
    if _public_smuggle(target) > 0:
        score += 1.2
    if level == "normal":
        score -= 1.0
        thresh = 4.0
    else:
        thresh = 4.2
    score += rng.uniform(-1.0, 1.0)
    return "inspect" if score >= thresh else "pass"


# ---------- Black market: auto-submit when eligible ----------

def choose_black_market(g, seat, level):
    """Return (type, slot) to submit, or None. Every bot submits if eligible."""
    p = g.players[seat]
    for t in g.quest_types:
        slot = g.quest_claimed.get(t, 0)
        if slot >= 2:
            continue
        held = sum(1 for c in p.stand_contra if c["type"] == t)
        if held >= game.BLACK_MARKET_NEED:
            return t, slot
    return None
