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
- `cyberpunk_mod/` —— 赛博朋克换皮：所有货物名、阶段名、界面关键词改为霓虹赛博风格（v1.1.0，支持聊天文本换名）。
- `medieval_mod/` —— 中世纪英格兰换皮：果园苹果、修道院奶酪、战弩与蜂蜜酒。
- `starlight_mod/` —— 星光殖民地（星际）换皮：水培苹果、等离子弩与星云酒。
- `steampunk_mod/` —— 蒸汽锻炉城换皮：黄铜苹果、发条鸡与蒸汽弩。
- `arcane_mod/` —— 奥术秘境（魔法）换皮：仙灵苹果、奥术弩与精灵酒。
- 换皮模组只修改本地显示文本与配色，**仅客户端生效**：联机时每个玩家只能看到自己模组的版本，服务器规则不受影响（v1.3.0 起聊天消息中的货物名也会按本地模组显示）。

## 模组市场 / In-game Mods Market

主菜单点「模组市场」即可在线浏览并一键下载安装社区模组（下载到当前可写的模组目录，之后到「模组」界面启用并重启游戏）。市场清单托管在 GitHub，支持 raw + jsDelivr CDN 双源回退。