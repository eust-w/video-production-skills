# 媒体契约与命令

[English](media-contracts.md) | 简体中文

以下路径均按任务指定。使用中保留已安装 Skill 源码和模板，将模板复制到产物目录后传入显式输入。工具没有项目专属目录依赖。

## 依赖

完整流程需要 Python 3.10+、Node.js、FFmpeg/FFprobe 和可用浏览器。Python 依赖见 `assets/requirements.txt`。使用已有兼容环境或任务隔离环境，不修改全局包。

```sh
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/product-demo-video"
TASK_MEDIA_DIR="/absolute/path/to/demo-artifacts"
mkdir -p "$TASK_MEDIA_DIR"
python3 -m venv "$TASK_MEDIA_DIR/.venv"
"$TASK_MEDIA_DIR/.venv/bin/pip" install -r "$SKILL_DIR/assets/requirements.txt"
```

通过可用运行时工具、项目依赖解析或显式模块／可执行文件发现 Playwright 和浏览器安装位置。Codex desktop 可通过 `load_workspace_dependencies` 定位随包 Node 依赖。路径写在任务局部命令中，不写回 Skill。FFmpeg 不含 `libass` 也可用：合成器把字幕渲染为 PNG 叠层。

中文旁白字幕需要覆盖中文字形的字体。平台自动发现失败时显式传入字体；缺字应明确失败，不输出方框。当前选项以工具 `--help` 为准。

## 计划

复制 `assets/plan.example.json`。章节 ID 唯一且适合作文件名，`chapters` 顺序就是影片顺序。产品名与时长只是示例。

```json
{
  "product": "NOVA",
  "pronunciations": {"NOVA": "N O V A"},
  "video": {"width": 1600, "height": 1000, "caption_band": 120, "fps": 30},
  "chapters": [
    {"id": "intro", "title": "从一个问题开始", "narration": "NOVA 帮你整理信息。"},
    {"id": "inspect", "title": "查看结果", "narration": "这里用演示数据说明操作。", "persistent_label": "演示数据"}
  ]
}
```

`video.height` 是素材画面高度，最终高度为 `height + caption_band`。1920×1080 成片若用 120 像素字幕带，设置 width=1920、素材 height=960。

`narration` 是精确显示文本，`pronunciations` 只改变指定术语读法。显式声明缩写发音。若提供 `pronunciation_script`／`voice_text`，必须与声明的替换一致，不能静默改变旁白。

## 旁白与字幕

默认声音和参数来自 `assets/voice-profile.json`。服务在线，只发送已审阅旁白；随包客户端为第三方 Edge 神经语音客户端，不保证服务可用。声音目录失败或所选声音缺失应报错，不因此换成系统语音。

```sh
"$TASK_MEDIA_DIR/.venv/bin/python" "$SKILL_DIR/scripts/narrate.py" \
  --plan "$TASK_MEDIA_DIR/plan.json" --output "$TASK_MEDIA_DIR/audio"

"$TASK_MEDIA_DIR/.venv/bin/python" "$SKILL_DIR/scripts/narrate.py" \
  --plan "$TASK_MEDIA_DIR/plan.json" --output "$TASK_MEDIA_DIR/audio" --generate
```

第一条离线验证，第二条合成。新声音／版本使用新目录。`--generate --resume` 只复用当前且哈希正确的音频，全部可复用时可离线运行。修改章节后用 `--generate --resume --overwrite` 重生变化内容并保留其他有效章节。`--chapters` 可选子集，但清单仍描述完整计划；缺失或过期章节不能得到完整状态。临时网络失败时保留所选声音与有效分块，网络恢复后用 `--resume` 重试，保留 TLS 验证。不能手改哈希或将部分清单说成完整影片。

音频清单包含 `status`、`plan_sha256`、声音设置与 `chapters`。每章记录 `id`、`display_text`、`speech_text`、`wav_file`、实际时长、哈希、服务原始边界和字幕：

```json
{"start_seconds":0.1,"end_seconds":2.8,"text":"这里用演示数据说明操作。"}
```

字幕时间相对该音频文件起点，合成器会加入实际章节与旁白放置偏移。调和短重叠或引号缺失时保留原始边界元数据，文案变化需要更新音频。

## 浏览器录制

检查目标界面后修改可信的任务局部 `assets/scenario.example.cjs` 副本。其导出异步函数，接收 page、context、browser、base URL、输出目录与 marker 函数。封装负责捕获和清理，scenario 只负责任务获授权的产品操作。

```sh
node "$SKILL_DIR/scripts/record.cjs" --help
node "$SKILL_DIR/scripts/record.cjs" \
  --scenario "$TASK_MEDIA_DIR/scenario.cjs" \
  --output "$TASK_MEDIA_DIR/recordings/inspect" \
  --url "http://127.0.0.1:PORT/" \
  --playwright-module "/discovered/playwright/module" \
  --executable "/discovered/browser/executable"
```

将 `PORT` 和发现路径换成实际值。独立捕获上下文不替代应用授权，Skill 包内不能含 cookie、密钥或环境凭据。

## 剪辑决策

复制 `assets/edit.example.json`。顶层对象把章节 ID 映射到剪辑决策。源路径相对 edit JSON 所在目录，裁切秒数相对源文件，不是墙钟时间。可在不同章节合理复用源素材。

```json
{
  "inspect": {
    "segments": [
      {"path":"recordings/query.webm","start":1.2,"end":6.8},
      {"path":"recordings/query.webm","start":20.0,"end":26.0,"crop":[200,120,1100,700]}
    ],
    "label":"演示数据"
  }
}
```

`crop` 为源像素 `[x,y,width,height]`。可选 `speed` 改变实际片段速度，显著变化应向观众说明。`fit_to_voice` 允许有限整章加速。优先裁掉空等，不把点击加速到难以观看。检查裁切边缘，避免过度放大栅格图。

## 合成与验证

```sh
"$TASK_MEDIA_DIR/.venv/bin/python" "$SKILL_DIR/scripts/compose.py" \
  --plan "$TASK_MEDIA_DIR/plan.json" \
  --edit "$TASK_MEDIA_DIR/edit.json" \
  --audio-manifest "$TASK_MEDIA_DIR/audio/manifest.json" \
  --output "$TASK_MEDIA_DIR/product-demo.mp4"

"$TASK_MEDIA_DIR/.venv/bin/python" "$SKILL_DIR/scripts/verify.py" \
  --manifest "$TASK_MEDIA_DIR/product-demo.manifest.json" \
  --extract-frames "$TASK_MEDIA_DIR/review-frames" \
  --report "$TASK_MEDIA_DIR/media-checks.json"
```

可用 `--font` 显式传字体。修订版换新文件名，或先归档旧产物再有意 `--overwrite`；保留原始捕获。

合成输出 MP4、SRT、章节元数据／清单和来源清单。默认旁白偏移 +0.45 秒，进行响度归一化并设独立字幕带。清单记录真实时长、裁切、crop／speed／hold、输入哈希及声音。缓存复用应基于相关实际输入，不能在脚本、声音或剪辑变化后静默复用旧输出。

机械验证检查当前文件与哈希、解码、流、章节和 SRT。单独查看抽帧与关键转场；自动报告不能证明内容真实、美观、匿名或听感良好。

## 交付

链接／展示已检查 MP4，提供 SRT 和按最终章节时间编排的干净脚本，独立保留剪辑表与原始材料。面向公众的稿件只含旁白与必要数据标签，不含内部路径、实现日志或测试摘要。重建失败后不能将上次成功草稿当成最终版。
