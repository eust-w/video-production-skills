# Video Production Skills

两个可独立安装的 Agent Skills：真实产品演示与代码驱动解释动画。面向支持 `SKILL.md` 格式的编程助手，提供 Codex 安装示例。

| Skill | 用途 | 包含内容 |
| --- | --- | --- |
| [product-demo-video](skills/product-demo-video/SKILL.md) | 产品介绍、录屏、中文旁白与同步字幕 | Playwright 录制、Edge TTS、FFmpeg 剪辑、SRT、媒体验证、测试与模板 |
| [vibe-motion-meta](skills/vibe-motion-meta/SKILL.md) | 技术解释动画、MG、B-roll | 创作流程、MotionFace 参考研究、生态路由、工程经验与交付审计 |

## 安装

克隆仓库，将所需 Skill 的**整个目录**复制到助手的技能目录。Codex 示例（已有同名目录时先备份，避免覆盖自定义内容）：

```sh
git clone https://github.com/eust-w/video-production-skills.git
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R video-production-skills/skills/product-demo-video "${CODEX_HOME:-$HOME/.codex}/skills/"
cp -R video-production-skills/skills/vibe-motion-meta "${CODEX_HOME:-$HOME/.codex}/skills/"
```

重新启动或刷新助手的 Skill 发现后调用：

```text
使用 $product-demo-video，为我的应用制作一个两分钟的中文产品演示，展示实际操作，输出 MP4、SRT 和讲稿。

使用 $vibe-motion-meta，把这份技术讲稿制作成解释动画，交付可播放成片和可编辑源码。
```

也可从 [Releases](https://github.com/eust-w/video-production-skills/releases) 下载单独的 ZIP 包，解压后将顶层 Skill 目录放入技能目录。其他助手的安装位置与工具接口以各自文档为准，未保证所有助手均已实测。

## 运行依赖

安装 Skill 本身不安装运行时。真实录屏流水线需要 Python 3.10+、Node.js、FFmpeg/FFprobe、Playwright 及可用浏览器、支持所用字幕语言的字体。使用隔离环境：

```sh
python3 -m venv .venv
.venv/bin/pip install -r skills/product-demo-video/assets/requirements.txt
npm install playwright
npx playwright install chromium
```

录制脚本支持显式指定 Playwright 模块和浏览器路径；运行各脚本的 `--help` 查看接口。计划、剪辑与完整命令见 [media-contracts.md](skills/product-demo-video/references/media-contracts.md)。

默认旁白为中文晓晓 `zh-CN-XiaoxiaoNeural`，可配置。在线语音由第三方 `edge-tts` 客户端访问 Microsoft 服务，需要网络且不保证可用性；只发送已审阅的旁白文本，使用者应核对服务条款。离线验证与媒体剪辑不需要在线合成。

`vibe-motion-meta` 是创作与工具路由 Skill，不是独立渲染引擎。它不捆绑上游项目或素材；按任务选择并检查其依赖与许可。新创作或重要视觉改版要求实际尝试浏览 MotionFace；无法访问时记录限制并使用可访问来源继续工作。

## 验证

```sh
.venv/bin/python -m unittest discover -s skills/product-demo-video/scripts -p 'test_*.py'
node --check skills/product-demo-video/scripts/record.cjs
python3 skills/vibe-motion-meta/scripts/audit_delivery.py --help
```

合成回归测试使用本地生成的图像与音调，不访问真实产品或在线语音。通过自动检查不代表已经完成画面、叙事或听感验收。

## 来源与许可

本仓库的原创说明、脚本与模板采用 [MIT License](LICENSE)。这是从本地工作流整理的公开版本：移除了私人路径与项目专属偏好，保留了可复用的默认值、来源与历史观察范围。

`vibe-motion-meta` 是独立研究整理，不是浙大猫学长、MotionFace 或 Vibe Motion 官方发布或背书。来源归属见 [evidence.md](skills/vibe-motion-meta/references/evidence.md) 和 [资源索引](skills/vibe-motion-meta/references/resources.md)。历史网站状态与接口记录不构成当前可用性保证。链接指向的代码、字体、音频、媒体及服务各自保留原有许可与条款，不因本仓库的 MIT 许可而获再分发或商业使用授权。
