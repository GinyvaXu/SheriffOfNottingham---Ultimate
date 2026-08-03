# v1.7.3 - Complete in-game GUI redesign & performance boost

**English / 中文**

## English
- **Redesigned the whole in-game screen.** Every module now lives in its own fixed zone that never overlaps: a clean top bar (phase/round/sheriff, deck count, rule-mod chips), a full-width player strip, the black-market quest panel, a dedicated "your table" line (bag + smuggled goods), the hand cards, the instruction line, the action buttons, and the chat column.
- **Player nameplates fully expanded.** Panels are wider and their height adapts to the stall contents, so 5-6 player rooms no longer squeeze everyone into tiny boxes; avatar, name, gold/hand, bag, declaration, reputation/favor, colored stall and smuggling info each get their own row.
- **Chat gives way to the players.** The chat column is now its own panel on the right: title, round-event strip, scrollable history, quick-chat buttons (no longer clipped at the screen edge) and the chat input are all inside it.
- **Quick chat fixed.** All 12 phrases now sit at the bottom of the chat panel in a compact two-column block, fully visible and clickable.
- **Deck logo moved into the top bar** so it no longer overlaps player nameplates; the "your table" info line no longer collides with hand cards.
- **Bribe/counter inputs moved into the action row** (amount + note + buttons), always readable and never overlapping cards.
- **Performance: idle frames are now nearly free.** Menu and update screens reuse the cached scaled frame when nothing moves (mouse idle), running about 4x faster at 2560x1440 (3.5 ms vs 15.7 ms per frame); hover glows, fades, scrolling, chat and view updates still redraw instantly. Release-note wrapping and background decorations are cached too.
- **Change:** all bundled mod versions are synced with the game build (1.7.3).

## 中文
- **局内界面整体重做。** 每个模块都有自己固定的区域、互不重叠：顶部信息条（阶段/回合/警长、牌堆数、玩法模组标记）、通栏玩家区、黑市任务面板、独立的“我的桌面”信息行（袋中 + 走私保留）、手牌区、提示行、操作按钮区与聊天栏。
- **玩家名牌充分展开。** 面板加宽，高度随摊位内容自适应，5-6 人局不再挤成一团；头像、名字、金币/手牌、封袋、申报、声望/恩惠、彩色摊位与走私信息各占一行，互不遮挡。
- **聊天区为玩家信息让位。** 聊天独立成右侧面板：标题、回合事件条、可滚动历史、快捷用语（不再被屏幕边缘截断）与输入框全部收进面板内。
- **快捷用语修复。** 12 条短语统一放在聊天面板底部的两列区块中，完整可见、随时点击。
- **牌堆图标移入顶部信息条**，不再与玩家名牌重叠；“我的桌面”信息行与手牌卡不再碰撞。
- **贿赂/还价输入框并入操作区**（金额 + 留言 + 按钮），始终清晰可读，不再压到卡牌。
- **性能：空闲帧近乎零开销。** 主菜单与更新页在鼠标静止时直接复用缓存画面，2560x1440 下每帧从约 15.7ms 降至约 3.5ms（快约 4 倍）；悬停光效、切屏淡入、滚动、聊天与对局视图更新仍即时重绘。更新日志换行与背景装饰也改为缓存。
- **同步：** 所有内置模组版本与游戏版本同步为 1.7.3。
