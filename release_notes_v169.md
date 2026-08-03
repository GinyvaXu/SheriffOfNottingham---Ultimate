# v1.6.9 - Auto-update works in mainland China

**English / 中文**

## English
- **New: update checks and installer downloads no longer depend on reaching GitHub directly.** The game now tries several community GitHub acceleration proxies usable from mainland China (**ghfast.top**, **gh-proxy.com**, **ghproxy.net**, **gh.llkk.cc**) in order — for both the update manifest and the installer download — so checking and updating keep working even when `api.github.com` / `raw.githubusercontent.com` are slow or blocked.
- **New: custom mirror support.** Advanced users can point the game at their own mirror (for example a Gitee repo) by creating `%APPDATA%/SheriffOfNottingham/mirror.json`:
  ```json
  {"manifest": "https://gitee.com/USER/REPO/raw/main/update.json",
   "installer": "https://gitee.com/USER/REPO/releases/download/v1.6.9/Setup.exe"}
  ```
  Both keys are optional; the manifest is then checked first, and the installer is downloaded from your mirror (GitHub proxy mirrors still apply if the value itself is hosted on GitHub).
- **New: mod-market downloads use the same proxy fallback** and prefer fresh GitHub sources over the stale jsDelivr cache.
- **Fix:** the update error screen now explains mainland-China GitHub restrictions and points to the manual download page.
- **Change:** all bundled mod versions are synced with the game build (1.6.9).

## 中文
- **新增：更新检测与安装包下载不再依赖直连 GitHub。** 游戏会按顺序自动尝试多个国内可用的 GitHub 加速镜像（**ghfast.top**、**gh-proxy.com**、**ghproxy.net**、**gh.llkk.cc**）——更新清单与安装包下载都走同样的多源回退，即使 `api.github.com` / `raw.githubusercontent.com` 被屏蔽或限速，也能正常检查与更新。
- **新增：自定义镜像支持。** 高级用户可在 `%APPDATA%/SheriffOfNottingham/mirror.json` 配置自建镜像（例如 Gitee 仓库）：
  ```json
  {"manifest": "https://gitee.com/用户名/仓库/raw/main/update.json",
   "installer": "https://gitee.com/用户名/仓库/releases/download/v1.6.9/Setup.exe"}
  ```
  两个字段都可选；配置后优先使用该镜像检查更新与下载安装包（若镜像地址本身托管在 GitHub，仍会套用加速镜像回退）。
- **新增：模组市场下载同样接入国内加速镜像**，并优先使用 GitHub 实时源，避免 jsDelivr 缓存滞后。
- **修复：** 更新失败界面现在会提示国内网络访问 GitHub 受限的原因，并引导点击「打开更新页面」手动下载。
- **改动：** 所有内置模组版本与游戏版本同步为 1.6.9。
