# Resource routing on demand

English | [简体中文](resources.zh-CN.md)

This index is based on public research dated 2026-11-02. Read the actual entry point and verify current status before use. Frameworks, commands, and default branches below are historical observations rather than permanent interfaces. The index selects resources that affect tool choice instead of reproducing all 69 historical repository records.

## Obtain and reuse

Inspect the existing project and installed skills first. Obtain remote code through available, configured GitHub connectors, Git, or public file access, keeping dependencies in the task workspace. Confirm the target branch from repository metadata; for example, `threejs-earth` and `threejs-boids` previously used defaults other than `main`.

Read the chosen resource's README, actual skill, referenced scripts, build/render entry points, and license. Normally adapt parameters through the existing interface rather than running an entire ecosystem installer for one effect. Preserve modified checkouts rather than automatically resetting or pulling over changes. Record the actual commit used.

An uninstalled upstream skill can supply task-local instructions only if its invoked files are obtained too. If dependencies are unavailable, implement the necessary equivalent in the existing project or report a concrete blocker. Do not claim an invocation succeeded when it did not. Keep global skills unchanged unless long-term installation is requested.

## Content and base pipelines

| Resource | When useful | Implementation and boundaries |
| --- | --- | --- |
| [create-vibe-motion](https://github.com/vibe-motion/create-vibe-motion) | A new 2D code-animation project is needed and the current framework is insufficient | Remotion 2D scaffold with creative/runtime separation. Read the current README and template plugin interface before generating scenes. Not an automatic script-writing service. |
| [create-vibe-motion-3d](https://github.com/vibe-motion/create-vibe-motion-3d) | Spatial relationships, 3D models, or camera movement add value | Three.js + Puppeteer. The documented template exposes readiness, dimensions, frame count, and `setFrame` through `window.__SCENE_3D_EXPORT__`. Do not assume Remotion. |
| [auto-motion/PROMPT.md](https://github.com/vibe-motion/auto-motion/blob/main/PROMPT.md) | A complete SRT needs semantic multi-shot visuals and execution prerequisites are met | SRT → grouping by topic/causality/visual concept → separate directories → serial Claude Code → HyperFrames silent MP4 → FFmpeg assembly. First read the [execution script](https://github.com/vibe-motion/auto-motion/blob/main/exampleFolder/run-claude-ai.sh). Requires Claude CLI, not automatically available in Codex. Narration, mixing, research, and script writing are separate. |
| [remotion-code-motion-explainer](https://github.com/vibe-motion/remotion-code-motion-explainer) / [skill](https://github.com/vibe-motion/remotion-code-motion-explainer/blob/main/SKILL.md) | Explanatory shots need continuous objects and causal changes | By Bingo/DWCD-Bingo. Provides directing, shot design, and QA, rather than a method solely originated by 浙大猫学长. Load relevant sections only. |
| [remotion-starter](https://github.com/vibe-motion/remotion-starter) | A new project genuinely needs a production workspace and shared shot system | By 陈与小金. Kit/template and produce, overlay, and evolve workflows; not the author's complete private pipeline. Existing projects need not migrate just to use the method. |
| [mg-style-prompt-atlas](https://github.com/sxhzju/mg-style-prompt-atlas) | Seeking motion-graphics visual directions and reference dimensions | 15 style-reference/prompt categories. Reference images come from other works, not 15 wholly original visual systems by the repository owner. |
| [MotionFace](https://motionface.cc/) | Required visit before new creative work/major redesign; also a source of clips, code, and references | Follow [website study](website-study.md). Community source: check each author, GitHub link, and asset license. A maintenance homepage on 2026-11-03 does not establish future unavailability. Recheck for each new project. Browsing does not authorize payment, commissioning, or publication. |

## Specific visual effects

Collection: [vibe-motion/skills](https://github.com/vibe-motion/skills). At the snapshot it contained 16 entries and its README announced it was no longer maintained, directing users to MotionFace. Check whether the desired effect still has a usable project. Collection maintenance status does not describe the entire organization.

| Need | Candidate skill/project | What to inspect |
| --- | --- | --- |
| One or a few procedural fish/koi | [procedural-fish-render](https://github.com/vibe-motion/skills/blob/main/procedural-fish-render/SKILL.md) / [procedural-fish](https://github.com/vibe-motion/procedural-fish) | Parameterized fish and its render entry point. Evaluate this before introducing flock simulation just to change colors, text, or paths. |
| Schooling, avoidance, or bait-ball behavior | [threejs-boids](https://github.com/vibe-motion/threejs-boids) | Verify neighborhood, separation/alignment/cohesion, and scene implementation. Use when group behavior is actually needed; visual simulation does not validate ecological claims. |
| 3D earth, routes, and flight arcs | [threejs-earth-render](https://github.com/vibe-motion/skills/blob/main/threejs-earth-render/SKILL.md) / [threejs-earth](https://github.com/vibe-motion/threejs-earth) | Obtain the render scripts, capture frames, and encode with FFmpeg. Initial loading may need CDN/texture access. Actual files determine routes, dimensions, and branches. |
| CLI typing window and motion | [claude-typer skill](https://github.com/vibe-motion/skills/blob/main/claude-typer/SKILL.md) / [claude-typer](https://github.com/vibe-motion/claude-typer) | Use shared timing/plugin interfaces and parameters rather than rewriting through additional screen recording. |
| Fisheye, moire, vignette, or push-in | [fisheye-motion skill](https://github.com/vibe-motion/skills/blob/main/fisheye-motion/SKILL.md) / [project](https://github.com/vibe-motion/fisheye-motion) | Core WebGL renderer can be separate from the scene framework. One effect layer need not force migration of the film. |
| Ruler progress, 2D WeChat UI, other motion graphics | [ruler-progress-render](https://github.com/vibe-motion/skills/blob/main/ruler-progress-render/SKILL.md), [wechat-2d-render](https://github.com/vibe-motion/skills/blob/main/wechat-2d-render/SKILL.md); search the collection for others | Verify existence and interface compatibility. Other entries include candlestick, spotlight, ticker, vinyl, and brand effects; do not load them all by default. |
| Geometric logo reconstruction or motion design | [pixel2motion](https://github.com/vibe-motion/skills/blob/main/pixel2motion/SKILL.md), [Disney principles](https://github.com/vibe-motion/skills/blob/main/disney-animation-rule-skill/SKILL.md) | Reuse decomposition, anticipation, follow-through, and easing guidance. Skip unrelated system operations. |
| Hand-drawn paper, line boil, or animation on twos | [op55-handdrawn-sketchbook](https://github.com/sxhzju/op55-handdrawn-sketchbook) | Canvas2D deterministic frames, low-frequency line boil, smooth camera, subframe motion blur, Playwright + FFmpeg. Borrow implementation only; client captions/lyrics are not the creator's own voice, and audio may not be bundled. |
| Soft-body drops, thruster landings, or control experiments | [hoverslam](https://github.com/vibe-motion/hoverslam) / [architecture](https://github.com/vibe-motion/hoverslam/blob/main/docs/ARCHITECTURE.md) | Precomputed XPBD simulation, control research, Three.js cinematic time mapping, Playwright/FFmpeg. Higher dependency/compute cost; use for real simulation needs. Validate image quality and model validity separately. |
| Chladni audio particles, line curtains, or Jianying effect recreation | [3d-chladni-render](https://github.com/vibe-motion/skills/blob/main/3d-chladni-render/SKILL.md), [printed-curtain-render](https://github.com/vibe-motion/skills/blob/main/printed-curtain-render/SKILL.md), [colorize](https://github.com/vibe-motion/colorize) | Specific third-party sources and media restrictions apply. Chladni references nolangz and Lykno media; curtains adapt Jason Labbe; colorize includes Jianying effect resources. Code licensing alone does not establish commercial rights for every asset. |

## Sound

Prefer one relevant subskill in the personal [sxhzju/sound](https://github.com/sxhzju/sound) repository:

- [sfx-sources](https://github.com/sxhzju/sound/blob/main/sfx-sources/SKILL.md): sound search/download. The snapshot covered Pixabay, Freesound, Mixkit, and Kenney. Check each asset's license; ratings and download counts are weak selection signals.
- [procedural-audio](https://github.com/sxhzju/sound/blob/main/procedural-audio/SKILL.md): offline Python synthesis; Surge XT/sfizz are optional routes. Install heavy dependencies only when needed.
- [audio-mixing](https://github.com/sxhzju/sound/blob/main/audio-mixing/SKILL.md): FFmpeg gain, panning, EQ, ducking, mixing, and loudness. Inspect the resulting file and listen after mixing.

The organization repository [vibe-motion/sound](https://github.com/vibe-motion/sound) publicly implemented only Freesound at the snapshot. Keep its scope distinct from the personal repository and inspect current files before use.

## Minimum source record

For external code/assets actually used, record the URL, author/upstream, commit or asset version, applicable code/media licenses, modifications, and used scope in existing project notes or a small sources file. Keep client lyrics and third-party assets out of new reusable skill packages.
