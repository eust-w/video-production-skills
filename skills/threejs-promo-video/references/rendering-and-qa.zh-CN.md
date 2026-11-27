# 渲染与质检

[English](rendering-and-qa.md) | 简体中文

## 模板结构（`assets/template/`）

| 文件 | 作用 |
| --- | --- |
| `storyboard.json` | 全部内容与时间：品牌、主题、开场钩子、步骤、字幕、镜头、落版。从 `storyboard.example.json` 复制 |
| `public/main.js` | three.js 场景与 2D 叠加层；暴露 `window.renderFrame(t)` 和 `window.ready` |
| `public/index.html` | import map，从 `node_modules` 加载 `three` |
| `render.mjs` | 本地静态服务 + Playwright + FFmpeg 管道：`--stills` 或 `--video`、`--lang`、`--storyboard`、`--browser` |
| `gen-audio.mjs` | 按 storyboard 自动卡点的合成配乐，输出 `music.wav` |
| `sample/` | 虚构界面与 `make-sample-shots.mjs`，没有真实素材时也能先渲染 |

依赖：Node.js 18+，`npm install`（three、playwright），`PATH` 里有 FFmpeg，以及 Google Chrome 或 `npx playwright install chromium`。字体：中文用苹方或 Noto CJK，西文用 Avenir 或 Inter；字体栈会自动回退。

## 镜头字段

- `img`：相对项目根目录的路径；也可以是前缀加 `seq: N`（可选 `ext`），表示 `img0.png … imgN-1.png` 在镜头时长内依次播放。真实的进度变化（如阶段条推进）用序列表现。
- `frame`：相机取景矩形；`frame2` + `pan: [t0, t1]` 表示在同一镜头内平移到第二个矩形（例如从审核意见移到「批准」按钮）。
- `spot`：高亮矩形（其余区域压暗），`call` 是标注气泡文字；`checks: {x, ys, start, gap}` 给清单逐条打勾。
- 所有矩形都用截图像素坐标（`screen.width × screen.height`）；同一项目的所有截图必须是同一尺寸。

取景要紧：`frame` 宽 700–900 px 时约放大 2.5 倍，14 px 的界面字才看得清。取景太宽是最常见的错误。

## 确定性

- `update` / `composite` 里不要用 `Math.random()` 或系统时间，用带种子的 `rng()` 和 `t`。画布纹理只在状态键变化时重绘。
- 渲染静帧前会先预热一帧；视频按顺序渲染，纹理上传已预热。
- 想实时预览：用任意静态服务器以项目根目录为根，打开 `public/index.html?play&lang=en`。

## 已踩过的坑

- **画布状态泄漏**：重绘之间状态会残留（如上次的 `textAlign = center` 让下次文字错位）。模板在 `upd()` 里调用了 `ctx.reset()`，不要删。
- **浅色界面泛光**：亮度超过 bloom 阈值就会糊。屏幕颜色用 `0xeeeeee`、阈值 0.9；只有 HDR 强调色（`color × k > 1`）会发光。
- **镜头切换时整屏发白**：深色风格里很刺眼。模板会在高亮出现前先压暗屏幕。
- **标注与顶栏 / 字幕冲突**：气泡会自动翻到高亮区上方或下方，并限制在 y = 165 到 H − 220 之间。
- **字幕过长溢出**：模板会缩到画面宽度的 86%，但应该改写文案，不要依赖它。
- **`server.listen()` 是异步的**：要等它完成再读端口（`render.mjs` 已处理）。
- **FFmpeg 没有 `drawtext`**（Homebrew 版常见）：联系表只用 `scale` 和 `tile`，按序号推算时间（`t = step × k`）。
- **静帧排序**：文件名补零（`t012.60.jpg`），`-pattern_type glob` 才会按时间排序。
- **无头 WebGL 速度**：用本机 Chrome（`channel: 'chrome'`，macOS 上走 ANGLE/Metal），30 秒 1080p 约 35–45 秒出片；自带 Chromium 会退回 SwiftShader，慢很多。

## 交付前检查清单

1. 每种语言在每个镜头的开头、中间、结尾各出静帧，拼成联系表。检查可读性、遮挡、顶栏与步骤条、字幕冲突。
2. 完整出片后跑 `scripts/contact_sheet.sh out.mp4`：时长等于 storyboard，响度约 −14 到 −13 LUFS（必要时调 `gen-audio.mjs` 里的 `norm`）。
3. 专门看每个切换点后 0.5 秒的过渡帧，确认没有空画面或过曝。
4. 确认打码在最终成片里仍然有效，而不只是在源静帧里。
5. 汇报时说明是否完整看过、听过成片；只看了静帧就如实说。
