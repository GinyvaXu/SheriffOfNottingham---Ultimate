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
    "POT": "Bribe Pot",
}

TYPE_ZH = {
    "APPLE": "\u82f9\u679c", "CHEESE": "\u5976\u9171", "BREAD": "\u9762\u5305", "CHICKEN": "\u9e21\u8089",
    "SILK": "\u4e1d\u7ef8", "CROSSBOW": "\u5f29", "COFFEE": "\u5496\u5561", "WINE": "\u9152",
    "ROYAL_GREEN_APPLE": "\u9752\u82f9\u679c", "ROYAL_GOLD_APPLE": "\u91d1\u82f9\u679c",
    "ROYAL_GOUDA_CHEESE": "\u8c6a\u8fbe\u5976\u9171", "ROYAL_BLUE_CHEESE": "\u84dd\u7eb9\u5976\u9171",
    "ROYAL_RYE_BREAD": "\u9ed1\u9ea6\u9762\u5305", "ROYAL_COARSE_BREAD": "\u7c97\u7cae\u9762\u5305",
    "ROYAL_CHICKEN": "\u7687\u5bb6\u9e21\u8089",
    "BLACK_MARKET": "\u9ed1\u5e02",
    "POT": "\u8d4f\u91d1\u6c60",
}

KING_BONUS = {"APPLE": 20, "CHICKEN": 10, "CHEESE": 15, "BREAD": 15}
QUEEN_BONUS = {"APPLE": 10, "CHICKEN": 5, "CHEESE": 10, "BREAD": 10}

HAND_SIZE = 6
BAG_MIN, BAG_MAX = 1, 5
DISCARD_MAX = 5

# Default match length: n * ROUNDS_PER_PLAYER rounds (3-player games use the
# dedicated 3p multiplier). Rule mods may patch these to lengthen/shorten a
# match; the host server drives the rules so every player must install the
# same rule mods.
ROUNDS_PER_PLAYER = 2
ROUNDS_PER_PLAYER_3P = 3

# Black Market quests: 3 random contraband types, 2 reward slots each. A slot is
# claimed via the Submit button once a player has BLACK_MARKET_NEED cards of the
# type in their stall; the 3 cards are discarded and the player gets the slot's
# gold reward + a black-market card (+25 end-game each). Rewards are generated at
# game start and shown in advance (1st: 30-35, 2nd: 25-30, strictly lower).
BLACK_MARKET_GROUPS = 3
BLACK_MARKET_NEED = 3
BLACK_MARKET_REWARD_RANGES = [(30, 35), (25, 30)]  # (min, max) per slot
BLACK_MARKET_CARD_BONUS = 25      # end-game points per black-market card held

# ---------- Rule-mod extension hooks (all default OFF = classic rules) ----------
# Each value can be patched by a rules mod (api.patch("game", "X", ...)). The
# host server enforces the same mod set for everyone (id+version check), so a
# mod that enables any of these must be installed by all players in the room.

# Bribe Economics: share (0..1) of every accepted bribe that goes into a public
# pot instead of the sheriff. 0 = classic (sheriff keeps everything).
BRIBE_POT_RATIO = 0
# Pot payout mode: "split" divides the pot equally at game end (remainder to the
# richest merchant). Kept as one mode for balance simplicity.
BRIBE_POT_MODE = "split"

# Trade Caravans: extra gold paid per card of the round's route good that
# passes the sheriff. 0 = off.
ROUTE_BONUS = 0

# Wild Cards: N extra legal wild cards shuffled into the deck (host sets the
# count in the lobby). A wild card sitting in a declared bag automatically
# becomes the declared goods type. 0 = off.
WILD_CARDS = 0

# Sheriff Intel: once per round the sheriff may pay gold (equal to the total
# number of cards still in the un-inspected bags) to learn how many of those
# are contraband - reported only as a bucket (0-2, 3-5, ...). Only usable while
# at least 2 merchants are still to be inspected. 0 = off.
SHERIFF_INTEL = 0

# Super Contraband: one special card per contraband type whose value and fine
# are triple the base card. Behave exactly like contraband when inspected.
SUPER_CONTRA = 0

# Guild Contracts: number of secret contracts dealt at game start (0 = off).
# Each contract = (legal type, needed delivered count, gold reward).
GUILD_CONTRACTS = 0

# Royal Favor: gold reward milestones for royal cards smuggled past the sheriff.
ROYAL_FAVOR = 0
ROYAL_FAVOR_MILESTONES = [(2, 6), (4, 10), (6, 18)]

# Merchant Reputation: 0 = off. Perks unlock at reputation thresholds.
REPUTATION = 0
REP_DISCARD_AT = 1   # may discard one extra card in the market
REP_FINE_AT = 3      # fines the merchant pays are -10%
REP_HAND_AT = 5      # refills to HAND_SIZE+1 at round end

# Night Market: seconds allowed per action before the server auto-plays a
# default action. 0 = no timer (classic indefinite wait).
ACTION_TIMEOUT = 0

# Bribe bargaining: max counter-offers exchanged per negotiation (both sides
# combined). When reached, only accept/reject (or pass/inspect) remain.
BRIBE_MAX_ROUNDS = 3


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
    if WILD_CARDS > 0:
        cards.extend([{"type": "WILD", "value": 0, "fine": 0, "wild": True}
                      for _ in range(WILD_CARDS)])
    if SUPER_CONTRA:
        for t in CONTRABAND:
            d = GOODS[t]
            cards.append({"type": "SUPER_" + t, "value": d["value"] * 3,
                          "fine": d["fine"] * 3, "super": True, "of": t})
    rng.shuffle(cards)
    return cards


def is_contraband(card):
    """A royal / super card behaves as contraband (cannot be declared, confiscated)."""
    return card.get("royal") or card.get("super") or card["type"] in CONTRABAND


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
    def __init__(self, name, avatar=None):
        self.name = name
        self.avatar = avatar or {"kind": "builtin", "id": "pig"}
        self.gold = 50
        self.hand = []
        self.bag = []
        self.bag_loaded = False
        self.stand_legal = []
        self.stand_contra = []
        self.decl = None      # {"type":..., "count":...}
        self.bribe = None     # {"gold":..., "msg":...} merchant's standing offer
        self.sheriff_demand = None  # sheriff's counter-demand in gold (bargaining)
        self.bribe_round = 0        # counter-offers exchanged so far
        self.bribe_first = 0    # original offer, restored if a counter-offer is rejected
        self.connected = True
        self.black_market_cards = 0   # black-market reward cards held (+25 each at game end)
        self.reputation = 0           # merchant reputation (rule mod)
        self.royal_favor = 0          # royal cards smuggled past the sheriff (rule mod)
        self.contracts = []           # secret guild contracts [{type,need,reward,done}] (rule mod)

    def view_public(self):
        return {
            "name": self.name,
            "avatar": self.avatar,
            "gold": self.gold,
            "hand_count": len(self.hand),
            "stand_legal": _counts(self.stand_legal),
            "stand_royal": [c["type"] for c in self.stand_contra if c.get("royal")],
            "smuggle_secret": True,
            "smuggle_count": sum(1 for c in self.stand_contra if not c.get("royal")),
            "bag_size": len(self.bag) if self.bag_loaded else 0,
            "decl": self.decl,
            "connected": self.connected,
            "reputation": self.reputation,
            "royal_favor": self.royal_favor,
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
        self.rounds_total = rounds_total or self.n * (ROUNDS_PER_PLAYER_3P if self.n == 3 else ROUNDS_PER_PLAYER)
        self.order = []       # merchant order this round (left of sheriff first)
        self.market_idx = 0
        self.decl_idx = 0
        self.inspect_idx = 0
        self.discard_hold = {}  # seat -> cards discarded this market turn, not yet placed
        self.draw_allow = {}    # seat -> how many more cards this player may draw this market turn
        self.market_done = {}   # seat -> market turn finished (parallel market)
        # Black Market quest state (3 groups x 2 slots, one contraband type each)
        self.black_market = black_market
        self.quest_types = []
        self.quest_rewards = {}   # type -> [slot0 gold, slot1 gold]
        self.quest_claimed = {}   # type -> number of claimed slots (0/1/2)
        self.quest_claimers = {}  # type -> [name or None, name or None]
        self.intel_used = False         # sheriff intel used this round (rule mod)
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
        # Rule-mod state
        self.pot = 0                  # public bribe pot (Bribe Economics)
        self.route_type = None        # current round's trade route good
        self._route_history = []      # recent route goods (avoid repeats)
        if GUILD_CONTRACTS:
            self._deal_contracts()

    def _deal_contracts(self):
        """Deal secret contracts to each player at game start (3p gets one fewer)."""
        pool = [t for t in LEGAL if GOODS[t]["cnt%d" % _card_counts(self.n)] > 0]
        cnt = GUILD_CONTRACTS if self.n >= 4 else max(1, GUILD_CONTRACTS - 1)
        for p in self.players:
            p.contracts = []
            for _ in range(cnt):
                t = self.rng.choice(pool)
                need = {2: 5, 3: 4, 4: 3}.get(GOODS[t]["value"], 4)
                reward = need * GOODS[t]["value"] + 10
                p.contracts.append({"type": t, "need": need,
                                    "reward": reward, "done": False})

    # ---------- Round progression ----------

    def start_round(self):
        self.sheriff = (self.first_sheriff + self.round_no) % self.n
        self.round_no += 1
        for p in self.players:
            p.bag = []
            p.bag_loaded = False
            p.decl = None
            p.bribe = None
            p.sheriff_demand = None
            p.bribe_round = 0
            p.bribe_first = 0
        self.market_done = {}
        self.intel_used = False
        self.order = [(self.sheriff + i) % self.n for i in range(1, self.n)]
        if ROUTE_BONUS:
            pool = [t for t in LEGAL if GOODS[t]["cnt%d" % _card_counts(self.n)] > 0
                    and t not in self._route_history[-2:]]
            if not pool:
                pool = [t for t in LEGAL if GOODS[t]["cnt%d" % _card_counts(self.n)] > 0]
            self.route_type = self.rng.choice(pool)
            self._route_history.append(self.route_type)
        self.phase = "MARKET"
        self.market_idx = 0
        self.discard_hold = {}
        self.draw_allow = {}

    def market_current(self):
        """First merchant who has not finished their parallel market turn (or None)."""
        pending = self.market_pending()
        return pending[0] if pending else None

    def market_pending(self):
        """All merchants who still have to finish their market turn this round."""
        return [i for i in self.order if not self.market_done.get(i)]

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

    # ---------- Market (all merchants act simultaneously) ----------

    def do_market_discard(self, seat, indices):
        if self.phase != "MARKET":
            return False, "Not the market phase"
        if seat not in self.order:
            return False, "Not your turn"
        if self.market_done.get(seat):
            return False, "You already finished the market"
        if self.discard_hold.get(seat) is not None:
            return False, "You already discarded this turn"
        idx = sorted(set(indices))
        limit = DISCARD_MAX
        if REPUTATION and self.players[seat].reputation >= REP_DISCARD_AT:
            limit += 1
        if len(idx) > limit:
            return False, f"You can discard at most {limit}"
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
        if seat not in self.order:
            return False, "Not your turn"
        if self.market_done.get(seat):
            return False, "You already finished the market"
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
        card = self._draw_card(self.players[seat])
        if card is None:
            return False, "No cards left to draw"
        self.players[seat].hand.append(card)
        self.draw_allow[seat] -= 1
        return True, ""

    def finish_market_turn(self, seat):
        self._place_discards(seat)
        self.market_done[seat] = True
        if not self.market_pending():
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
        """First merchant who has not declared yet (or None)."""
        pending = self.declare_pending()
        return pending[0] if pending else None

    def declare_pending(self):
        """All merchants who still have to declare this round (parallel declare)."""
        return [i for i in self.order if self.players[i].decl is None]

    def do_declare(self, seat, ctype):
        if self.phase != "DECLARE":
            return False, "Not the declaration phase"
        if seat not in self.order:
            return False, "Not your turn"
        if self.players[seat].decl is not None:
            return False, "You already declared"
        if ctype not in LEGAL:
            return False, "You can only declare legal goods"
        p = self.players[seat]
        p.decl = {"type": ctype, "count": len(p.bag)}
        if WILD_CARDS:
            gd = GOODS[ctype]
            for c in p.bag:
                if c.get("wild"):
                    c["type"] = ctype
                    c["value"] = gd["value"]
                    c["fine"] = gd["fine"]
                    c.pop("wild", None)
        if not self.declare_pending():
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
        if p.bribe is not None:
            return False, "A bribe was already offered"
        gold = max(0, min(int(gold or 0), p.gold))
        p.bribe = {"gold": gold, "msg": (msg or "")[:80]}
        p.bribe_first = gold
        p.sheriff_demand = None
        p.bribe_round = 0
        return True, ""

    def do_counter_bribe(self, sheriff_seat, gold):
        """Sheriff makes a counter-demand on the merchant's standing offer."""
        if self.phase != "INSPECT":
            return False, ["Not the inspection phase"]
        if sheriff_seat != self.sheriff:
            return False, ["You are not the sheriff"]
        owner = self.players[self.inspect_current()]
        if owner.bribe is None:
            return False, ["No bribe to negotiate"]
        if owner.sheriff_demand is not None:
            return False, ["The merchant must respond to the counter-offer first"]
        cur = owner.bribe.get("gold", 0)
        if cur <= 0:
            return False, ["Nothing to negotiate: the merchant offered no bribe"]
        if owner.bribe_round >= BRIBE_MAX_ROUNDS:
            return False, ["No more counter-offers allowed"]
        try:
            gold = max(0, int(gold or 0))
        except (TypeError, ValueError):
            return False, ["Invalid amount"]
        if gold <= cur:
            return False, ["Counter-offer must be more than the current offer ({0} gold)".format(cur)]
        if gold > owner.gold:
            return False, ["The merchant only has {0} gold".format(owner.gold)]
        owner.sheriff_demand = gold
        owner.bribe_round += 1
        return True, ["{0} demands {1} gold from {2}".format(
            self.players[sheriff_seat].name, gold, owner.name)]

    def do_respond_counter(self, seat, action, gold=0):
        """Merchant answers the Sheriff's counter-demand: accept / reject / counter."""
        if self.phase != "INSPECT":
            return False, ["Not the inspection phase"]
        if seat != self.inspect_current():
            return False, ["Not your turn"]
        owner = self.players[seat]
        if owner.sheriff_demand is None:
            return False, ["No counter-offer pending"]
        sheriff = self.players[self.sheriff]
        demand = owner.sheriff_demand
        cur = owner.bribe.get("gold", 0) if owner.bribe else 0
        if action == "accept":
            owner.bribe["gold"] = demand
            events = ["{0} accepts the counter-offer of {1} gold".format(owner.name, demand)]
            self._settle_pass(owner, sheriff, events)
            self._next_merchant(owner, events)
            return True, events
        if action == "reject":
            # Negotiation failed: fall back to the merchant's ORIGINAL offer, so
            # the Sheriff can still pass/inspect at that price.
            owner.bribe = {"gold": owner.bribe_first or 0,
                           "msg": (owner.bribe or {}).get("msg", "")}
            owner.sheriff_demand = None
            owner.bribe_round = 0
            return True, ["{0} rejects the counter-offer".format(owner.name)]
        if action == "counter":
            if owner.bribe_round >= BRIBE_MAX_ROUNDS:
                return False, ["No more counter-offers allowed"]
            try:
                gold = max(0, int(gold or 0))
            except (TypeError, ValueError):
                return False, ["Invalid amount"]
            if gold <= cur:
                return False, ["Counter-offer must be more than your current offer ({0} gold)".format(cur)]
            if gold >= demand:
                return False, ["Counter-offer must be less than the Sheriff's demand ({0} gold)".format(demand)]
            if gold > owner.gold:
                return False, ["Not enough gold"]
            owner.bribe["gold"] = gold
            owner.sheriff_demand = None
            owner.bribe_round += 1
            return True, ["{0} counters with {1} gold".format(owner.name, gold)]
        return False, ["Unknown response"]

    def _settle_pass(self, owner, sheriff, events):
        """Pay the agreed bribe and deliver the bag (sheriff passed / deal struck)."""
        bribe = owner.bribe or {"gold": 0, "msg": ""}
        if bribe["gold"] > 0:
            if BRIBE_POT_RATIO > 0:
                total = min(int(bribe["gold"]), owner.gold)
                owner.gold -= total
                pot_share = int(total * BRIBE_POT_RATIO)
                sheriff.gold += total - pot_share
                self.pot += pot_share
                events.append("{0} bribes the Sheriff {1} gold "
                              "({2} gold goes to the public pot)".format(
                                  owner.name, total - pot_share, pot_share))
            else:
                res = transfer(owner, sheriff, bribe["gold"])
                events.append("{0} bribes the Sheriff {1} gold".format(owner.name, bribe["gold"]))
                if res != "pays {0} gold".format(bribe["gold"]):
                    events.append(res)
        if bribe["msg"]:
            events.append("{0}'s promise: {1}".format(owner.name, bribe["msg"]))
        for c in owner.bag:
            events.extend(self._deliver(owner, c))
        self._route_bonus(owner, owner.bag, events)
        events.append("{0} passes unchecked ({1} card(s) enter)".format(
            owner.name, len(owner.bag)))

    def _next_merchant(self, owner, events):
        owner.bag = []
        owner.bag_loaded = False
        owner.bribe = None
        owner.sheriff_demand = None
        owner.bribe_round = 0
        owner.bribe_first = 0
        self.inspect_idx += 1
        if self.inspect_idx >= len(self.order):
            self.end_round()
            if self.phase == "GAME_OVER":
                events.append("Game over! See results.")
            else:
                events.append("Round {0} complete. Round {1} starts.".format(
                    self.round_no - 1, self.round_no))

    def do_sheriff_intel(self, sheriff_seat):
        """Sheriff Intel mod: pay (total cards still in un-inspected bags) to
        learn a bucketed count (0-2 / 3-5 / ...) of contraband remaining."""
        if not SHERIFF_INTEL:
            return False, "Sheriff intel is disabled"
        if self.phase != "INSPECT":
            return False, "Not the inspection phase"
        if sheriff_seat != self.sheriff:
            return False, "You are not the sheriff"
        if self.intel_used:
            return False, "Intel already used this round"
        pending = self.order[self.inspect_idx:]
        if len(pending) < 2:
            return False, "Need at least 2 merchants left to inspect"
        cost = sum(len(self.players[i].bag) for i in pending)
        sheriff = self.players[sheriff_seat]
        if sheriff.gold < cost:
            return False, "Not enough gold: intel costs {0}".format(cost)
        sheriff.gold -= cost
        self.intel_used = True
        contra = sum(1 for i in pending
                     for c in self.players[i].bag if is_contraband(c))
        lo = (contra // 3) * 3
        hi = lo + 2
        return True, {"cost": cost, "lo": lo, "hi": hi}

    def _legal_probability(self, p):
        """Merchant Reputation mod: chance of drawing a legal card from the
        deck. Positive reputation raises it (capped at 90%), negative lowers it
        (legal floor 30%, i.e. contraband odds stay below the 90% mirror)."""
        r = p.reputation
        if r > 0:
            return min(0.5 + 0.08 * r, 0.9)
        if r < 0:
            return max(0.5 + 0.05 * r, 0.25)
        return 0.5

    def _draw_card(self, p):
        """Draw one card, biased by reputation when the mod is on."""
        if REPUTATION:
            want_legal = self.rng.random() < self._legal_probability(p)
            for i, c in enumerate(self.deck):
                if is_contraband(c) != want_legal:
                    return self.deck.pop(i)
        if not self.deck:
            self._ensure_deck(1)
            if not self.deck:
                return None
        return self.deck.pop()

    def do_inspect_decision(self, sheriff_seat, action):
        if self.phase != "INSPECT":
            return False, ["Not the inspection phase"]
        if sheriff_seat != self.sheriff:
            return False, ["You are not the sheriff"]
        if action not in ("pass", "inspect"):
            return False, ["Unknown decision"]
        owner = self.players[self.inspect_current()]
        sheriff = self.players[self.sheriff]
        if owner.sheriff_demand is not None:
            return False, ["The merchant must respond to the counter-offer first"]
        events = []
        if action == "pass":
            self._settle_pass(owner, sheriff, events)
        else:
            decl_type = owner.decl["type"]
            declared = [c for c in owner.bag if c["type"] == decl_type]
            hidden = [c for c in owner.bag if c["type"] != decl_type]
            if not hidden:
                penalty = sum(c.get("fine", c["value"]) for c in owner.bag)
                res = transfer(sheriff, owner, penalty)
                for c in owner.bag:
                    events.extend(self._deliver(owner, c))
                self._route_bonus(owner, owner.bag, events)
                events.append("Inspection of {0}: TRUTH! Sheriff pays {1} gold".format(owner.name, penalty))
                if res != "pays {0} gold".format(penalty):
                    events.append(res)
                if REPUTATION:
                    owner.reputation += 1
                    events.append("{0}'s reputation +1 -> {1}".format(owner.name, owner.reputation))
            else:
                delivered = []
                for c in declared:
                    delivered.append(c)
                    events.extend(self._deliver(owner, c))
                seized, detained = [], []
                for c in hidden:
                    (seized if is_contraband(c) else detained).append(c)
                self.d1.extend(seized)
                self.d1.extend(detained)
                if seized:
                    detail = ", ".join("{0}x{1}".format(TYPE_EN.get(t, t), n) for t, n in _counts(seized).items())
                    fine = sum(c.get("fine", c["value"]) for c in seized)
                    if REPUTATION and owner.reputation >= REP_FINE_AT:
                        fine = int(fine * 0.9)
                        events.append("{0}'s reputation discounts the fine by 10%".format(owner.name))
                    res = transfer(owner, sheriff, fine)
                    events.append(
                        "Inspection of {0}: LIE! {1} contraband seized "
                        "({2}), merchant pays {3} gold fine, "
                        "{4} mismatched legal card(s) detained".format(
                            owner.name, len(seized), detail, fine, len(detained)))
                    if res != "pays {0} gold".format(fine):
                        events.append(res)
                else:
                    events.append(
                        "Inspection of {0}: LIE! {1} mismatched legal card(s) "
                        "detained, no fine".format(owner.name, len(detained)))
                self._route_bonus(owner, delivered, events)
                if REPUTATION and seized:
                    owner.reputation -= 1
                    events.append("{0}'s reputation -1 -> {1}".format(owner.name, owner.reputation))
        self._next_merchant(owner, events)
        return True, events

    def _route_bonus(self, player, cards, events):
        """Trade Caravans: award ROUTE_BONUS per legal route-type card delivered."""
        if not (ROUTE_BONUS and self.route_type):
            return
        n = sum(1 for c in cards
                if c["type"] == self.route_type and not is_contraband(c))
        if n:
            bonus = ROUTE_BONUS * n
            player.gold += bonus
            events.append(f"{player.name} delivers {n} {TYPE_EN[self.route_type]} "
                          f"on the trade route: +{bonus} gold")

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
            if ROYAL_FAVOR:
                player.royal_favor += 1
                for lvl, reward in ROYAL_FAVOR_MILESTONES:
                    if player.royal_favor == lvl:
                        player.gold += reward
                        events.append(f"{player.name} reaches Royal Favor {lvl}: +{reward} gold")
                        break
        else:
            player.stand_contra.append(card)
        return events

    def black_market_view(self):
        """Public black-market quest state for the UI (None when disabled)."""
        if not self.black_market:
            return None
        return {
            "types": list(self.quest_types),
            "rewards": {t: list(self.quest_rewards.get(t, [0, 0])) for t in self.quest_types},
            "claimed": dict(self.quest_claimed),
            "claimers": {t: list(self.quest_claimers.get(t, [None, None])) for t in self.quest_types},
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
            target = HAND_SIZE
            if REPUTATION and p.reputation >= REP_HAND_AT:
                target += 1
            while len(p.hand) < target:
                self._ensure_deck(1)
                card = self._draw_card(p)
                if card is None:
                    break
                p.hand.append(card)
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
                    contra_count[c.get("of", c["type"])] += 1
                delivered.append(c)
            value = sum(c["value"] for c in delivered) + p.gold
            rows.append({
                "seat": i, "name": p.name, "avatar": p.avatar, "gold": p.gold, "value": value,
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

    def _pot_awards(self):
        """Bribe Economics: equal shares of the pot, remainder to the richest."""
        if self.pot <= 0 or BRIBE_POT_RATIO <= 0:
            return []
        n = max(1, self.n)
        share = self.pot // n
        rem = self.pot - share * n
        aw = [{"seat": i, "bonus": share} for i in range(self.n)]
        if rem:
            rows = self._base_rows()
            top = max(rows, key=lambda r: r["value"])
            for a in aw:
                if a["seat"] == top["seat"]:
                    a["bonus"] += rem
        return aw

    def _pot_payout(self, rows):
        for a in self._pot_awards():
            seat = a["seat"]
            if a["bonus"]:
                rows[seat]["bonus"] += a["bonus"]
                rows[seat]["bonus_detail"].append({"type": "POT", "bonus": a["bonus"]})

    def _contract_rows(self, rows):
        """Guild Contracts: reward each fulfilled secret contract at game end."""
        if not GUILD_CONTRACTS:
            return
        for r in rows:
            p = self.players[r["seat"]]
            for ct in p.contracts:
                if ct["done"]:
                    continue
                eff = r["legal"].get(ct["type"], 0) + r["royal"].get(ct["type"], 0)
                if eff >= ct["need"]:
                    ct["done"] = True
                    r["bonus"] += ct["reward"]
                    r["bonus_detail"].append(
                        {"type": ct["type"], "bonus": ct["reward"], "count": eff})

    def score(self):
        rows = self._base_rows()
        self._legal_king_queen(rows)
        self._black_market_rows(rows)
        self._contract_rows(rows)
        self._pot_payout(rows)
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
        pot = self._pot_awards()
        if pot:
            table.append({"kind": "pot", "type": "POT", "awards": [
                {"name": self.players[a["seat"]].name, "bonus": a["bonus"]} for a in pot]})
        return table
