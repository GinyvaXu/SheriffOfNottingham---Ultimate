**English** | [??](README_zh-CN.md)

# Sheriff of Nottingham - Python Lite Online

A minimal Python implementation of the classic board game **Sheriff of Nottingham**.
Feature-complete, simple code, modular design. Classic rules plus two optional
house modules (Royal Goods cards and Black Market quests), both toggleable.
v1.1.0 adds a **mod system** and an **installable/uninstallable setup package**.
v1.2.0 adds a **game icon**, decorative in-game graphics, an **in-game mods management screen**, and a bundled **cyberpunk reskin mod**.
v1.2.1 adds **automatic update checking** (startup check + menu button) and one-click silent reinstall from GitHub releases.
v1.2.2 fixes **mod enable/disable save failures** (UTF-8 BOM manifests and read-only files) and makes the **update check** resilient (jsDelivr + GitHub API fallback sources, retries, friendly timeout/network messages).
v1.2.3 fixes **"mod.json not writable" after installing under Program Files**: the installer grants write permission on the mods folder, the game self-repairs folder ACLs (icacls) on demand, and automatically falls back to a per-user mods folder under %APPDATA% (with migration) when the install folder is still not writable. The Mods screen now shows the actual mods folder path.

## Files

```
game.py      Rules & state machine (pure logic, no UI/network)
bot.py       Bot AI module (easy / normal / hard, runs on the host server)
net.py       TCP server + JSON protocol + disconnect/reconnect + bot driver
gui.py       pygame button-only UI
gfx.py       Procedural decorative graphics (badge, coin, card back, icon)
mods.py      Mod loader (mods/ folder next to the exe, ModAPI for add/patch)
lang.py      Bilingual strings (zh/en) + card-name rebuild for mods
main.py      Entry point (--version shows the version dialog)
version.py   __version__ = "1.2.3"
installer.iss  Inno Setup script that builds the installer
test_bot.py  Headless bot automation test (full game + reconnect)
test_ai_bots.py  Test for in-lobby AI bots (host adds bots, plays a full game)
test_new_rules.py  Unit tests for royal goods & black market modules
test_mods.py Mod loader unit tests (register/patch/enable/disable/errors)
mods/        Built-in mod folder (README.md + example_mod + cyberpunk_mod, disabled by default)
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
adjusts to however many players actually joined. In the lobby the host can set the
number of rounds (default: each player is sheriff twice) and rename themselves.

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

## AI bots

- In the lobby the host can add bots (Easy / Normal / Hard) with the buttons on
  the right to fill empty seats, and remove them again before starting.
- Bots act autonomously on the host server (market discard/draw, bag loading,
  declarations, bribes, sheriff inspections, black-market submissions) and do
  not need a network connection. Their decisions only use public information.
- A game can be played solo: 1 human + 1-4 bots.

## Mod system (v1.2.0)

- The main menu has a **Mods** screen: view every installed mod (name, version,
  description), enable/disable it (written back to its `mod.json`), refresh the
  list and see load errors. Changes apply after the game restarts.
- A bundled `cyberpunk_mod/` renames all goods, phases and key UI terms to a
  neon cyberpunk theme with matching colors (disabled by default).

Any folder under `mods/` (next to the exe, or the project root when running from
source) with a `mod.json` is a mod:

```json
{
  "id": "example_mod",
  "name": "Example Mod",
  "version": "0.1.0",
  "description": "Adds Tea (contraband) and Pear (legal goods).",
  "enabled": false
}
```

- `enabled: true` loads the mod; the folder may also contain `mod.py` whose
  `register(api)` function is called at startup.
- The `ModAPI` lets you add card types or change the game itself:

```python
def register(api):
    api.add_contraband("TEA", "Tea", "??", value=5, fine=3, cnt3=8, cnt6=12, color=(90, 160, 120))
    api.add_legal("PEAR", "Pear", "?", value=3, fine=2, cnt3=24, cnt6=24,
                  king_bonus=10, queen_bonus=5, color=(140, 200, 90))
    api.patch("game", "HAND_SIZE", 7)     # e.g. change the hand size rule
```

- `add_legal` / `add_contraband` / `add_royal` register new card types with the
  per-player card counts (`cnt3` for 3 players, `cnt6` for 4-6 players), colors,
  values, fines and (for legal goods) the 1st/2nd-place end bonuses.
- `patch("game", attr, value)` / `get("game", attr)` read or modify any engine
  attribute (rules). Broken mods are skipped with an error shown on the menu
  screen; they never crash the game.
- See `mods/README.md` (bilingual) and `mods/example_mod/` for the full API.
- All players in a room should install the same content mods: the server drives
  the rules, clients only need the names/colors to render cards.

## Installer (v1.2.0)

`installer\SheriffOfNottingham-Setup-1.2.0.exe` is a normal Windows setup built
with Inno Setup:

- Installs the game + `mods\` folder + a desktop/start-menu shortcut.
- Uninstalls cleanly from "Apps & features" (Control Panel) and removes the
  whole app folder including any mods you added.
- Supports English and Chinese installer languages (chosen at install time).
- Rebuild it with: `ISCC.exe installer.iss` after running `??.bat`.

## Graphics & icon (v1.2.0)

- A sheriff-badge app icon is drawn procedurally and used for the window, the
  exe and the installer.
- In-game decorations: menu logo, gold coin next to gold displays, sheriff
  badge on the sheriff's nameplate, and a card-back for the deck.

## Rules notes

- Market: players discard up to 5 cards, then draw the same number from the
  deck. The discard piles are hidden and can no longer be drawn from.
- Each card type has a fixed value/fine; card counts scale with player count.
- 4 legal goods (apple / chicken / cheese-milk / bread) and 4 contraband
  (silk / crossbow / coffee / wine) in the classic rules, plus royal goods.
- If you smuggle 3 cards of the same black-market contraband, the quest
  auto-submits: the 3 cards are discarded, the reward (1st 30-35 gold, 2nd
  25-30) is announced, and completed quests lock for everyone else.

## Gameplay

- **Market**: choose hand cards to discard (0-5), then draw the same number back from the deck.
- **Load**: secretly pick 1-5 cards into your bag, then seal it.
- **Declare**: pick a legal goods type and confirm (card count is forced = bag size; the type may be a lie).
- **Inspect**: the bag owner may bribe (gold + note); the sheriff decides pass or inspect.
- **Chat**: bottom-right input, Enter to send; quick-chat buttons are also available.

## Game over / back to lobby

- After the game ends (results screen) click **Back to Room** to return everyone
  to the lobby of the same room (seats and bots are kept, the host can start a
  new game). The room can also be quit with the Quit button.
- Bots of the same difficulty get numbered names (Bot-Easy 1, Bot-Easy 2, ...)
  so multiple bots of one level are easy to tell apart.

## Disconnect / reconnect

If a player drops mid-game the game waits for them (no AI takeover, no forfeit).
Rejoining the same room with the **same name** restores the seat; the client also
auto-reconnects.

## Automated test

```
python test_new_rules.py              # royal goods + black market unit tests
python test_mods.py                   # mod loader tests
python test_bot.py --players 3        # full 3-player game (incl. disconnect/reconnect)
python test_bot.py --players 5        # 5-player game
python test_ai_bots.py --rounds 2     # in-lobby AI bots
```

## Known limitations

- Trust mode: the host is the server, theoretically cheat-able; for friends only.
- Bilingual UI (Chinese default; font loader keeps CJK system fonts as fallback).
- Plaintext TCP, no encryption or anti-cheat.
- Direct public connection depends on NAT type; use frp/ngrok as relay if it fails.
- Bribes simplified to gold + note; no goods/promise validation.

## Package to exe

```
??.bat                        # or run the command below manually
python -m PyInstaller --clean --noconfirm SheriffOfNottingham.spec
```

- Produces `dist\SheriffOfNottingham.exe` (~41 MB, single file, no Python install
  needed) with version info 1.1.0 and a bundled `mods\` copy; the running exe
  reads `mods\` **next to itself**, so you can add/remove mods freely.
- The first run as host triggers a Windows Firewall prompt; allow it to open the port.
- To see error output, package with `--console` or run `python main.py` directly.
- The exe accepts the same CLI args: `SheriffOfNottingham.exe --host --players 4`
  or `SheriffOfNottingham.exe --join 192.168.1.5:5555`.
