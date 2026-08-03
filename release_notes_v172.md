# v1.7.2 - Settings overhaul, smooth rendering & UI feedback

**English / 中文**

## English
- **New: Settings screen rebuilt** (following the usual game-settings layout). Left panel: resolution presets + custom width/height. Right panel: display mode (Windowed / Borderless / Fullscreen) and screen fit (Fit keep ratio / Stretch no black bars). Changes are staged and applied with one Apply button, Restore defaults resets everything, and a status line shows unsaved changes or success.
- **New: Stretch mode removes black bars.** When the window ratio does not match the game's 16:10 canvas, you can stretch to fill the window edge-to-edge (slight distortion) instead of letterboxing.
- **Fix: no more pixelated/jagged edges at big window sizes.** The canvas is scaled to the window with smooth bilinear resampling plus a cached presentation surface, so 1920x1080 / 2560x1440 presets look clean.
- **Fix: screen-transition animation no longer lags.** The fade overlay and the scaled frame are cached and the fade is shorter; the update screen now runs at 90+ FPS even at 2560x1440.
- **New: button feedback.** Buttons glide to their hover color, sink 2px while pressed, and flash a soft white ring when clicked.
- **Fix: Black Market submit buttons realigned.** Every quest row has its Submit button at the row's right edge, exactly matching the panel layout (grayed until claimable).
- **Change:** all bundled mod versions are synced with the game build (1.7.2).

## 中文
- **新增：设置页整体重做**（参考主流游戏设置布局）。左侧：分辨率预设 + 自定义宽高；右侧：显示模式（窗口模式 / 无边框 / 全屏）与画面适配（适应保持比例 / 拉伸填满无黑边）。更改先暂存，点击"应用"后生效，"恢复默认"一键还原，并有状态提示显示未保存或已应用。
- **新增：拉伸填满模式可消除黑边。** 当窗口比例与游戏 16:10 画布不一致时，可选择拉伸填满窗口（略有变形）而不是留黑边。
- **修复：大窗口下不再出现像素块/毛边。** 画布改用双线性平滑缩放并缓存呈现面，1920x1080 / 2560x1440 等预设下画面更清晰。
- **修复：切屏动画不再卡顿。** 淡入遮罩与缩放帧均改为缓存复用、过渡更短；更新页在 2560x1440 下仍保持 90+ FPS。
- **新增：按钮反馈动画。** 悬停颜色平滑过渡、按下下沉 2px、点击时闪烁一圈柔光。
- **修复：黑市提交按钮位置重排。** 每个任务行的右侧对齐一个提交按钮，与面板布局精确对应（不可领取时置灰）。
- **同步：** 所有内置模组版本与游戏版本同步为 1.7.2。
