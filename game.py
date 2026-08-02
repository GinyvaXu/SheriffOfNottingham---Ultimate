# -*- coding: utf-8 -*-
"""Sheriff of Nottingham - classic rules state machine (pure logic, no UI/network, testable)
Includes royal goods cards and black market quests (both toggleable)."""

import random

LEGAL = ["APPLE", "CHICKEN", "CHEESE", "BREAD"]
CONTRABAND = ["SILK", "CROSSBOW", "COFFEE", "WINE"]

# Goods table: fixed value per card, per-card fine (sheriff pays when wrongly
# inspecting legal goods / merchant pays when caught with contraband), and card
# counts for 3-player games vs 4-6 player games (user-defined house numbers).
GOODS = {
    "APPLE":    {"value": 2, "fine": 2, "cnt3": 48, "cnt6": 48},
    "CHICKEN":  {"value": 4, "fine": 2, "cnt3": 24, "cnt6": 24},
    "CHEESE":   {"value": 3, "fine": 2, "cnt3": 36, "cnt6": 36},
    "BREAD":    {"value": 3, "fine": 2, "cnt3": 0,  "cnt6": 36},
    "SILK":     {"value": 8, "fine": 4, "cnt3": 9,  "cnt6": 12},
    "CROSSBOW": {"value": 9, "fine": 4, "cnt3": 5,  "cnt6": 5},
    "COFFEE":   {"value": 6, "fine": 4, "cnt3": 18, "cnt6": 22},
    "WINE":     {"value": 7, "fine": 4, "cnt3": 16, "cnt6": 21},
}

# Royal goods: contraband that, once smuggled past the sheriff, counts as
# `equals` normal cards of its base legal type for the end-game 1st/2nd ranking.
ROYAL_GOODS = {
    "ROYAL_GREEN_APPLE":  {"of": "APPLE",   "equals": 2, "value": 4, "fine": 3, "cnt3": 2, "cnt6": 2},
    "ROYAL_GOLD_APPLE":   {"of": "APPLE",   "equals": 3, "value": 6, "fine": 4, "cnt3": 1, "cnt6": 2},
    "ROYAL_GOUDA_CHEESE": {"of": "CHEESE",  "equals": 2, "value": 6, "fine": 4, "cnt3": 2, "cnt6": 2},
    "ROYAL_BLUE_CHEESE":  {"of": "CHEESE",  "equals": 3, "value": 9, "fine": 5, "cnt3": 0, "cnt6": 1},
    "ROYAL_RYE_BREAD":    {"of": "BREAD",   "equals": 2, "value": 6, "fine": 4, "cnt3": 0, "cnt6": 2},
    "ROYAL_COARSE_BREAD": {"of": "BREAD",   "equals": 3, "value": 9, "fine": 5, "cnt3": 0, "cnt6": 1},
    "ROYAL_CHICKEN":      {"of": "CHICKEN", "equals": 2, "value": 8, "fine": 4, "cnt3": 1, "cnt6": 2},
}
ROYAL_TYPES = list(ROYAL_GOODS.keys())
ROYAL_TYPE_OF = {rt: d["of"] for rt, d in ROYAL_GOODS.items()}
ALL_TYPES = LEGAL + CONTRABAND + ROYAL_TYPES

TYPE_EN = {
    "APPLE": "Apple", "CHEESE": "Cheese", "BREAD": "Bread", "CHICKEN": "Chicken",
    "SILK": "Silk", "CROSSBOW": "Crossbow", "COFFEE": "Coffee", "WINE": "Wine",
    "ROYAL_GREEN_APPLE": "Green Apple", "ROYAL_GOLD_APPLE": "Gold Apple",
    "ROYAL_GOUDA_CHEESE": "Gouda Cheese", "ROYAL_BLUE_CHEESE": "Blue Cheese",
    "ROYAL_RYE_BREAD": "Rye Bread", "ROYAL_COARSE_BREAD": "Coarse Bread",
    "ROYAL_CHICKEN": "Royal Chicken",
    "BLACK_MARKET": "Black Market",
}

TYPE_ZH = {
    "APPLE": "\u82f9\u679c", "CHEESE": "\u5976\u9171", "BREAD": "\u9762\u5305", "CHICKEN": "\u9e21\u8089",
    "SILK": "\u4e1d\u7ef8", "CROSSBOW": "\u5f29", "COFFEE": "\u5496\u5561", "WINE": "\u9152",
    "ROYAL_GREEN_APPLE": "\u9752\u82f9\u679c", "ROYAL_GOLD_APPLE": "\u91d1\u82f9\u679c",
    "ROYAL_GOUDA_CHEESE": "\u8c6a\u8fbe\u5976\u9171", "ROYAL_BLUE_CHEESE": "\u84dd\u7eb9\u5976\u9171",
    "ROYAL_RYE_BREAD": "\u9ed1\u9ea6\u9762\u5305", "ROYAL_COARSE_BREAD": "\u7c97\u7cae\u9762\u5305",
    "ROYAL_CHICKEN": "\u7687\u5bb6\u9e21\u8089",
    "BLACK_MARKET": "\u9ed1\u5e02",
}

KING_BONUS = {"APPLE": 20, "CHICKEN": 10, "CHEESE": 15, "BREAD": 15}
QUEEN_BONUS = {"APPLE": 10, "CHICKEN": 5, "CHEESE": 10, "BREAD": 10}

HAND_SIZE = 6
BAG_MIN, BAG_MAX = 1, 5
DISCARD_MAX = 5

# Black Market quests: 3 random contraband types, 2 reward slots each. A slot is
# claimed via the Submit button once a player has BLACK_MARKET_NEED cards of the
# type in their stall; the 3 cards are discarded and the player gets the slot's
# gold reward + a black-market card (+25 end-game each). Rewards are generated at
# game start and shown in advance (1st: 30-35, 2nd: 25-30, strictly lower).
BLACK_MARKET_GROUPS = 3
BLACK_MARKET_NEED = 3
BLACK_MARKET_REWARD_RANGES = [(30, 35), (25, 30)]  # (min, max) per slot
BLACK_MARKET_CARD_BONUS = 25      # end-game points per black-market card held


def _card_counts(players):
    """Card-count table key: 3-player numbers for <=3 players, 4-6 otherwise."""
    return 3 if players <= 3 else 6


def make_deck(rng=None, royal=True, players=3):
    """Build the goods deck sized for the player count (user-defined house numbers)."""
    rng = rng or random.Random()
    key = _card_counts(players)
    cards = []
    for t in LEGAL + CONTRABAND:
        d = GOODS[t]
        n = d["cnt3"] if key == 3 else d["cnt6"]
        cards.extend([{"type": t, "value": d["value"], "fine": d["fine"]} for _ in range(n)])
    if royal:
        for rt, d in ROYAL_GOODS.items():
            n = d["cnt3"] if key == 3 else d["cnt6"]
            cards.extend([{"type": rt, "value": d["value"], "fine": d["fine"],
                           "royal": True, "royal_type": d["of"], "equals": d["equals"]}
                          for _ in range(n)])
    rng.shuffle(cards)
    return cards


def is_contraband(card):
    """A royal goods card behaves as contraband (cannot be declared, confiscated)."""
    return card.get("royal") or card["type"] in CONTRABAND


def _counts(cards):
    out = {}
    for c in cards:
        out[c["type"]] = out.get(c["type"], 0) + 1
    return out


def transfer(pay_from, pay_to, amount):
    """Pay gold from pay_from to pay_to; if short, settle with stall goods (no change), remaining debt waived."""
    if amount <= 0:
        return ""
    paid = 0
    if pay_from.gold >= amount:
        pay_from.gold -= amount
        pay_to.gold += amount
        return f"pays {amount} gold"
    paid = pay_from.gold
    pay_from.gold = 0
    pay_to.gold += paid
    need = amount - paid
    pay_from.stand_legal.sort(key=lambda c: -c["value"])
    while need > 0 and pay_from.stand_legal:
        c = pay_from.stand_legal.pop(0)
        pay_to.stand_legal.append(c)
        need -= c["value"]
    while need > 0 and pay_from.stand_contra:
        c = pay_from.stand_contra.pop(0)
        pay_to.stand_contra.append(c)
        need -= c["value"]
    return "insufficient gold, settled with goods (remaining debt waived)"


class Player:
    def __init__(self, name):
        self.name = name
        self.gold = 50
        self.hand = []
        self.bag = []
        self.bag_loaded = False
        self.stand_legal = []
        self.stand_contra = []
        self.decl = None      # {"type":..., "count":...}
        self.bribe = None     # {"gold":..., "msg":...}
        self.connected = True
        self.black_market_cards = 0   # black-market reward cards held (+25 each at game end)

    def view_public(self):
        return {
            "name": self.name,
            "gold": self.gold,
            "hand_count": len(self.hand),
            "stand_legal": _counts(self.stand_legal),
            "stand_royal": [c["type"] for c in self.stand_contra if c.get("royal")],
            "smuggle_secret": True,
            "smuggle_count": sum(1 for c in self.stand_contra if not c.get("royal")),
            "bag_size": len(self.bag) if self.bag_loaded else 0,
            "decl": self.decl,
            "connected": self.connected,
        }


class Game:
    """Five-phase state machine. Methods return (ok, msg) or (ok, events)."""

    def __init__(self, players, rng=None, royal=True, black_market=True, rounds_total=None):
        self.players = players
        self.n = len(players)
        self.rng = rng or random.Random()
        self.deck = make_deck(self.rng, royal=royal, players=self.n)
        self.d1 = []  # discard piles 1/2, end of list = top
        self.d2 = []
        for p in self.players:
            p.hand = [self.deck.pop() for _ in range(HAND_SIZE)]
        for _ in range(5):
            self.d1.append(self.deck.pop())
        for _ in range(5):
            self.d2.append(self.deck.pop())
        self.phase = "LOBBY"
        self.first_sheriff = self.rng.randrange(self.n)
        self.sheriff = self.first_sheriff
        self.round_no = 0
        self.rounds_total = rounds_total or self.n * (3 if self.n == 3 else 2)
        self.order = []       # merchant order this round (left of sheriff first)
        self.market_idx = 0
        self.decl_idx = 0
        self.inspect_idx = 0
        self.discard_hold = {}  # seat -> cards discarded this market turn, not yet placed
        self.draw_allow = {}    # seat -> how many more cards this player may draw this market turn
        # Black Market quest state (3 groups x 2 slots, one contraband type each)
        self.black_market = black_market
        self.quest_types = []
        self.quest_rewards = {}   # type -> [slot0 gold, slot1 gold]
        self.quest_claimed = {}   # type -> number of claimed slots (0/1/2)
        self.quest_claimers = {}  # type -> [name or None, name or None]
        if black_market:
            pool = list(CONTRABAND)
            self.rng.shuffle(pool)
            self.quest_types = pool[:BLACK_MARKET_GROUPS]
            for t in self.quest_types:
                lo1, hi1 = BLACK_MARKET_REWARD_RANGES[0]
                first = self.rng.randint(lo1, hi1)
                lo2, hi2 = BLACK_MARKET_REWARD_RANGES[1]
                second = self.rng.randint(lo2, min(hi2, first - 1))
                self.quest_rewards[t] = [first, second]
            self.quest_claimed = {t: 0 for t in self.quest_types}
            self.quest_claimers = {t: [None, None] for t in self.quest_types}

    # ---------- Round progression ----------

    def start_round(self):
        self.sheriff = (self.first_sheriff + self.round_no) % self.n
        self.round_no += 1
        for p in self.players:
            p.bag = []
            p.bag_loaded = False
            p.decl = None
            p.bribe = None
        self.order = [(self.sheriff + i) % self.n for i in range(1, self.n)]
        self.phase = "MARKET"
        self.market_idx = 0
        self.discard_hold = {}
        self.draw_allow = {}

    def market_current(self):
        return self.order[self.market_idx]

    def _ensure_deck(self, need=1):
        if len(self.deck) >= need:
            return
        for pile in (self.d1, self.d2):
            if pile:
                self.deck.extend(pile)
                pile[:] = []
        self.rng.shuffle(self.deck)

    def _place_discards(self, seat):
        placed = self.discard_hold.pop(seat, [])
        for c in placed:
            self.d1.append(c)

    # ---------- Market ----------

    def do_market_discard(self, seat, indices):
        if self.phase != "MARKET":
            return False, "Not the market phase"
        if seat != self.market_current():
            return False, "Not your turn"
        idx = sorted(set(indices))
        if len(idx) > DISCARD_MAX:
            return False, "You can discard at most 5"
        hand = self.players[seat].hand
        chosen = [hand[i] for i in idx if 0 <= i < len(hand)]
        for i in reversed(idx):
            if 0 <= i < len(hand):
                del hand[i]
        self.discard_hold[seat] = chosen
        self.draw_allow[seat] = len(chosen)
        legal = sum(1 for c in chosen if not is_contraband(c))
        contra = len(chosen) - legal
        if not chosen:
            # Nothing discarded -> nothing to draw; end this market turn at once.
            self.finish_market_turn(seat)
            return True, ""
        return True, (f"You discarded {len(chosen)} card(s) "
                      f"({legal} legal, {contra} contraband). Draw to 6.")

    def do_market_draw(self, seat, source):
        if self.phase != "MARKET":
            return False, "Not the market phase"
        if seat != self.market_current():
            return False, "Not your turn"
        if source not in (None, "deck"):
            return False, "Only draw from the deck"
        if len(self.players[seat].hand) >= HAND_SIZE:
            return False, "Your hand is already full"
        if self.draw_allow.get(seat, 0) <= 0:
            return False, "No more draws left"
        if not self.deck:
            self._ensure_deck(1)
            if not self.deck:
                return False, "No cards left to draw"
        self.players[seat].hand.append(self.deck.pop())
        self.draw_allow[seat] -= 1
        return True, ""

    def finish_market_turn(self, seat):
        self._place_discards(seat)
        self.market_idx += 1
        if self.market_idx >= len(self.order):
            self.phase = "LOAD"

    # ---------- Load bag ----------

    def do_load(self, seat, indices):
        if self.phase != "LOAD":
            return False, "Not the load phase"
        if seat == self.sheriff:
            return False, "The Sheriff does not load a bag"
        p = self.players[seat]
        if p.bag_loaded:
            return False, "You already sealed your bag"
        idx = sorted(set(indices))
        chosen = [p.hand[i] for i in idx if 0 <= i < len(p.hand)]
        if not (BAG_MIN <= len(chosen) <= BAG_MAX):
            return False, f"Bag must contain {BAG_MIN}-{BAG_MAX} cards"
        for i in reversed(idx):
            if 0 <= i < len(p.hand):
                del p.hand[i]
        p.bag = chosen
        p.bag_loaded = True
        if all(pp.bag_loaded for i, pp in enumerate(self.players) if i != self.sheriff):
            self.phase = "DECLARE"
            self.decl_idx = 0
        return True, f"Bag sealed ({len(chosen)} card(s))"

    # ---------- Declare ----------

    def declare_current(self):
        return self.order[self.decl_idx]

    def do_declare(self, seat, ctype):
        if self.phase != "DECLARE":
            return False, "Not the declaration phase"
        if seat != self.declare_current():
            return False, "Not your turn"
        if ctype not in LEGAL:
            return False, "You can only declare legal goods"
        p = self.players[seat]
        p.decl = {"type": ctype, "count": len(p.bag)}
        self.decl_idx += 1
        if self.decl_idx >= len(self.order):
            self.phase = "INSPECT"
            self.inspect_idx = 0
        return True, ""

    # ---------- Inspect ----------

    def inspect_current(self):
        return self.order[self.inspect_idx]

    def do_bribe(self, seat, gold, msg=""):
        if self.phase != "INSPECT":
            return False, "Not the inspection phase"
        if seat != self.inspect_current():
            return False, "Not your turn"
        p = self.players[seat]
        gold = max(0, min(int(gold or 0), p.gold))
        p.bribe = {"gold": gold, "msg": (msg or "")[:80]}
        return True, ""

    def do_inspect_decision(self, sheriff_seat, action):
        if self.phase != "INSPECT":
            return False, ["Not the inspection phase"]
        if sheriff_seat != self.sheriff:
            return False, ["You are not the sheriff"]
        if action not in ("pass", "inspect"):
            return False, ["Unknown decision"]
        owner = self.players[self.inspect_current()]
        sheriff = self.players[self.sheriff]
        events = []
        bribe = owner.bribe or {"gold": 0, "msg": ""}
        if action == "pass":
            if bribe["gold"] > 0:
                res = transfer(owner, sheriff, bribe["gold"])
                events.append(f"{owner.name} bribes the Sheriff {bribe['gold']} gold")
                if res != f"pays {bribe['gold']} gold":
                    events.append(res)
            if bribe["msg"]:
                events.append(f"{owner.name}'s promise: {bribe['msg']}")
            for c in owner.bag:
                events.extend(self._deliver(owner, c))
            events.append(f"{owner.name} passes unchecked ({len(owner.bag)} card(s) enter)")
        else:
            decl_type = owner.decl["type"]
            declared = [c for c in owner.bag if c["type"] == decl_type]
            hidden = [c for c in owner.bag if c["type"] != decl_type]
            if not hidden:
                penalty = sum(c.get("fine", c["value"]) for c in owner.bag)
                res = transfer(sheriff, owner, penalty)
                for c in owner.bag:
                    events.extend(self._deliver(owner, c))
                events.append(f"Inspection of {owner.name}: TRUTH! Sheriff pays {penalty} gold")
                if res != f"pays {penalty} gold":
                    events.append(res)
            else:
                for c in declared:
                    events.extend(self._deliver(owner, c))
                seized, passed = [], []
                for c in hidden:
                    (seized if is_contraband(c) else passed).append(c)
                for c in passed:
                    events.extend(self._deliver(owner, c))
                self.d1.extend(seized)
                if seized:
                    detail = ", ".join(f"{TYPE_EN[t]}x{n}" for t, n in _counts(seized).items())
                    fine = sum(c.get("fine", c["value"]) for c in seized)
                    res = transfer(owner, sheriff, fine)
                    events.append(
                        f"Inspection of {owner.name}: LIE! {len(seized)} contraband seized "
                        f"({detail}), merchant pays {fine} gold fine, "
                        f"{len(passed)} legal card(s) enter")
                    if res != f"pays {fine} gold":
                        events.append(res)
                else:
                    events.append(
                        f"Inspection of {owner.name}: LIE but all legal - "
                        f"{len(hidden)} card(s) enter, nothing seized")
        owner.bag = []
        owner.bag_loaded = False
        owner.bribe = None
        self.inspect_idx += 1
        if self.inspect_idx >= len(self.order):
            self.end_round()
            if self.phase == "GAME_OVER":
                events.append("Game over! See results.")
            else:
                events.append(f"Round {self.round_no - 1} complete. Round {self.round_no} starts.")
        return True, events

    def _deliver(self, player, card):
        """Deliver a card past the sheriff. Royal cards are announced (visible stall)."""
        events = []
        if card["type"] in LEGAL:
            player.stand_legal.append(card)
        elif card.get("royal"):
            player.stand_contra.append(card)
            events.append(
                f"{player.name} smuggled {TYPE_EN[card['type']]} "
                f"(counts as {card.get('equals', 2)} {TYPE_EN[card['royal_type']]})")
        else:
            player.stand_contra.append(card)
        return events

    def black_market_view(self):
        """Public black-market quest state for the UI (None when disabled)."""
        if not self.black_market:
            return None
        progress = {}
        for i, p in enumerate(self.players):
            progress[i] = {t: sum(1 for c in p.stand_contra if c["type"] == t)
                           for t in self.quest_types}
        return {
            "types": list(self.quest_types),
            "rewards": {t: list(self.quest_rewards.get(t, [0, 0])) for t in self.quest_types},
            "claimed": dict(self.quest_claimed),
            "claimers": {t: list(self.quest_claimers.get(t, [None, None])) for t in self.quest_types},
            "progress": progress,
            "need": BLACK_MARKET_NEED,
        }

    def do_black_market_submit(self, seat, ctype, slot=None):
        """Manually claim a black-market reward slot via the quest panel button."""
        if self.phase in ("LOBBY", "GAME_OVER"):
            return False, "Game not in progress"
        if not self.black_market:
            return False, "Black market is disabled"
        if ctype not in self.quest_types:
            return False, "No black market quest for that type"
        if slot is None:
            slot = self.quest_claimed[ctype]
        elif slot != self.quest_claimed[ctype]:
            return False, "This black market quest is already completed"
        if slot >= len(self.quest_rewards[ctype]):
            return False, "This black market quest is already completed"
        p = self.players[seat]
        held = [c for c in p.stand_contra if c["type"] == ctype]
        if len(held) < BLACK_MARKET_NEED:
            return False, f"Need {BLACK_MARKET_NEED} smuggled {TYPE_EN[ctype]} to submit"
        removed = 0
        kept = []
        for c in p.stand_contra:
            if c["type"] == ctype and removed < BLACK_MARKET_NEED:
                self.d1.append(c)
                removed += 1
            else:
                kept.append(c)
        p.stand_contra = kept
        reward = self.quest_rewards[ctype][slot]
        p.gold += reward
        p.black_market_cards += 1
        self.quest_claimed[ctype] = slot + 1
        self.quest_claimers[ctype][slot] = p.name
        return True, (f"{p.name} completes BLACK MARKET quest for {TYPE_EN[ctype]} "
                      f"({'1st' if slot == 0 else '2nd'} reward): +{reward} gold, +Black Market card")

    # ---------- End of round / scoring ----------

    def end_round(self):
        for p in self.players:
            while len(p.hand) < HAND_SIZE:
                self._ensure_deck(1)
                if not self.deck:
                    break
                p.hand.append(self.deck.pop())
        if self.round_no >= self.rounds_total:
            self.phase = "GAME_OVER"
        else:
            self.start_round()

    def _base_rows(self):
        rows = []
        for i, p in enumerate(self.players):
            legal_count = {t: 0 for t in LEGAL}
            contra_count = {t: 0 for t in CONTRABAND}
            royal_eff = {t: 0 for t in LEGAL}
            royal_cards = 0
            delivered = []
            for c in p.stand_legal:
                legal_count[c["type"]] += 1
                delivered.append(c)
            for c in p.stand_contra:
                if c.get("royal"):
                    royal_eff[c["royal_type"]] += c.get("equals", 2)
                    royal_cards += 1
                else:
                    contra_count[c["type"]] += 1
                delivered.append(c)
            value = sum(c["value"] for c in delivered) + p.gold
            rows.append({
                "seat": i, "name": p.name, "gold": p.gold, "value": value,
                "legal_total": len(p.stand_legal),
                "contra_total": len(p.stand_contra),
                "legal": legal_count, "contra": contra_count,
                "royal": royal_eff, "royal_cards": royal_cards,
                "black_market_cards": p.black_market_cards,
                "bonus": 0, "bonus_detail": [], "final": 0,
            })
        return rows

    @staticmethod
    def _eff_legal(r, t):
        """Effective legal count: normal cards + royal cards at their card-face multiplier."""
        return r["legal"][t] + r["royal"].get(t, 0)

    def _legal_king_queen(self, rows):
        """End-of-game 1st/2nd reward per legal good (royal cards count as 2)."""
        entries = []
        for t in LEGAL:
            ranked = sorted(rows, key=lambda r: -self._eff_legal(r, t))
            top_eff = self._eff_legal(ranked[0], t)
            if top_eff <= 0:
                continue
            aw = []
            top = [r for r in ranked if self._eff_legal(r, t) == top_eff]
            king = KING_BONUS.get(t, 0)
            queen = QUEEN_BONUS.get(t, 0)
            if len(top) > 1:
                share = (king + queen) // len(top) if (king + queen) else 0
                for r in top:
                    aw.append({"seat": r["seat"], "bonus": share})
            else:
                aw.append({"seat": ranked[0]["seat"], "bonus": king})
                if len(ranked) > 1:
                    second_eff = self._eff_legal(ranked[1], t)
                    if second_eff > 0 and queen:
                        second = [r for r in ranked[1:] if self._eff_legal(r, t) == second_eff]
                        share = queen // len(second)
                        for r in second:
                            aw.append({"seat": r["seat"], "bonus": share})
            entries.append({"type": t, "awards": aw})
            for a in aw:
                rows[a["seat"]]["bonus"] += a["bonus"]
                rows[a["seat"]]["bonus_detail"].append({"type": t, "bonus": a["bonus"]})
        return entries

    def _black_market_rows(self, rows):
        """End-of-game points for held black-market cards (+25 each)."""
        entries = []
        for r in rows:
            n = r["black_market_cards"]
            if n > 0:
                b = n * BLACK_MARKET_CARD_BONUS
                r["bonus"] += b
                r["bonus_detail"].append({"type": "BLACK_MARKET", "bonus": b, "count": n})
        if any(r["black_market_cards"] > 0 for r in rows):
            entries.append({"type": "BLACK_MARKET", "awards": [
                {"seat": r["seat"], "bonus": r["black_market_cards"] * BLACK_MARKET_CARD_BONUS}
                for r in rows if r["black_market_cards"] > 0]})
        return entries

    def score(self):
        rows = self._base_rows()
        self._legal_king_queen(rows)
        self._black_market_rows(rows)
        for r in rows:
            r["final"] = r["value"] + r["bonus"]
        rows.sort(key=lambda r: (-r["final"], -r["legal_total"], -r["contra_total"]))
        return rows

    def bonus_table(self):
        """Structured per-good end-bonus awards for the results screen."""
        rows = self._base_rows()
        table = []
        for e in self._legal_king_queen(rows):
            table.append({"kind": "king", "type": e["type"], "awards": [
                {"name": self.players[a["seat"]].name, "bonus": a["bonus"]} for a in e["awards"]]})
        for e in self._black_market_rows(rows):
            table.append({"kind": "blackmarket", "type": e["type"], "awards": [
                {"name": self.players[a["seat"]].name, "bonus": a["bonus"]} for a in e["awards"]]})
        return table
