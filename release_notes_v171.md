# v1.7.1 - Faster, China-friendly update check

**English / 中文**

## English
- **New: the update check now runs in parallel.** Every mirror (GitHub acceleration proxies, raw GitHub, jsDelivr CDN, GitHub API) is probed at the same time under one shared deadline, so a full check finishes in a few seconds instead of up to a minute. No more long hangs or "check timed out" on slow mainland-China networks.
- **New: jsDelivr CDN sources added** (cdn / fastly / gcore edges) - fast and reliable from mainland China. When several sources answer, the HIGHEST version wins, so a stale CDN cache can never hide a newer release.
- **Fix: GitHub release list cleaned up.** An old draft release (v1.5.3) was left unpublished at the top of the list; it has been removed so `releases/latest` and the page both point at v1.7.x correctly.
- **Tip:** if your network blocks every built-in source, create `%APPDATA%/SheriffOfNottingham/mirror.json` with `{"manifest": "https://...", "installer": "https://..."}` to use your own mirror (for example a Gitee repo).
- **Change:** all bundled mod versions are synced with the game build (1.7.1).

## 中文
- **新增：更新检查改为并行。** 所有镜像源（GitHub 加速代理、raw GitHub、jsDelivr CDN、GitHub API）同时探测并共用一条全局时限，整个检查只需几秒，不再在国内慢速网络上长时间卡住或显示"检查超时"。
- **新增：加入 jsDelivr CDN 源**（cdn / fastly / gcore 边缘节点），国内快速稳定；多源同时返回时取版本号最高者，旧 CDN 缓存永远不会掩盖新版本。
- **修复：清理 GitHub Release 列表。** 旧版 v1.5.3 的草稿发布曾悬在列表顶部，现已移除，`releases/latest` 与发布页均正确指向 v1.7.x。
- **提示：** 若网络屏蔽了所有内置源，可在 `%APPDATA%/SheriffOfNottingham/mirror.json` 配置自建镜像：`{"manifest": "https://...", "installer": "https://..."}`（例如 Gitee 仓库）。
- **同步：** 所有内置模组版本与游戏版本同步为 1.7.1。
