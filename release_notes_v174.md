# v1.7.4 - 6-player crash fix & font robustness

**English / 中文**

## English
- **Fixed the 6-player "Passed a NULL pointer" crash.** The nameplate font "shrink" loop actually *grew* the point size (the pixel line height is larger than the point size), so a long name in a narrow 5-6 player panel ramped the font up until SDL_ttf returned a broken font and the next text measurement crashed the game. Name fonts now shrink correctly and absurdly long names are trimmed with an ellipsis.
- **Font loading is now validated.** get_font probes every font right after loading, so corrupt/truncated font files (for example from a broken install or an interrupted update) are skipped instead of crashing the next time text is drawn.
- **Sync:** all bundled mod versions are synced with the game build (1.7.4).

## 中文
- **修复 6 人局"Passed a NULL pointer"崩溃。** 玩家名牌的"缩小字体"循环其实在反向放大字号（像素行高大于字号），窄面板（5-6 人局）遇到较长名字时字号一路暴涨，直到 SDL_ttf 返回坏字体，下一次测量文本时游戏直接崩溃。现在名牌字体会正确缩小，超长名字自动以省略号截断。
- **字体加载增加校验。** get_font 每次加载后都会实测字体可用性，损坏/截断的字体文件（例如安装或更新中断产生）会被自动跳过，不再导致文字渲染崩溃。
- **同步：** 所有内置模组版本与游戏版本同步为 1.7.4。
