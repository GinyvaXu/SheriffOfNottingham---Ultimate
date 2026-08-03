# 模组（Mod）说明 / Mod Guide

把模组文件夹放进本目录（`mods/`），游戏启动时自动加载。每个模组是一个子文件夹，
至少包含 `mod.json`；可选 `mod.py`（Python 代码）和 `assets/`（资源文件）。

一个模组文件夹示例：`example_mod/`（默认禁用，可直接复制开启研究）。

## mod.json（清单）

```json
{
  "id": "example_mod",            // 唯一 id（缺省用文件夹名）
  "name": "Example Mod",          // 显示名称
  "version": "0.1.0",
  "description": "说明文字",
  "enabled": true                 // false 则跳过加载（不删除即可停用）
}
```

## mod.py（可选代码）

定义了 `register(api)` 就会在启动时被调用，api 提供：

- `api.add_legal(key, name_en, name_zh, value, fine, cnt3, cnt6, color, king_bonus, queen_bonus)`
  新增合法货物（苹果/鸡肉这类，可申报）。
- `api.add_contraband(key, name_en, name_zh, value, fine, cnt3, cnt6, color)`
  新增违禁品（丝绸/咖啡这类，会被没收）。
- `api.add_royal(key, name_en, name_zh, of, equals, value, fine, cnt3, cnt6, color)`
  新增皇家货品（违禁品，结算时按 `equals` 倍计入对应合法货物 `of`）。
- `api.patch("game", "HAND_SIZE", 7)` —— 直接修改游戏本体属性（改规则用）。
- `api.get("game", "BAG_MAX")` —— 读取游戏属性。

说明：

- `key` 是内部编号（自动转大写），`name_en`/`name_zh` 是显示名，`value` 是价值，
  `fine` 是错查/查到罚款（缺省等于价值），`cnt3`/`cnt6` 是 3 人局 / 4-6 人局卡牌数，
  `color` 是卡面颜色 RGB（可选）。
- 合法货物默认没有终局名次奖励；要设置请在 `add_legal` 里传 `king_bonus`/`queen_bonus`。
- 模组代码出错的模组会被跳过并在游戏菜单里提示，不会导致游戏崩溃。
- 联网对局时，**所有玩家需要安装相同的内容模组**（房主服务器执行规则，
  客户端需要模组的名称/颜色来显示卡牌）。
- 卸载：删除对应文件夹即可；游戏安装包卸载时会一并删除 `mods/` 目录。

## 内置模组管理界面 / In-game Mods screen

主菜单点「模组」即可打开模组管理：查看所有已安装模组的名称/版本/说明，
一键启用或禁用（写回各自 `mod.json`），刷新列表。修改会在下次启动游戏时生效。
损坏模组的加载错误也会显示在这里。
## 内置模组 / Bundled mods

- `example_mod/` —— 最简单的示例：新增茶叶（违禁品）与梨（合法货物），默认禁用。
- `cyberpunk_mod/` —— 赛博朋克换皮：磁轨枪、神经兴奋剂、夜酿与记忆丝绸等未来都市货物（v1.2.0，支持聊天文本换名）。
- `medieval_mod/` —— 中世纪英格兰换皮：肥育阉鸡、修道院奶酪、燕麦面包与修士蜜酒。
- `starlight_mod/` —— 星光殖民地（星际）换皮：水培果、蛋白块、等离子步枪与星云酒。
- `steampunk_mod/` —— 蒸汽锻炉城换皮：发条禽、齿轮奶酪、蒸汽步枪与煤烟威士忌。
- `arcane_mod/` —— 奥术秘境（魔法）换皮：仙灵果、使魔母鸡、奥术法杖与精灵酒。
- 换皮模组只修改本地显示文本与配色，**仅客户端生效**：联机时每个玩家只能看到自己模组的版本，服务器规则不受影响（v1.3.0 起聊天消息中的货物名也会按本地模组显示）。

## 玩法模组 / Rule mods

玩法模组会改变游戏规则；联机对局时**全房间玩家必须安装同一组玩法模组**（服务器校验 id + 版本，缺失时大厅可一键下载安装）。内置玩法模组：

- `rules_bribe_pot` —— 赏金经济（Bribe Economics）：每笔被接受的赏金有一半进入公开赏金池，结束时均分。
- `rules_guild_contracts` —— 行会契约（Guild Contracts）：开局发放秘密契约，完成后结算金币奖励。
- `rules_marathon_market` —— 马拉松集市（Marathon Market）：规则模组：延长对局，每名玩家默认两回合改为三回合（3人局为4回合）。房间内所有玩家都需安装此模组。
- `rules_merchant_reputation` —— 商人声望（Merchant Reputation）：玩法模组：查实说真话声望 +1，被查出违禁品声望 -1（仅合法货物与申报不同不扣声望）。声望影响抽牌：正声望抽到合法货概率梯度上升（声望5约90%），负声望抽到违禁品概率上升但封顶约70%，留有翻盘余地。1/3/5 点额外解锁：市场多弃1张、罚金-10%、补牌至7张。
- `rules_night_market` —— 夜市场时限（Night Market Timer）：每个阶段 40 秒动作倒计时，超时自动执行默认动作。
- `rules_royal_favor` —— 皇家恩宠（Royal Favor）：皇家卡累计恩宠，2/4/6 张触发 +6/+10/+18 金。
- `rules_spice_road` —— 香料之路（Spice Road）：规则模组：新增合法货物胡椒与违禁品茶叶。房间内所有玩家都需安装此模组。
- `rules_trade_caravans` —— 车队商路（Trade Caravans）：每回合公开商路，指定法定货物每张过关 +4 金。
- `rules_wild_card` —— 万能卡（Wild Card）：玩法模组：牌库中加入 n 张万能卡（房主在大厅设置数量）。申报时袋中的万能卡自动变成所申报的合法货物，属于合法品不会被没收。
- `rules_sheriff_intel` —— 警长情报（Sheriff Intel）：玩法模组：每回合警长有一次机会支付金币（等于剩余未查玩家袋中物品数量之和），获知剩余袋中违禁品的数量区间（0-2 / 3-5 依此类推）。仅当待查商人不少于两人时可用。
- `rules_super_contraband` —— 超级违禁品（Super Contraband）：玩法模组：每种违禁品加入一张超级违禁品，价值与罚金均为该类普通违禁品的三倍（如超级咖啡价值18、超级弩价值27）。被检查时按普通违禁品同样没收并罚款。

## 模组市场 / In-game Mods Market

主菜单点「模组市场」即可在线浏览并一键下载安装社区模组（下载到当前可写的模组目录，之后到「模组」界面启用并重启游戏）。市场清单托管在 GitHub，支持 raw + jsDelivr CDN 双源回退。