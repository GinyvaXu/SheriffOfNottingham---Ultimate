# Sheriff of Nottingham - Python Lite Online

A minimal Python implementation of the classic board game **Sheriff of Nottingham**.
Feature-complete, simple code, modular design. Classic rules plus two optional
house modules (Royal Goods cards and Black Market quests), both toggleable.

## Files

```
game.py      Rules & state machine (pure logic, no UI/network)
bot.py       Bot AI module (easy / normal / hard, runs on the host server)
net.py       TCP server + JSON protocol + disconnect/reconnect + bot driver
gui.py       pygame button-only UI
main.py      Entry point
test_bot.py  Headless bot automation test (full game + reconnect)
test_ai_bots.py  Test for in-lobby AI bots (host adds bots, plays a full game)
test_new_rules.py  Unit tests for royal goods & black market modules
00_企画书...    Project proposal (Chinese)
01_计划书...    Implementation plan (Chinese)
```

## Dependencies & install

- Python 3.10+
- `pip install pygame`

## Language

- The UI is bilingual: Chinese by default, English available.
- Toggle with the button in the top-right of the menu/lobby, or start with `--lang en`.
- A CJK font (Microsoft YaHei) is bundled into the exe so Chinese renders everywhere,
  no system font required. Drop an OFL font as `assets\NotoSansCJKsc-Regular.otf` to replace it.
- IME input works for chat/names (pygame text input); Ctrl+V also works.

## Quick start

**Host (create a room):**
```
python main.py --host --players 4 --port 5555 --name ZhangSan
```
`--players` is the seat cap, 2-5. The host clicks "Start Game" in the lobby; the game
adjusts to however many players actually joined.

## AI bots

- In the lobby the host can add bots (Easy / Normal / Hard) with the buttons on
  the right to fill empty seats, and remove them again before starting.
- Bots act autonomously on the host server (market discard/draw, bag loading,
  declarations, bribes, sheriff inspections, black-market submissions) and do
  not need a network connection. Their decisions only use public information.
- A game can be played solo: 1 human + 1-4 bots.

## Rules notes

- Market: players discard up to 5 cards, then draw the same number from the
  deck. The discard piles are hidden and can no longer be drawn from.

**Player (join):**
```
python main.py --join 192.168.1.5:5555 --name LiSi
```

**LAN**: connect directly to the host's LAN IP. In the lobby the host can click
"Copy Address" to copy `LAN_IP:port` to the clipboard for sending to friends, and the
menu has a "Paste" button to drop a received `IP:port` straight into the join box.
**Internet**: no built-in tunneling; the host does their own port forwarding (either way):
- Router port forwarding: forward the public port to the host machine's 5555.
- Tunneling tool (frp / ngrok / etc.): map the public port to local 5555.
- Then share `PublicIP:Port` with friends to join.

## Optional modules (default ON, both toggleable)

**Royal Goods cards** (`--no-royal` to disable):
- 12 high-value contraband cards: Royal Apple/Cheese/Bread/Chicken, 3 of each.
- Value 12 gold each. They behave as contraband: cannot be declared, and are
  confiscated with the usual fine if the sheriff inspects and catches them.
- End scoring: each Royal card counts as **2 legal cards of its type**, so it can
  push you to the 1st/2nd place bonus for that legal goods.

**Black Market quests** (`--no-blackmarket` to disable):
- At setup, 3 quest groups are revealed, each pinned to one contraband type
  (silk / pepper / crossbow / honey / medicine / relic).
- The first player to smuggle **3 cards of that type** into town completes the
  quest: the 3 cards are discarded, the completion is announced to everyone, and
  the player gets +35 gold plus a Black Market card (reward slots per type: 1st +35,
  2nd +28). Each Black Market card held is worth **+25 points** at game end.

## Gameplay

- **Market**: choose hand cards to discard (0-5), then draw from a discard-pile top or the deck to refill to 6.
- **Load**: secretly pick 1-5 cards into your bag, then seal it.
- **Declare**: pick a legal goods type and confirm (card count is forced = bag size; the type may be a lie).
- **Inspect**: the bag owner may bribe (gold + note); the sheriff decides pass or inspect.
- **Chat**: bottom-right input, Enter to send; quick-chat buttons are also available.

## Disconnect / reconnect

If a player drops mid-game the game waits for them (no AI takeover, no forfeit).
Rejoining the same room with the **same name** restores the seat; the client also
auto-reconnects.

## Automated test

```
python test_new_rules.py              # royal goods + black market unit tests
python test_bot.py --players 3        # full 3-player game (incl. disconnect/reconnect)
python test_bot.py --players 5        # 5-player game
```

## Known limitations

- Trust mode: the host is the server, theoretically cheat-able; for friends only.
- Bilingual UI (Chinese default; font loader keeps CJK system fonts as fallback).
- Plaintext TCP, no encryption or anti-cheat.
- Direct public connection depends on NAT type; use frp/ngrok as relay if it fails.
- Bribes simplified to gold + note; no goods/promise validation (consistent with 01_计划书).

## Package to exe

```
打包.bat                      # or run the command below manually
python -m PyInstaller --onefile --windowed --name "SheriffOfNottingham" --add-data "assets;assets" main.py
```

- Produces `dist\SheriffOfNottingham.exe` (~28 MB, single file, no Python install needed).
- The first run as host triggers a Windows Firewall prompt; allow it to open the port.
- To see error output, package with `--console` or run `python main.py` directly.
- The exe accepts the same CLI args: `SheriffOfNottingham.exe --host --players 4` or `SheriffOfNottingham.exe --join 192.168.1.5:5555`.