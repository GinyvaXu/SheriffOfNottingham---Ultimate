[English](README.md) | **中文**

# 诺丁汉警长 - Python 极简联机版

经典桌游《诺丁汉警长》的 Python 极简实现。功能完整、代码简洁、模块化设计。
经典规则外加两个可选模块（皇家赏赐卡与黑市任务），均可开关。
v1.1.0 新增**模组系统**与**可安装/可卸载的安装包**。

## 文件结构

```
game.py      规则与状态机（纯逻辑，不含界面/网络）
bot.py       人机 AI 模块（简单/普通/困难，运行在房主服务器上）
net.py       TCP 服务器 + JSON 协议 + 断线/重连 + 人机驱动
gui.py       pygame 纯按钮界面
mods.py      模组加载器（exe 旁的 mods/ 目录，ModAPI 支持添加/修改）
lang.py      中英双语文本 + 模组卡牌名重建
main.py      入口（--version 弹出版本对话框）
version.py   __version__ = "1.1.0"
installer.iss  Inno Setup 安装脚本
test_bot.py  无头人机自动化测试（完整对局 + 断线重连）
test_ai_bots.py  大厅人机测试（房主添加机器人并完整对局）
test_new_rules.py  皇家赏赐卡 & 黑市任务单元测试
test_mods.py 模组加载器单元测试（注册/修改/启用/禁用/报错）
test_back_lobby.py  结算返回房间 + 同难度人机命名测试
mods/        内置模组目录（README.md + example_mod，默认禁用）
```

## 依赖与安装

- Python 3.10+
- `pip install pygame`

## 语言

- 界面中英双语：默认中文，可切换英文。
- 菜单/大厅右上角按钮切换，或启动时加 `--lang en`。
- exe 内置中文字体（微软雅黑），无需系统字体即可正常显示中文。
  如需替换，放入 OFL 字体为 `assets\NotoSansCJKsc-Regular.otf`。
- 聊天/名字支持中文输入法（pygame 文本输入），也支持 Ctrl+V 粘贴。

## 快速开始

**开房（房主）：**
```
python main.py --host --players 4 --port 5555 --name ZhangSan
```
`--players` 为座位上限，2-5 人。房主在大厅点击"开始游戏"；游戏按实际加入人数
调整。大厅中房主可设置回合数（默认每人当两次警长）以及修改自己的名字。

**加入：**
```
python main.py --join 192.168.1.5:5555 --name LiSi
```

**局域网**：直接连接房主局域网 IP。大厅中房主可点"复制地址"把 `LAN_IP:port`
复制到剪贴板发给好友，菜单里也有"粘贴"按钮可直接填入收到的 `IP:port`。
**互联网**：游戏不内置穿透，房主自行端口映射（二选一）：
- 路由器端口转发：把公网端口转发到房主机器的 5555。
- 穿透工具（frp / ngrok 等）：把公网端口映射到本地 5555。
- 然后把 `公网IP:端口` 发给好友加入。

## 人机（AI 机器人）

- 大厅中房主可添加简单/普通/困难三档机器人填补空位，开始前也可移除。
- 机器人在房主服务器上自主行动（市场弃摸牌、装袋、申报、贿赂、检查、黑市提交），
  不占用网络连接，决策只使用公开信息。
- 同难度的多个人机会自动编号命名（如 Bot-Easy 1、Bot-Easy 2），方便区分。
- 支持单人游玩：1 名真人 + 1-4 名机器人。

## 模组系统（v1.1.0 新增）

`mods/` 目录（exe 旁；源码运行时为项目根目录）下，每个含 `mod.json` 的文件夹
就是一个模组：

```json
{
  "id": "example_mod",
  "name": "Example Mod",
  "version": "0.1.0",
  "description": "添加茶叶（违禁品）与梨（合法货物）。",
  "enabled": false
}
```

- `enabled: true` 即加载该模组；文件夹内可有 `mod.py`，其 `register(api)` 函数
  会在启动时被调用。
- `ModAPI` 支持添加卡牌类型或直接修改游戏本身：

```python
def register(api):
    api.add_contraband("TEA", "Tea", "茶叶", value=5, fine=3, cnt3=8, cnt6=12, color=(90, 160, 120))
    api.add_legal("PEAR", "Pear", "梨", value=3, fine=2, cnt3=24, cnt6=24,
                  king_bonus=10, queen_bonus=5, color=(140, 200, 90))
    api.patch("game", "HAND_SIZE", 7)     # 例如修改手牌上限规则
```

- `add_legal` / `add_contraband` / `add_royal` 注册新卡牌类型，可指定
  3 人局与 4-6 人局的卡牌数量（`cnt3`/`cnt6`）、颜色、价值、罚款，
  合法货物还可指定第一名/第二名终局奖励（`king_bonus`/`queen_bonus`）。
- `patch("game", 属性, 值)` / `get("game", 属性)` 可直接读写任意引擎属性（改规则）。
- 损坏的模组会被跳过并在菜单页显示错误，绝不会导致游戏崩溃。
- 完整 API 见 `mods/README.md`（中英双语）与示例 `mods/example_mod/`。
- 同一房间的玩家应安装相同的内容模组：服务器决定规则，客户端只需名称/颜色来渲染卡牌。

## 安装包（v1.1.0）

`installer\SheriffOfNottingham-Setup-1.1.0.exe` 是 Inno Setup 制作的常规 Windows 安装程序：

- 安装游戏本体 + `mods\` 目录 + 桌面/开始菜单快捷方式。
- 可在系统"应用"中彻底卸载，会删除整个应用目录（含玩家自行添加的模组）。
- 支持中英文安装界面（安装时选择）。
- 重新构建：先运行 `打包.bat`，再执行 `ISCC.exe installer.iss`。

## 规则说明

- 市场：玩家可弃掉最多 5 张手牌，再从牌堆补回等量。弃牌堆保密，且不能再从中摸牌。
- 每种货物价值/罚款固定，卡牌数量随人数变化。
- 经典规则含 4 种合法货物（苹果/鸡肉/奶酱/面包）与 4 种违禁品（丝绸/弩/咖啡/酒），
  外加皇家赏赐卡。
- 黑市任务：某违禁品走私成功满 3 张自动提交，3 张卡弃掉，奖励
  （第一名 30-35 金币、第二名 25-30）全局通报，已完成的黑市任务其他人无法再做。

## 游戏流程

- **市场**：选择弃掉 0-5 张手牌，然后从牌堆补回相同数量。
- **装袋**：秘密挑选 1-5 张牌放入布袋，然后封袋。
- **申报**：选择一种合法货物并确认（数量强制等于袋中张数，种类可以撒谎）。
- **检查**：袋主可先贿赂（金币+备注）；警长决定放行或检查。
- **聊天**：右下输入框，回车发送；另有快捷短语按钮。

## 结算后返回房间

- 对局结束（结算界面）点击**返回房间**即可让所有人回到同一房间的大厅
  （座位与人机保留，房主可开新一局），也可点"退出"离开游戏。

## 断线 / 重连

对局中断线会等待该玩家（不托管、不判负）。用**相同名字**重进同一房间即可恢复座位；
客户端也会自动重连。

## 自动化测试

```
python test_new_rules.py              # 皇家赏赐卡 + 黑市任务单元测试
python test_mods.py                   # 模组加载器测试
python test_back_lobby.py             # 结算返回房间 + 人机命名测试
python test_bot.py --players 3        # 3 人完整对局（含断线/重连）
python test_bot.py --players 5        # 5 人对局
python test_ai_bots.py --rounds 2     # 大厅人机测试
```

## 已知限制

- 信任模式：房主即服务器，理论上可作弊，仅适合熟人之间。
- 中英双语界面（默认中文；字体加载器保留系统中文字体兜底）。
- 明文 TCP，无加密与反作弊。
- 公网直连取决于 NAT 类型；失败可用 frp/ngrok 中转。
- 贿赂简化为金币+备注，不校验货物/承诺。

## 打包成 exe

```
打包.bat                        # 或手动执行下面命令
python -m PyInstaller --clean --noconfirm SheriffOfNottingham.spec
```

- 生成 `dist\SheriffOfNottingham.exe`（约 41MB，单文件，无需安装 Python），
  带 1.1.0 版本信息与内置 `mods\` 副本；运行时读取 exe **旁**的 `mods\` 目录，
  可自由增删模组。
- 房主首次运行会触发 Windows 防火墙提示，请允许以开放端口。
- 查看报错可改用 `--console` 打包，或直接运行 `python main.py`。
- exe 支持相同命令行参数：`SheriffOfNottingham.exe --host --players 4`
  或 `SheriffOfNottingham.exe --join 192.168.1.5:5555`。