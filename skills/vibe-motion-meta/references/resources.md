# 按需资源路由

索引基于 2026-11-02 的公开资料。使用前读取实际入口并核对当前状态；不要把表中的框架、命令或默认分支当永久接口。这里只精选影响选型的资源，不复制 69 条历史仓库清单。

## 获取与复用

先检查当前项目和已安装 Skill。获取远端代码时使用已配置、可用的 GitHub 连接器或 Git／公开文件入口，在任务自己的工作目录中保留依赖。目标分支先由仓库元数据确认；例如 `threejs-earth` 与 `threejs-boids` 的默认分支曾不是 `main`。

对所选资源读取 README、实际 SKILL、其相对引用脚本，以及构建／渲染入口和许可证。正常情况下按原接口改参数即可；不为使用一个效果先运行整个生态的安装脚本。已有 checkout 有修改时保留修改，不自动 reset 或用拉取覆盖。记录最终实际使用的 commit。

未安装的上游 Skill 可以作为任务局部操作说明使用，但必须同时取得它真正调用的文件。若当前环境缺少其依赖工具，优先在当前项目实现等价的必要部分，或给出具体阻断；不要伪称调用成功。用户未要求长期安装时不修改全局 Skills。

## 内容与基础管线

| 资源／入口 | 适用条件 | 关键实现与边界 |
| --- | --- | --- |
| [create-vibe-motion](https://github.com/vibe-motion/create-vibe-motion) | 需要新建二维代码动画项目且现有框架不够用 | Remotion 2D 脚手架；创作层与运行层分离。读当前 README 和模板 plugin 接口，再生成场景。不是自动写稿服务。 |
| [create-vibe-motion-3d](https://github.com/vibe-motion/create-vibe-motion-3d) | 空间关系、三维模型、相机运动确有价值 | Three.js + Puppeteer；模板通过 `window.__SCENE_3D_EXPORT__` 提供就绪、尺寸、帧数和 `setFrame` 等接口。不能假定走 Remotion。 |
| [auto-motion/PROMPT.md](https://github.com/vibe-motion/auto-motion/blob/main/PROMPT.md) | 已有完整 SRT，需要按语义生成多镜头视觉片，且实际环境满足执行依赖 | SRT → 按主题／因果／视觉概念合并 → 独立目录 → 串行 Claude Code → HyperFrames 静音 MP4 → FFmpeg 拼接。先读 [执行脚本](https://github.com/vibe-motion/auto-motion/blob/main/exampleFolder/run-claude-ai.sh)。需要 Claude CLI；不能假定当前 Codex 自动具有它。配音、混音和研究写稿不由该模板包办。 |
| [remotion-code-motion-explainer](https://github.com/vibe-motion/remotion-code-motion-explainer) / [SKILL](https://github.com/vibe-motion/remotion-code-motion-explainer/blob/main/SKILL.md) | 需要连续对象与因果变化的解释型镜头 | 作者 Bingo／DWCD-Bingo。提供解释动画导演方法、镜头和 QA；不是猫学长本人独创的方法。只加载相关部分。 |
| [remotion-starter](https://github.com/vibe-motion/remotion-starter) | 新项目确实需要制作工作台与共享镜头体系 | 作者陈与小金。kit／template 与 produce、overlay、evolve 相关流程；不包含作者完整私有生产线。已有项目不为采用方法强制迁移。 |
| [mg-style-prompt-atlas](https://github.com/sxhzju/mg-style-prompt-atlas) | 需要找 MG 的视觉方向与参考维度 | 15 类风格参考与提示词；原参考图来自其他作品，不是 15 种本人原创视觉体系。 |
| [MotionFace](https://motionface.cc/) | 新创作／重要视觉改版前必访，也可寻找片段、源码和参考 | 先执行 [网站学习要求](website-study.md)。社区来源，逐条核对作者、GitHub 链接及素材许可。2026-11-03 首页维护，不代表未来仍不可用；每个新项目核对现状。浏览页面不代表授权付费、委托或发布。 |

## 具体视觉效果

集合入口：[vibe-motion/skills](https://github.com/vibe-motion/skills)。快照时有 16 项，README 明确宣布不再维护并转向 MotionFace。优先查目标效果是否仍有可用工程；不要把旧集合停更理解成整个组织停止活动。

| 需要 | 可选 Skill／工程 | 取用重点 |
| --- | --- | --- |
| 一条或少量程序鱼、锦鲤效果 | [procedural-fish-render](https://github.com/vibe-motion/skills/blob/main/procedural-fish-render/SKILL.md) / [procedural-fish](https://github.com/vibe-motion/procedural-fish) | 参数化程序鱼及自己的渲染入口。只改颜色、文字或路径时先评估这个，不直接引入鱼群仿真。 |
| 群体游动、避障、饵球机制 | [threejs-boids](https://github.com/vibe-motion/threejs-boids) | 先确认邻域、分离／对齐／聚合与场景实现。需要的是真实群体行为才用它；不能把视觉仿真当现实生态结论的验证。 |
| 三维地球、航线、飞线 | [threejs-earth-render](https://github.com/vibe-motion/skills/blob/main/threejs-earth-render/SKILL.md) / [threejs-earth](https://github.com/vibe-motion/threejs-earth) | 读取并获取 Skill 的 render 脚本；按帧捕获后 FFmpeg 编码。首次加载可能需要 CDN 和纹理网络访问；默认路由、尺寸及分支以实际文件为准。 |
| CLI 打字窗口与相关动效 | [claude-typer Skill](https://github.com/vibe-motion/skills/blob/main/claude-typer/SKILL.md) / [claude-typer](https://github.com/vibe-motion/claude-typer) | 用共享 timing／plugin 和参数，而不是额外录屏重写。 |
| 鱼眼、摩尔纹、暗角、推镜 | [fisheye-motion Skill](https://github.com/vibe-motion/skills/blob/main/fisheye-motion/SKILL.md) / [工程](https://github.com/vibe-motion/fisheye-motion) | 核心 WebGL 渲染器可与场景框架分离；不为一层特效迁移整片。 |
| 尺子进度、二维微信界面、其他 MG | [ruler-progress-render](https://github.com/vibe-motion/skills/blob/main/ruler-progress-render/SKILL.md)、[wechat-2d-render](https://github.com/vibe-motion/skills/blob/main/wechat-2d-render/SKILL.md)；其余按集合目录检索 | 先确定目标组件存在且接口匹配。集合另含 candlestick、spotlight、ticker、vinyl、品牌等效果，不默认全部加载。 |
| Logo 几何重建、动作设计 | [pixel2motion](https://github.com/vibe-motion/skills/blob/main/pixel2motion/SKILL.md)、[Disney 原则](https://github.com/vibe-motion/skills/blob/main/disney-animation-rule-skill/SKILL.md) | 可采用部件拆分、预备／跟随／缓动等指导。不要照搬与当前任务无关的系统操作。 |
| 手绘纸张、抖线、角色一拍二 | [op55-handdrawn-sketchbook](https://github.com/sxhzju/op55-handdrawn-sketchbook) | Canvas2D 定帧绘制、低频 line-boil、平滑镜头、子帧运动模糊、Playwright + FFmpeg。只借鉴实现；客户字幕／歌词不作为作者口吻素材，音频未必随仓库提供。 |
| 软体坠落、推进器着陆、控制实验 | [hoverslam](https://github.com/vibe-motion/hoverslam) / [架构文档](https://github.com/vibe-motion/hoverslam/blob/main/docs/ARCHITECTURE.md) | 预计算 XPBD 仿真、控制研究、Three.js 电影时间映射、Playwright／FFmpeg。依赖和计算成本较重，仅实际需要物理实验时采用。画面质量与模型有效性分别验证。 |
| 克拉尼声音粒子／线帘／剪映效果重建 | [3d-chladni-render](https://github.com/vibe-motion/skills/blob/main/3d-chladni-render/SKILL.md)、[printed-curtain-render](https://github.com/vibe-motion/skills/blob/main/printed-curtain-render/SKILL.md)、[colorize](https://github.com/vibe-motion/colorize) | 有明确第三方来源及媒体限制，读具体许可证。Chladni 指向 nolangz、媒体 Lykno；线帘改编自 Jason Labbe；colorize 包含来自剪映的效果资源。不能仅凭代码许可推断所有媒体可商用。 |

## 声音

优先按具体任务读取个人仓库 [sxhzju/sound](https://github.com/sxhzju/sound) 的一个子 Skill：

- [sfx-sources](https://github.com/sxhzju/sound/blob/main/sfx-sources/SKILL.md)：音效检索与下载，快照涉及 Pixabay、Freesound、Mixkit、Kenney。检查具体素材许可证，评分和下载量只是选材弱信号。
- [procedural-audio](https://github.com/sxhzju/sound/blob/main/procedural-audio/SKILL.md)：Python 离线合成，Surge XT／sfizz 等为可选路线。只有任务需要才安装重型依赖。
- [audio-mixing](https://github.com/sxhzju/sound/blob/main/audio-mixing/SKILL.md)：FFmpeg 增益、声像、EQ、ducking、混音和响度处理。混音后重新检查文件与实际听感。

组织的 [vibe-motion/sound](https://github.com/vibe-motion/sound) 快照时公开实现仅 Freesound，不能与个人仓库的范围混写。实际使用以当前文件为准。

## 最小来源记录

只要实际使用了外部代码／素材，就在项目已有说明或小型来源文件中记录其 URL、作者／上游、commit 或素材版本、代码与媒体的适用许可、修改内容及所用范围。不要把客户歌词和第三方素材复制进新的可复用 Skill 包。
