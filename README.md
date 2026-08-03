**English** | [中文](README_zh-CN.md)

# Sheriff of Nottingham - Python Lite Online

A minimal Python implementation of the classic board game **Sheriff of Nottingham**.
Feature-complete, simple code, modular design. Classic rules plus two optional
house modules (Royal Goods cards and Black Market quests), both toggleable.
v1.1.0 adds a **mod system** and an **installable/uninstallable setup package**.
v1.2.0 adds a **game icon**, decorative in-game graphics, an **in-game mods management screen**, and a bundled **cyberpunk reskin mod**.
v1.2.1 adds **automatic update checking** (startup check + menu button) and one-click silent reinstall from GitHub releases.
v1.2.2 fixes **mod enable/disable save failures** (UTF-8 BOM manifests and read-only files) and makes the **update check** resilient (jsDelivr + GitHub API fallback sources, retries, friendly timeout/network messages).
v1.2.3 fixes **"mod.json not writable" after installing under Program Files**: the installer grants write permission on the mods folder, the game self-repairs folder ACLs (icacls) on demand, and automatically falls back to a per-user mods folder under %APPDATA% (with migration) when the install folder is still not writable. The Mods screen now shows the actual mods folder path.
v1.3.0 adds an in-game **Mods Market** (browse the GitHub-hosted catalog, one-click download & install), ships **5 text-only reskin mods** (cyberpunk / medieval / starlight / steampunk / arcane), and makes server **chat messages follow the local reskin** — reskins are client-side only, so each player online sees their own version.
v1.4.0 adds **rule mods** (gameplay-changing mods) with a **server-side room check**: everyone in a room must have the same rule mods installed (id + version), the lobby shows each player's mod status and offers **one-click download & install** of missing rule mods. Ships two example rule mods (**Marathon Market**, **Spice Road**).
v1.4.1 adds **player profiles & avatars**: your name + avatar are saved in `%APPDATA%/SheriffOfNottingham/profile.json` and restored on every launch; pick one of **8 built-in avatars** or **upload your own picture** (auto-downscaled and shared with everyone in the room); avatars appear in the menu, lobby, player panels and results screen. The **5 reskin mods now include themed avatar palettes** matching their world. Also: the **Mods/Market screens list every mod** (Spice Road is no longer hidden), a **Restart Game** button appears after enabling or installing mods, and the **update-restart flow is fixed** (single-CRLF batch file, waits for the old process to fully exit). New gameplay-mod ideas are detailed in **MOD_IDEAS.md** for review.
v1.6.6 adds four new **rule mods**: **Wild Card** (the host sets how many wild cards go into the deck; they are legal goods, and any wild card in your bag automatically becomes the goods you declared when inspected), **Sheriff Intel** (once per round the Sheriff may pay n coins - the total cards left in the un-inspected bags - to learn how many contraband cards remain among the waiting merchants, as a range such as 0-2 or 3-5, only when at least two merchants are still waiting), **Super Contraband** (each contraband type gets one super card worth triple its value and triple its fine), and **Merchant Reputation v2** (legal goods that simply don't match your declared type no longer cost reputation; positive reputation makes you draw legal goods more often - at reputation 5 each card is 90% legal; negative reputation raises contraband odds but is tuned down to leave room to recover). All bundled mod versions are synced with the game build (1.6.6).
v1.6.7 adds the **Twists of Fate Event Pack** (风云变幻事件包) rule mod: at the start of every round one public event card is revealed and stays in effect until the round ends. Its 10 medium/low-difficulty events are **Bountiful Harvest** (+1 market draw), **Famine** (bag max 4 cards), **Plague** (one legal good is banned from bags - wild cards cannot become it either), **Market Day** (truthful inspections pay +1 gold per card), **City Gate Tax** (pay 1 gold to seal your bag), **Inspector Visit** (the Sheriff must inspect at least one merchant), **Full Lockdown** (contraband fines x2, super contraband included), **Amnesty Day** (seized without fine), **Black Market Boom** (smuggled contraband is worth +1), and **Street Rumors** (the Sheriff may peek at one card from a waiting merchant, once per round). The event name and full effect stay visible in a banner above the in-game chat; during Plague the banned goods are listed and greyed out when packing, and the Sheriff gets a **Peek** button while inspecting. Bots respect bag limits and the ban; Black Market missions are unaffected (confirmed). Also: the lobby wild-card count input is now clickable, lobby rule-mod rows expand to show full bilingual rules, declaring with wild cards reports how many counted as your declared goods, the in-game chat history has a real scrollbar, and the chat no longer crashes when empty. All bundled mod versions are synced with the game build (1.6.7).
v1.7.0 adds **screen transition animations**, a **scalable window** (the whole UI renders on a fixed 1280x800 logical canvas that scales onto your real window, with automatic compact player panels for 5-6 players so the crowded six-player table gets more room), a **Settings screen** (window presets 1280x800/1600x900/1920x1080/2560x1440, custom width/height, fullscreen and borderless modes), a **Match History screen** (every finished game records date/time, players, rounds and detailed scores + ranking, kept locally in `%APPDATA%/SheriffOfNottingham/history.json`, clearable), and a **Sponsor button** on the menu that opens the developer's Love Power page. The Black Market quest panel was redesigned with colored goods chips and star-marked reward slots. All bundled mod versions are synced with the game build (1.7.0).
v1.7.1 makes the **update check parallel and China-friendly**: every mirror (GitHub acceleration proxies, raw GitHub, jsDelivr CDN edges, GitHub releases API) is probed at the same time under one shared deadline, so a full check finishes in a few seconds instead of up to a minute, and the old "check timed out" hangs are gone on mainland-China networks. New jsDelivr CDN sources (cdn / fastly / gcore) are fast from China, and when several sources answer the highest version wins, so a stale CDN cache can never hide a newer release. Also cleaned up the GitHub release list (removed the old v1.5.3 draft). All bundled mod versions are synced with the game build (1.7.1).
v1.7.3 completely redesigns the in-game screen. Every module gets its own fixed, non-overlapping zone: a clean top bar (phase/round/sheriff, deck count, rule-mod chips), a full-width player strip, the black-market quest panel, a dedicated your-table line (bag + smuggled goods), the hand cards, the instruction line, the action row, and a self-contained chat column. Player nameplates are wider and their height adapts to the stall contents, so 5-6 player rooms no longer squeeze; chat gives way to the players, quick-chat moved inside the chat panel (no more clipped buttons), the deck logo moved into the top bar, and bribe/counter inputs live in the action row. Performance: idle frames now reuse the cached scaled frame (menu/update screens about 4x faster at 2560x1440; 3.5 ms vs 15.7 ms per frame) while hover/fade/scroll/chat still redraw instantly; release-note wrapping and background decorations are cached too. The update manifest history was rebuilt in clean bilingual text. All bundled mod versions are synced with the game build (1.7.3).
v1.7.4 fixes the **6-player "Passed a NULL pointer" crash**: the nameplate font "shrink" loop actually grew the point size (the pixel line height is larger than the point size), so a long name in a narrow 5-6 player panel ramped the font up until SDL_ttf returned a broken font and the next text measurement crashed the game. Name fonts now shrink correctly and absurdly long names are trimmed with an ellipsis. **Font loading is now validated**: get_font probes every font after loading, so corrupt/truncated font files (for example from a broken install or an interrupted update) are skipped instead of crashing text rendering. All bundled mod versions are synced with the game build (1.7.4).
v1.7.2 rebuilds the Settings screen into a clean game-style layout (left: resolution presets + custom size; right: display mode Windowed/Borderless/Fullscreen and screen fit Fit/Stretch). New Stretch mode fills the window edge-to-edge so mismatched window ratios no longer show black bars. The canvas is now scaled with smooth bilinear resampling and a cached presentation surface, removing the pixelated/jagged edges at large presets (1920x1080/2560x1440 look clean). The screen-transition fade reuses cached overlays and is shorter, so the menu/update screens no longer lag (90+ FPS at 2560x1440). Buttons gained feedback animations (hover glide, 2px press sink, soft click flash). Black Market Submit buttons were realigned to each quest row's right edge. All bundled mod versions are synced with the game build (1.7.2).
v1.6.9 makes **auto-update work in mainland China**: the update check and the installer download no longer depend on reaching GitHub directly - the game now tries several community GitHub acceleration proxies usable from mainland China (ghfast.top, gh-proxy.com, ghproxy.net, gh.llkk.cc) in order, for both the update manifest and the installer download, so checking and updating keep working even when api/raw.githubusercontent.com are slow or blocked. Advanced users can point the game at their own mirror (for example a Gitee repo) via `%APPDATA%/SheriffOfNottingham/mirror.json` (`{"manifest": "...", "installer": "..."}`, both optional). Mod-market downloads use the same proxy fallback and prefer fresh GitHub sources over the stale jsDelivr cache. The update error screen now explains mainland-China GitHub restrictions and offers the manual download page. All bundled mod versions are synced with the game build (1.6.9).
v1.6.8 expands the **Twists of Fate Event Pack** to **20 events** (added Apple Blight, Cheese Festival, Zero Tolerance, Double Compensation, Shortage, Parade Day, Bounty Board, Sheriff Payday, Rumors Pro, Royal Treasury), makes events draw randomly every round so they **never run out** and never repeat two rounds in a row, adds **6-player rooms** (lobby cap is now 2-6), fixes **Bountiful Harvest** actually granting the extra draw, fixes **Black Market auto-submit** so the final round can still claim rewards, and **color-codes chat messages** by type. All bundled mod versions are synced with the game build (1.6.8).


## Files

```
game.py      Rules & state machine (pure logic, no UI/network)
bot.py       Bot AI module (easy / normal / hard, runs on the host server)
net.py       TCP server + JSON protocol + disconnect/reconnect + bot driver
gui.py       pygame button-only UI
gfx.py       Procedural decorative graphics (badge, coin, card back, icon)
mods.py      Mod loader (mods/ folder next to the exe, ModAPI for add/patch/rename)
profile.py   Local player profile (name + avatar, %APPDATA%/SheriffOfNottingham/profile.json)
lang.py      Bilingual strings (zh/en) + card-name rebuild + reskin renames
market.py    Mod market: remote catalog + one-click download & install
mods_market.json  Mod market catalog (raw + jsDelivr CDN)
mods_pack/   Packed mod zips served to the in-game market
main.py      Entry point (--version shows the version dialog)
version.py   __version__ = "1.6.9"
installer.iss  Inno Setup script that builds the installer
test_bot.py  Headless bot automation test (full game + reconnect)
test_ai_bots.py  Test for in-lobby AI bots (host adds bots, plays a full game)
test_new_rules.py  Unit tests for royal goods & black market modules
test_mods.py Mod loader unit tests (register/patch/enable/disable/errors)
test_reskin_mods.py  Reskin mod + market install tests
test_avatars.py  Profile/avatar save-load + online avatar sync tests
MOD_IDEAS.md  Bilingual gameplay-mod idea proposals (for review)
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
Everyone in the lobby (host, guests and bots) must click **Ready** before the host
can start; joining clients must run the **same game version** as the host - the
host rejects mismatched versions with a clear error.

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
    api.add_contraband("TEA", "Tea", "茶", value=5, fine=3, cnt3=8, cnt6=12, color=(90, 160, 120))
    api.add_legal("PEAR", "Pear", "梨", value=3, fine=2, cnt3=24, cnt6=24,
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


## Rule Mods (v1.4.0)

A rule mod is a mod whose `mod.json` has `"category": "rules"`. Rule mods change
the actual rules of the game and come with a **server-side room check**:

- Rule mods run on the **host server** (the host process loads the mod and the
  server drives the changed rules).
- Every human player in the room must install the **exact same rule mods
  (id + version)** before the game can start.
- The lobby shows the room's required rule mods and each player's status
  (OK / missing). Players who are missing mods can click **"Install missing
  rule mods"** to download them from the in-game market with one click, then
  restart the game and rejoin.
- Bots always match the host (they run inside the server).
- Content added by a rule mod (e.g. new card types) is driven by the server;
  clients render the same cards because they have the same mod installed.

### Bundled example rule mods (disabled by default)

| Mod | What it changes |
| --- | --- |
| Marathon Market | Lengthens the match: 3 rounds per player (4 for 3-player games). |
| Spice Road | Adds a legal goods (Pepper) and a contraband (Tea). |

### Recommended rule-mod ideas

| Idea | Gameplay change |
| --- | --- |
| Double Fines | All inspection fines & compensation double - high risk, high reward. |
| Market Volatility | Goods values change randomly each round. |
| Black Market Baron | Bigger black-market rewards, different submit counts. |
| Strict Sheriff | The sheriff inspects one extra merchant per round; fines double. |
| Royal Feast | More royal cards, higher royal values. |
| Embargo | One random goods type is banned for the whole match. |
| Fast Trade | Hand size 5, bags of 1-4 cards. |
| Generous King | Higher 1st/2nd place end bonuses. |
| No Bribes | Bribe phase removed - pure nerve. |

## Installer (v1.2.0)


`installer\SheriffOfNottingham-Setup-1.2.0.exe` is a normal Windows setup built
with Inno Setup:

- Installs the game + `mods\` folder + a desktop/start-menu shortcut.
- Uninstalls cleanly from "Apps & features" (Control Panel) and removes the
  whole app folder including any mods you added.
- Supports English and Chinese installer languages (chosen at install time).
- Rebuild it with: `ISCC.exe installer.iss` (after building the exe).

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

- **Market**: all merchants act in parallel - each chooses hand cards to discard (0-5),
  then draws the same number back from the deck; the phase ends when everyone is done.
- **Load**: secretly pick 1-5 cards into your bag, then seal it.
- **Declare**: all merchants declare in parallel (card count is forced = bag size; the type may be a lie).
- **Inspect**: the bag owner may bribe (gold + note); the sheriff can accept it, pass,
  inspect, or **counter with a higher demand** - the merchant may then accept, reject,
  or counter again (up to 3 counter-offers per negotiation, then accept/reject only).
  If the merchant rejects the sheriff's counter-offer, their **original bribe offer
  still stands** (it is not voided).
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

## Windows Smart App Control blocks the game

Fresh Windows 11 devices enable **Smart App Control (SAC)**, which blocks
unsigned executables from unknown publishers. The game is currently unsigned,
so after installing, SAC may show:

> "Smart App Control has blocked a potentially unsafe app ... the publisher could not be verified"

Players can work around it:
- Turn it off: Windows Security -> App & browser control -> Smart App Control -> **Off**.
  Note: turning SAC off is permanent for that PC (it can only be re-enabled by resetting Windows).
- If the installer came from a browser download, first right-click the .exe -> Properties -> **Unblock**.

Developers can remove the block for everyone by code-signing **both** the game exe
and the installer with a publicly trusted certificate (an OV/EV certificate or
Microsoft Azure Trusted Signing), then run:

```
.\sign_assets.ps1 -Thumbprint <CERT_SHA1>
```

See the header of `sign_assets.ps1` for details.

## Known limitations

- Trust mode: the host is the server, theoretically cheat-able; for friends only.
- Bilingual UI (Chinese default; font loader keeps CJK system fonts as fallback).
- Plaintext TCP, no encryption or anti-cheat.
- Direct public connection depends on NAT type; use frp/ngrok as relay if it fails.
- Bribes are gold + note with counter-offer bargaining (up to 3 rounds); no goods/promise validation.

## Package to exe

```
python -m PyInstaller --clean --noconfirm SheriffOfNottingham.spec
```

- Produces a folder build `dist\SheriffOfNottingham\` (exe + permanent
  `_internal\` runtime, no Python install needed, no self-extraction) with
  version info 1.6.5 and a bundled `mods\` copy; the running exe reads `mods\`
  **next to itself**, so you can add/remove mods freely.
- The first run as host triggers a Windows Firewall prompt; allow it to open the port.
- To see error output, package with `--console` or run `python main.py` directly.
- The exe accepts the same CLI args: `SheriffOfNottingham.exe --host --players 4`
  or `SheriffOfNottingham.exe --join 192.168.1.5:5555`.v1.6.8 expands the **Twists of Fate Event Pack** to **20 events** (added Apple Blight, Cheese Festival, Zero Tolerance, Double Compensation, Shortage, Parade Day, Bounty Board, Sheriff Payday, Rumors Pro, Royal Treasury), makes events draw randomly every round so they **never run out** and never repeat two rounds in a row, adds **6-player rooms** (lobby cap is now 2-6), fixes **Bountiful Harvest** actually granting the extra draw, fixes **Black Market auto-submit** so the final round can still claim rewards, and **color-codes chat messages** by type. All bundled mod versions are synced with the game build (1.6.8).


## Files

```
game.py      Rules & state machine (pure logic, no UI/network)
bot.py       Bot AI module (easy / normal / hard, runs on the host server)
net.py       TCP server + JSON protocol + disconnect/reconnect + bot driver
gui.py       pygame button-only UI
gfx.py       Procedural decorative graphics (badge, coin, card back, icon)
mods.py      Mod loader (mods/ folder next to the exe, ModAPI for add/patch/rename)
profile.py   Local player profile (name + avatar, %APPDATA%/SheriffOfNottingham/profile.json)
lang.py      Bilingual strings (zh/en) + card-name rebuild + reskin renames
market.py    Mod market: remote catalog + one-click download & install
mods_market.json  Mod market catalog (raw + jsDelivr CDN)
mods_pack/   Packed mod zips served to the in-game market
main.py      Entry point (--version shows the version dialog)
version.py   __version__ = "1.7.0"
installer.iss  Inno Setup script that builds the installer
test_bot.py  Headless bot automation test (full game + reconnect)
test_ai_bots.py  Test for in-lobby AI bots (host adds bots, plays a full game)
test_new_rules.py  Unit tests for royal goods & black market modules
test_mods.py Mod loader unit tests (register/patch/enable/disable/errors)
test_reskin_mods.py  Reskin mod + market install tests
test_avatars.py  Profile/avatar save-load + online avatar sync tests
MOD_IDEAS.md  Bilingual gameplay-mod idea proposals (for review)
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
Everyone in the lobby (host, guests and bots) must click **Ready** before the host
can start; joining clients must run the **same game version** as the host - the
host rejects mismatched versions with a clear error.

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
    api.add_contraband("TEA", "Tea", "茶", value=5, fine=3, cnt3=8, cnt6=12, color=(90, 160, 120))
    api.add_legal("PEAR", "Pear", "梨", value=3, fine=2, cnt3=24, cnt6=24,
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


## Rule Mods (v1.4.0)

A rule mod is a mod whose `mod.json` has `"category": "rules"`. Rule mods change
the actual rules of the game and come with a **server-side room check**:

- Rule mods run on the **host server** (the host process loads the mod and the
  server drives the changed rules).
- Every human player in the room must install the **exact same rule mods
  (id + version)** before the game can start.
- The lobby shows the room's required rule mods and each player's status
  (OK / missing). Players who are missing mods can click **"Install missing
  rule mods"** to download them from the in-game market with one click, then
  restart the game and rejoin.
- Bots always match the host (they run inside the server).
- Content added by a rule mod (e.g. new card types) is driven by the server;
  clients render the same cards because they have the same mod installed.

### Bundled example rule mods (disabled by default)

| Mod | What it changes |
| --- | --- |
| Marathon Market | Lengthens the match: 3 rounds per player (4 for 3-player games). |
| Spice Road | Adds a legal goods (Pepper) and a contraband (Tea). |

### Recommended rule-mod ideas

| Idea | Gameplay change |
| --- | --- |
| Double Fines | All inspection fines & compensation double - high risk, high reward. |
| Market Volatility | Goods values change randomly each round. |
| Black Market Baron | Bigger black-market rewards, different submit counts. |
| Strict Sheriff | The sheriff inspects one extra merchant per round; fines double. |
| Royal Feast | More royal cards, higher royal values. |
| Embargo | One random goods type is banned for the whole match. |
| Fast Trade | Hand size 5, bags of 1-4 cards. |
| Generous King | Higher 1st/2nd place end bonuses. |
| No Bribes | Bribe phase removed - pure nerve. |

## Installer (v1.2.0)


`installer\SheriffOfNottingham-Setup-1.2.0.exe` is a normal Windows setup built
with Inno Setup:

- Installs the game + `mods\` folder + a desktop/start-menu shortcut.
- Uninstalls cleanly from "Apps & features" (Control Panel) and removes the
  whole app folder including any mods you added.
- Supports English and Chinese installer languages (chosen at install time).
- Rebuild it with: `ISCC.exe installer.iss` (after building the exe).

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

- **Market**: all merchants act in parallel - each chooses hand cards to discard (0-5),
  then draws the same number back from the deck; the phase ends when everyone is done.
- **Load**: secretly pick 1-5 cards into your bag, then seal it.
- **Declare**: all merchants declare in parallel (card count is forced = bag size; the type may be a lie).
- **Inspect**: the bag owner may bribe (gold + note); the sheriff can accept it, pass,
  inspect, or **counter with a higher demand** - the merchant may then accept, reject,
  or counter again (up to 3 counter-offers per negotiation, then accept/reject only).
  If the merchant rejects the sheriff's counter-offer, their **original bribe offer
  still stands** (it is not voided).
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

## Windows Smart App Control blocks the game

Fresh Windows 11 devices enable **Smart App Control (SAC)**, which blocks
unsigned executables from unknown publishers. The game is currently unsigned,
so after installing, SAC may show:

> "Smart App Control has blocked a potentially unsafe app ... the publisher could not be verified"

Players can work around it:
- Turn it off: Windows Security -> App & browser control -> Smart App Control -> **Off**.
  Note: turning SAC off is permanent for that PC (it can only be re-enabled by resetting Windows).
- If the installer came from a browser download, first right-click the .exe -> Properties -> **Unblock**.

Developers can remove the block for everyone by code-signing **both** the game exe
and the installer with a publicly trusted certificate (an OV/EV certificate or
Microsoft Azure Trusted Signing), then run:

```
.\sign_assets.ps1 -Thumbprint <CERT_SHA1>
```

See the header of `sign_assets.ps1` for details.

## Known limitations

- Trust mode: the host is the server, theoretically cheat-able; for friends only.
- Bilingual UI (Chinese default; font loader keeps CJK system fonts as fallback).
- Plaintext TCP, no encryption or anti-cheat.
- Direct public connection depends on NAT type; use frp/ngrok as relay if it fails.
- Bribes are gold + note with counter-offer bargaining (up to 3 rounds); no goods/promise validation.

## Package to exe

```
python -m PyInstaller --clean --noconfirm SheriffOfNottingham.spec
```

- Produces a folder build `dist\SheriffOfNottingham\` (exe + permanent
  `_internal\` runtime, no Python install needed, no self-extraction) with
  version info 1.6.5 and a bundled `mods\` copy; the running exe reads `mods\`
  **next to itself**, so you can add/remove mods freely.
- The first run as host triggers a Windows Firewall prompt; allow it to open the port.
- To see error output, package with `--console` or run `python main.py` directly.
- The exe accepts the same CLI args: `SheriffOfNottingham.exe --host --players 4`
  or `SheriffOfNottingham.exe --join 192.168.1.5:5555`.
