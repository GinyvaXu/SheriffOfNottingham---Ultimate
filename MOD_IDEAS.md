# 玩法模组创意提案 / Gameplay Mod Proposal

> 这份文档把“可以更改或扩展玩法”的模组想法逐个详细展开，供你审核。
> 每个提案都包含：玩法改动、数值示例、实现要点（对应到现有代码）、平衡性与难度、以及需要你拍板的选择。
> This document details gameplay-changing mod ideas for your review. Each proposal covers the rule change, example numbers, implementation notes mapped to the existing code, balance/difficulty, and the decisions you need to make.

---

## 现状：模组系统能做什么 / What the mod system can already do

- 内容模组可以新增货物（合法/违禁/皇家）、修改数值、修改回合数（`mods.py` 的 `api.add_legal / add_contraband / add_royal / patch`）。
- 换皮模组只改文字与颜色（`api.rename`、`api.patch("gui","TYPE_COLOR")`、`api.set_avatar_colors`），仅客户端生效。
- 玩法模组（category=rules）需要全房间一致才能开局，服务器在 `net.py` 做校验，缺失时可一键从市场安装。
- 但目前的规则模组只能“改参数”，还不能真正改流程（比如插入新阶段、新回合逻辑）。要做到后文那些“结构性玩法”，需要给 `game.py` 增加少量扩展点（下文会标注）。

---

## 提案 1：车队商路 / Trade Caravans

**一句话简介**：每回合随机出现一条“商路”，把指定合法货物送到市场的玩家拿额外赏金，警长能看到“哪条路值钱”的公开信息。
**One-liner**: Each round a random "trade route" appears; delivering the named legal good earns bonus gold, and the sheriff sees which route is hot.

**玩法改动 / Rule changes**
- 回合开始（装货前）公开揭示一张商路卡：例如“本回合奶酪 +6 金/张”。
- 商人在市场结算时（违禁品成功过关的那次结算）若包含该货物，每张额外得 6 金（现金立即到账，不是计分）。
- 警长也能利用该信息预判谁最可能走私相关货物。

**数值示例 / Example numbers**
- 商路赏金 = 对应合法货物价值的 1.5~2 倍（苹果 2 → +3~4；奶酪 3 → +4~6；鸡 4 → +6~8）。
- 每回合只揭示 1 条；连续 2 回合不重复同一货物。

**实现要点 / Implementation**
- 新增 `game.ROUTE_*` 状态 + 阶段首部揭示逻辑（在 `start_round` 里选路）。
- 结算处（`do_inspect_decision` 过关分支）给 `p.gold` 加赏金并广播事件。
- 视图 `view` 加 `route` 字段，GUI 顶部提示条显示。
- 服务器独立于客户端运行，因此这是“服务器级玩法模组”，需要全房间一致。

**平衡与难度 / Balance**
- 中低风险中回报，鼓励按公开信息决策，对新手友好。
- 风险：赏金过高会让所有人都盯着同一种货物，路线变化节奏要足够快。

**需要你拍板 / Decisions**
1. 赏金按“张”还是按“次成功过关”结算？
2. 商路信息要公开给所有人，还是只给警长（更刺激）？

---

## 提案 2：行会契约 / Guild Contracts

**一句话简介**：开局每人抽一张秘密契约（如“累计运进 4 只鸡”），游戏结束时完成则得大额金币奖励。
**One-liner**: Each player draws a secret contract at game start (e.g. deliver 4 chickens in total); completing it pays a large gold bonus at game end.

**玩法改动 / Rule changes**
- 游戏开始每人秘密抽 1 张契约卡（3 人局抽 1，4-6 人局抽 2 选 1 或直接 1 张）。
- 契约内容 = 某类合法货物的累计交付数量要求（含皇家品折算）。
- 结算在最终计分前进行：完成则 +20~30 金，并立即在聊天区通报。

**数值示例 / Example numbers**
- 简单契约：3 张苹果 / 2 张奶酪；奖励 +15。
- 困难契约：5 张鸡 / 4 张面包；奖励 +30。
- 皇家品按“等于几个普通品”折算进契约进度。

**实现要点 / Implementation**
- 需要持久化玩家级隐藏状态：`Player.contracts = [...]`，只在自己视图里可见（类似手牌）。
- `score()` 前新增 `_resolve_contracts()`，把奖励并入 `bonus`。
- 契约文本用货物 key + 数量描述，天然支持换皮模组。

**平衡与难度 / Balance**
- 高风险高回报，引导玩家围绕目标规划走私；与黑市任务并存时目标可能冲突，需限制契约种类避开黑市指定品。
- 困难点：契约完成的“计数口径”（按过关成功数，还是按最终摊位上的数量？）建议用后者，简单直观。

**需要你拍板 / Decisions**
1. 契约抽几张、是否允许弃掉重抽？
2. 计数按“最终摊位数量”还是“成功过关累计次数”？

---

## 提案 3：走私者同盟（连击套装）/ Smuggler's Guild (Combo Sets)

**一句话简介**：一次性把特定组合的违禁品运进城（例如 丝绸+酒 同袋过关），额外获得套装奖金。
**One-liner**: Deliver a specific contraband combo in one trip (e.g. Silk + Wine in the same bag) for a combo bonus.

**玩法改动 / Rule changes**
- 每种违禁品都有一个“黄金搭档”；同一趟（同一次申报过关）成功包含搭档组合 → 每套 +8~12 金。
- 组合信息公开（在摊位/规则面板显示），鼓励针对性走私。
- 与黑市任务可以叠加（同一袋咖啡既算任务又可能算套装，若存在套装）。

**数值示例 / Example numbers**
- 丝绸+弩：套装 +10；咖啡+酒：套装 +12；咖啡+丝绸：+8。
- 套装奖金不会因为警长查获而发放（被没收 = 失败）。

**实现要点 / Implementation**
- `game.py` 装货/过关分支处检测同袋类型集合，命中组合则在过关结算里加金并广播。
- 组合表放常量（`COMBO_SETS`），规则模组可 patch。
- 需要把“同袋组合”信息在过关时透传给结算函数（现在 `do_inspect_decision` 拿得到整袋卡）。

**平衡与难度 / Balance**
- 鼓励更激进的走私（袋子里混多种违禁品，申报难度更高），适合老玩家。
- 风险：套装奖金 + 黑市任务叠加会滚雪球，建议套装与任务二选一参与结算或限制同回合最多触发一次。

**需要你拍板 / Decisions**
1. 套装按“趟”还是按“套数”（同趟两套丝绸+弩给 2 次？）结算。
2. 是否允许和黑市任务同时叠加奖励。

---

## 提案 4：黑市拍卖 / Black Market Auction

**一句话简介**：每回合（或每隔一回合）开场前，所有商人用金币竞拍一张“隐藏违禁品卡”（从牌库随机抽出，拍卖时正面向下、只显示品类提示）。
**One-liner**: Before each round (or every other round) players bid gold for one hidden contraband card drawn from the deck (face-down, only a hint shown).

**玩法改动 / Rule changes**
- 新阶段“拍卖”插在市场阶段之前（或替代弃牌阶段）。
- 拍卖品：从牌库随机 1 张违禁品/皇家品，展示模糊提示（如“价值 ≥7”）。
- 暗标或公开轮叫价；成交金归“公库”（游戏结束平均分或弃置）。
- 拍到的人把该卡直接放进自己的袋/手（下回合装货可用）。

**数值示例 / Example numbers**
- 底价 5 金；成交通常 7~15 金（一张普通违禁品自身价值 6~9，但含“完成任务/套装”的期望价值）。
- 公库处理：游戏结束每人平分 1/4（小数向下取整），或直接烧掉。

**实现要点 / Implementation**
- 新增阶段状态机分支（`phase="AUCTION"`），多轮广播出价需要新增协议消息（`auction_bid`）。
- 拍卖品信息用“提示文本”而非真实类型，防止信息泄露——视图只给 hint。
- 这是对流程改动最大的提案之一，需要仔细设计超时/掉线处理。

**平衡与难度 / Balance**
- 金币消耗变多 → 现金计分占比下降，货物计分占比上升；要防止金币完全无用的极端。
- 适合喜欢嘴炮/博弈的中高阶玩家。

**需要你拍板 / Decisions**
1. 暗标还是公开叫价？
2. 拍卖所得金币去向（公库均分 / 烧掉 / 给警长）。

---

## 提案 5：皇家恩宠 / Royal Favor

**一句话简介**：皇家品单独一条“恩宠轨”，每次成功运进一张皇家品 +1 恩宠；达到里程碑立刻拿奖励（金币或临时能力）。
**One-liner**: Royal goods feed a separate "favor track"; each delivered royal card adds favor and unlocks milestone rewards.

**玩法改动 / Rule changes**
- 每个玩家的皇家品累计数量构成恩宠轨：2/4/6 张各触发一次奖励。
- 里程碑奖励示例：2 张 → +6 金；4 张 → 下回合可多装 1 张（袋上限 6）；6 张 → +15 金。
- 恩宠进度对所有人可见（皇家品本来就是公开陈列）。

**数值示例 / Example numbers**
- 里程碑：2→+6金，4→+10金，6→+18金（与普通计分叠加，皇家品照常计入“等于几个普通品”）。
- 若与“皇家品=2 张普通”计分重叠，皇家品会变得过强 → 建议恩宠轨与数量计分二选一，或调低里程碑金额。

**实现要点 / Implementation**
- `Player.royal_favor` 计数 + 结算钩子（过关成功时检查）。
- 视图 players 增加 `favor` 字段，GUI 玩家面板加进度条。
- “袋上限+1”类能力需要改 `do_load` 的 5 张限制为动态上限（一个很小的引擎改动）。

**平衡与难度 / Balance**
- 让皇家品成为真正的“高风险高回报”核心；与黑市任务抢节奏。
- 风险：皇家品数量有限（每局 1-2 张同款），多人抢同款会很卡；建议恩宠轨按“任意皇家品”累计，不按款式。

**需要你拍板 / Decisions**
1. 里程碑奖励只给金币，还是包含“临时能力”这种复杂效果？
2. 恩宠轨按任意皇家品累计，还是按单款累计？

---

## 提案 6：海关特派员 / Customs Inspector

**一句话简介**：每局 1 次，警长可以花 5 金“加开一次检查”，对同一个人再查一次（或指定第二个人开袋）。
**One-liner**: Once per game the sheriff may pay 5 gold for an extra inspection (re-inspect the same player or force-open a second bag).

**玩法改动 / Rule changes**
- 正常检查流程结束后，警长可选“特派检查”：花 5 金，再指定一名商人（不能是刚被查过的那位？）开袋。
- 特派检查不触发贿赂阶段（没收照常）。
- 若特派查获违禁品，警长额外得 +5 金；若查空，5 金不退。

**数值示例 / Example numbers**
- 特派费用 5 金；查获额外奖励 5 金；对“两袋违禁品”的商人威慑力很强。

**实现要点 / Implementation**
- `do_inspect_decision` 之后插入一个“可选追加”分支，需要新协议消息（`inspector_extra`）。
- 用一次性标记（`Player`/`Game` 上的 `inspector_used`）防滥用。
- 查获时钱款流转复用现有罚款逻辑。

**平衡与难度 / Balance**
- 给警长更强控制力，削弱“高风险走私”的舒适区；对 3 人局影响最大（警长频率高）。
- 建议 3 人局费用 6 金、查获奖励 4 金做微调。

**需要你拍板 / Decisions**
1. 特派检查是否允许带贿赂？（建议不允许，保持简单）
2. 费用/奖励数值是否按人数微调。

---

## 提案 7：商人声望 / Merchant Reputation

**一句话简介**：诚实申报（或查实无误）获得声望点，声望解锁小福利：多抽牌、罚款打折、弃牌上限提升。
**One-liner**: Honest declarations (or clean inspections) earn reputation; reputation unlocks perks such as extra draws, fine discounts, or a bigger discard limit.

**玩法改动 / Rule changes**
- 声望来源：申报被查实且完全诚实 +1；被查且无违禁品 +1；被查获违禁品 -1。
- 声望轨道 0~5；等级福利示例：
  - 1 点：市场阶段可弃 6 张（默认 5）；
  - 3 点：被罚金时打 9 折；
  - 5 点：回合结束可补到 7 张手牌（HAND_SIZE+1）。

**数值示例 / Example numbers**
- 声望在 3 人局约 6 回合可攒 3~4 点；门槛不宜太高。

**实现要点 / Implementation**
- `Player.reputation` + 各阶段钩子（市场弃牌上限、罚款系数、补牌数都改成变量）。
- 这些“变量化”是引擎小改动：`MAX_DISCARD`、`FINE_MULT`、`HAND_SIZE` 目前是常量，改成实例字段后规则模组就能 patch 默认值。
- 视图 players 加 `rep` 字段，GUI 显示小徽章。

**平衡与难度 / Balance**
- 长期策略深度 +，但会让“全走私流”玩家天然吃亏；要确保声望福利不至于让守法玩法碾压。
- 复杂度中等，对新手略不友好 → 可默认关闭。

**需要你拍板 / Decisions**
1. 声望是否公开可见（建议公开，制造谈判筹码）？
2. 福利清单用哪三条（上面的示例可替换）。

---

## 提案 8：贿赂经济（贿金池）/ Bribe Economics (Bribe Pot)

**一句话简介**：所有实际支付的贿金进入一个公开“贿金池”，游戏结束时由“最守法的玩家”（声望最高或查获最少）平分，或触发特殊事件。
**One-liner**: All bribes actually paid go into a public pot; at game end the pot is split or triggers a special event.

**玩法改动 / Rule changes**
- 警长收到贿金时，一半进私人钱包、一半进公池（或全进公池，规则可调）。
- 公池去向（选一）：游戏结束平均分 / 由“最诚实商人”独得 / 每 20 金触发一次全场小额分红。
- 贿赂变成“公共资源”博弈，减少“警长黑钱”的挫败感。

**数值示例 / Example numbers**
- 50% 进池；3 人局一局贿金通常 10~30 金，均分每人 5~10 金，影响可控。

**实现要点 / Implementation**
- `do_bribe` 处把金额拆成两份（一份进 `sheriff.gold`，一份进 `game.pot`）。
- 结束时 `score()` 加 `pot` 分配逻辑；需要“最诚实”定义（见决策）。
- 纯参数级改动，不需要新阶段，落地最容易。

**平衡与难度 / Balance**
- 低复杂度、高话题性；建议作为“可选常驻”规则。
- 风险：警长受贿动力下降 → 检查变少 → 走私变容易；需用“池子去向”平衡。

**需要你拍板 / Decisions**
1. 池子去向选哪种（均分 / 最诚实独得 / 定期分红）？
2. 进池比例（0% 就是原规则 / 50% / 100%）。

---

## 提案 9：夜市场（回合时限）/ Night Market (Round Timer)

**一句话简介**：给每个行动阶段加倒计时，超时自动弃权/自动随机行动，加快节奏。
**One-liner**: Add a countdown to each action phase; timeout auto-skips or plays a random action.

**玩法改动 / Rule changes**
- 房主开房时可选“夜市场模式”：装货 60s、申报 30s、检查 60s。
- 超时行为：装货=空袋自动封袋；申报=按袋内实际货物自动申报最接近的合法品；检查=默认不查。
- 与断线重连兼容（倒计时暂停于掉线玩家）。

**数值示例 / Example numbers**
- 默认值如上；房主可在房间页调整。

**实现要点 / Implementation**
- 服务器加计时器（`net.py` 的 `_drive_bots` 类似机制，每秒 tick），到点注入对应 action。
- 视图加 `time_left` 字段，GUI 顶部显示倒计时条。
- 属于“流程层”改动，但不需要新协议（复用现有 action 消息）。

**平衡与难度 / Balance**
- 纯体验优化，不改变数值；适合固定时长局。
- 风险：网络延迟高的玩家吃亏 → 倒计时至少 30s 起步。

**需要你拍板 / Decisions**
1. 是否做成“房主可选”，还是常驻？
2. 超时默认行为采用上面哪套？

---

## 提案 10：AI 人设包 / Bot Personalities

**一句话简介**：给现有简单/普通/困难 AI 加“性格参数”，让同一个难度下也有不同打法（多疑警长、贪婪商人、守法派）。
**One-liner**: Add personality parameters on top of the existing easy/normal/hard bots so same-difficulty bots play differently (paranoid sheriff, greedy merchant, honest trader).

**玩法改动 / Rule changes**
- 每个 AI 除了难度等级，还有一个性格标签（可选/随机）。
- 性格只微调决策权重，不改变难度上限：
  - 多疑警长：检查概率 +30%，受贿门槛提高；
  - 贪婪商人：装袋违禁品比例 +20%，更常贿赂；
  - 守法派：几乎只走私 1 张且低价品，市场弃牌更保守；
  - 豪赌客：经常整袋 5 张违禁品。

**数值示例 / Example numbers**
- 参数示例：`inspect_bias`（0.3~0.7）、`contra_ratio`（0.3~0.9）、`bribe_tendency`（0.2~0.8）、`bluff_rate`（0.1~0.6）。

**实现要点 / Implementation**
- `bot.py` 各决策函数目前接受 `level`，扩展成接受 `personality` 字典（默认按等级给默认参数）。
- 房间添加 AI 时可选“等级+性格”或“随机性格”；服务器校验与现有 bot 机制一致。
- 纯客户端主机侧改动，不涉及规则一致性（无新货物/数值）。

**平衡与难度 / Balance**
- 低风险高趣味；注意“豪赌客”在 hard 难度下容易过强，需要封顶参数。

**需要你拍板 / Decisions**
1. 性格由房主指定还是随机？
2. 是否让性格也影响命名（如“Bot-Hard 多疑”）？

---

## 实现优先级建议 / Suggested priority

1. **最容易落地（纯参数/小钩子）**：提案 8 贿赂经济、提案 9 夜市场、提案 10 AI 人设包。
2. **需要小引擎扩展点**：提案 1 商路、提案 2 契约、提案 5 皇家恩宠、提案 7 声望。
3. **需要新阶段/新协议**：提案 4 拍卖、提案 6 特派检查（6 是其中较轻的）。

## 需要你决定的全局问题 / Global decisions for you

1. 规则模组要做到“结构性玩法”需要给 `game.py` 加扩展点（阶段钩子、动态上限），这会让引擎代码更复杂——你接受多大改动量？
2. 这些玩法模组是否都走“全房间一致 + 一键安装”的服务器校验？（建议：涉及新阶段/新数值的全部走校验；纯 UI/计时类可以不校验。）
3. 先做哪 1-2 个？建议先做 **提案 8（贿赂经济）** + **提案 10（AI 人设）**，改动小、见效快。
