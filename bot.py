# -*- coding: utf-8 -*-
"""Bot AI module: easy / normal / hard decision logic.

Bots live on the host server and share the Game object, so they see the full
state. They may freely use their OWN hand/bag, but decisions about OTHER
players (sheriff inspection) only use public information, mirroring what a
human can see.
"""

import game

LEVELS = ("easy", "normal", "hard")

# Personality tags (client/host side only, no server-consistency requirement).
# Each personality adjusts the decision weights of its difficulty level.
PERSONALITIES = ("paranoid", "greedy", "honest", "reckless")
PERSONALITY_LABELS = {
    "paranoid": {"en": "Paranoid", "zh": "\u591a\u7591"},
    "greedy": {"en": "Greedy", "zh": "\u8d2a\u5a6a"},
    "honest": {"en": "Honest", "zh": "\u5b88\u6cd5"},
    "reckless": {"en": "Reckless", "zh": "\u8c6a\u8d4c"},
}

# Personality deltas applied on top of the difficulty defaults.
# inspect_bias:     sheriff extra chance to inspect
# contra_ratio:    multiplier on the number of contraband loaded
# bribe_tendency:  multiplier on bribe probability / amounts
# bluff_rate:      extra chance to load more cards than declared intent
_PERSONALITY_DELTAS = {
    "paranoid":  {"inspect_bias": 0.30, "contra_ratio": 0.70, "bribe_tendency": 1.10, "bluff_rate": 0.90},
    "greedy":    {"inspect_bias": -0.10, "contra_ratio": 1.25, "bribe_tendency": 1.35, "bluff_rate": 1.20},
    "honest":    {"inspect_bias": 0.10, "contra_ratio": 0.35, "bribe_tendency": 0.60, "bluff_rate": 0.60},
    "reckless":  {"inspect_bias": -0.20, "contra_ratio": 1.60, "bribe_tendency": 1.15, "bluff_rate": 1.50},
}

# Difficulty defaults (kept inside the module so levels stay comparable).
_DEFAULT_PARAMS = {
    "easy":   {"inspect_bias": 0.00, "contra_ratio": 0.15, "bribe_tendency": 0.30, "bluff_rate": 0.20},
    "normal": {"inspect_bias": 0.00, "contra_ratio": 0.55, "bribe_tendency": 0.60, "bluff_rate": 0.45},
    "hard":   {"inspect_bias": 0.00, "contra_ratio": 0.80, "bribe_tendency": 0.85, "bluff_rate": 0.70},
}


def bot_params(level, personality=None):
    """Merged decision parameters for a level + optional personality."""
    base = dict(_DEFAULT_PARAMS.get(level, _DEFAULT_PARAMS["normal"]))
    if personality:
        delta = _PERSONALITY_DELTAS.get(personality)
        if delta:
            for k, v in delta.items():
                base[k] = max(0.0, min(1.5, base[k] * v if k != "inspect_bias" else base[k] + v))
    return base


def bot_name(level, num=None, personality=None):
    """Wire name for a bot seat (num differentiates same-level bots)."""
    base = "Bot-" + level.capitalize()
    if personality:
        label = PERSONALITY_LABELS.get(personality, {}).get("en", personality)
        base = f"{base} ({label})"
    return base if num is None else f"{base} {num}"


_LEVEL_AVATARS = {
    "easy": ("pig", "chicken", "cat"),
    "normal": ("fox", "merchant", "wizard"),
    "hard": ("knight", "captain", "fox"),
}


def bot_avatar(level, num=1):
    """Deterministic builtin avatar per level+number so bots stay distinct."""
    pool = _LEVEL_AVATARS.get(level, ("pig", "chicken", "cat"))
    return pool[(num - 1) % len(pool)]


def _public_smuggle(p):
    """Public contraband count (royal cards are public and excluded)."""
    return sum(1 for c in p.stand_contra if not c.get("royal"))


# ---------- Market: discard choice ----------

def choose_discard(g, seat, level, personality=None):
    """Return hand indices (0-5) to discard; the bot redraws the same count."""
    hand = g.players[seat].hand
    quest = set(g.quest_types)
    params = bot_params(level, personality)

    def score(i):
        c = hand[i]
        s = c["value"]
        if c.get("royal"):
            s += 8
        if c["type"] in game.CONTRABAND:
            # greedy/reckless keep contraband in hand, honest/paranoid shed it
            s += 2 + params["contra_ratio"]
        if level == "hard" and c["type"] in quest:
            s += 6
        return s

    limit = {"easy": 3, "normal": 4, "hard": 5}[level]
    idx = sorted(range(len(hand)), key=score)
    return idx[:limit]


# ---------- Load bag: which hand cards go into the bag ----------

def choose_load(g, seat, level, personality=None):
    """Return hand indices (1-5) to smuggle this round."""
    hand = g.players[seat].hand
    rng = g.rng
    params = bot_params(level, personality)
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

    max_contra = max(0, min(len(contra), int(round({"easy": 1, "normal": 2, "hard": 4}[level]
                                                   * params["contra_ratio"]))))
    p_smuggle = min(1.0, {"easy": 0.15, "normal": 0.55, "hard": 0.80}[level]
                    * params["contra_ratio"])
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

def choose_declare(g, seat, level, personality=None):
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

def choose_bribe(g, seat, level, personality=None):
    """Return (gold, msg) the merchant offers; gold 0 means no bribe."""
    p = g.players[seat]
    rng = g.rng
    params = bot_params(level, personality)
    has_contra = any(game.is_contraband(c) for c in p.bag)
    gold = 0
    if level == "easy":
        if has_contra and rng.random() < min(1.0, 0.30 * params["bribe_tendency"]):
            gold = rng.randint(1, 3)
        elif rng.random() < min(1.0, 0.10 * params["bribe_tendency"]):
            gold = rng.randint(1, 2)
    elif level == "normal":
        if has_contra:
            if rng.random() < min(1.0, 0.60 * params["bribe_tendency"]):
                gold = rng.randint(3, 8)
        elif rng.random() < min(1.0, 0.30 * params["bribe_tendency"]):
            gold = rng.randint(1, 4)
    else:
        if has_contra:
            val = sum(c["value"] for c in p.bag if game.is_contraband(c))
            if rng.random() < min(1.0, 0.85 * params["bribe_tendency"]):
                gold = rng.randint(min(6, val + 1), min(18, val + 6))
        elif rng.random() < min(1.0, 0.40 * params["bribe_tendency"]):
            gold = rng.randint(2, 6)
    gold = max(0, min(gold, p.gold))
    return gold, ""


# ---------- Sheriff: inspect or pass ----------

def choose_inspect(g, sheriff_seat, level, personality=None):
    """Sheriff decision for the current merchant (public info only).
    Returns (action, gold): 'pass' | 'inspect' | 'counter' (gold = demand)."""
    target = g.players[g.inspect_current()]
    bribe = (target.bribe or {}).get("gold", 0)
    bag_n = len(target.bag)
    rng = g.rng
    params = bot_params(level, personality)
    if level == "easy":
        if bag_n >= 3 and bribe <= 1:
            return "inspect", None
        if bribe > 0 and bag_n >= 2 and rng.random() < 0.15:
            demand = min(bribe + rng.randint(1, 2), target.gold)
            return "counter", demand
        return "pass", None

    score = bag_n * 1.5
    if bribe == 0:
        score += 1.0
    elif bribe >= 10:
        score += 2.5
    elif bribe >= 4:
        score += 1.3
    if _public_smuggle(target) > 0:
        score += 1.2
    # A suspicious-looking merchant (big bag) who bribes little is worth
    # squeezing for more gold instead of an all-or-nothing inspection.
    if bribe > 0 and bag_n >= 2 and target.gold > bribe:
        want_more = (bribe < 6 and rng.random() < 0.30 * params["bribe_tendency"]) \
                 or (level == "hard" and bribe < 10 and rng.random() < 0.25)
        if want_more:
            demand = bribe + rng.randint(1, 4 if level == "hard" else 2)
            return "counter", min(demand, target.gold)
    if level == "normal":
        score -= 1.0
        thresh = 4.0
    else:
        thresh = 4.2
    score += params["inspect_bias"] * 2.0
    score += rng.uniform(-1.0, 1.0)
    return ("inspect" if score >= thresh else "pass"), None


def choose_respond(g, seat, level, personality=None):
    """Merchant response to the Sheriff's counter-demand.
    Returns (action, gold): 'accept' | 'reject' | 'counter' (gold = new offer)."""
    p = g.players[seat]
    demand = p.sheriff_demand or 0
    cur = (p.bribe or {}).get("gold", 0)
    rng = g.rng
    params = bot_params(level, personality)
    has_contra = any(game.is_contraband(c) for c in p.bag)
    contra_val = sum(c["value"] for c in p.bag if game.is_contraband(c))
    if has_contra:
        # Smuggling is worth paying for: value of the hidden goods + a margin.
        ceiling = contra_val + (0 if level == "easy" else rng.randint(2, 6))
    else:
        # Legal-only bag: fines are low, so a big bribe is usually a bad deal.
        ceiling = rng.randint(1, 2) if level == "easy" else rng.randint(2, 4)
    ceiling = max(ceiling, cur)
    if level == "easy":
        if demand <= ceiling or rng.random() < 0.8:
            return "accept", 0
        hi = min(demand - 1, p.gold)
        if hi > cur:
            return "counter", rng.randint(cur + 1, hi)
        return "reject", 0
    if level == "hard":
        reject_margin, counter_p = 3, 0.65
    elif level == "normal":
        reject_margin, counter_p = 6, 0.5
    else:
        reject_margin, counter_p = 99, 0.2
    if demand <= ceiling:
        return "accept", 0
    if demand > ceiling + reject_margin:
        return "reject", 0
    hi = min(demand - 1, p.gold)
    if hi <= cur:
        return "reject", 0
    if rng.random() < counter_p:
        return "counter", rng.randint(cur + 1, hi)
    return "accept", 0


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
