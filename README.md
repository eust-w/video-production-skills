# Video Production Skills

English | [简体中文](README.zh-CN.md)

Two independently installable Agent Skills for real product demonstrations and code-driven explainer videos. Each skill includes a `SKILL.md` entry point and its supporting resources. The installation examples below target Codex; other assistants must support this skill format and provide compatible tools.

| Skill | Use it for | Included resources |
| --- | --- | --- |
| [product-demo-video](skills/product-demo-video/SKILL.md) | Product introductions, recorded walkthroughs, narration, and synchronized captions | Playwright recording, Edge TTS narration, FFmpeg composition, SRT export, media verification, tests, and templates |
| [vibe-motion-meta](skills/vibe-motion-meta/SKILL.md) | Technical explainers, motion graphics, and B-roll | Creative workflow, MotionFace reference study, tool routing, production guidance, and a delivery audit helper |

## Installation

### From source

Clone the repository and copy the **entire directory** of each skill you want to install. Back up an existing skill with the same name before copying so you preserve any customizations.

The following commands use a POSIX shell, such as Bash or Zsh:

```sh
git clone https://github.com/eust-w/video-production-skills.git
cd video-production-skills
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skills/product-demo-video "${CODEX_HOME:-$HOME/.codex}/skills/"
cp -R skills/vibe-motion-meta "${CODEX_HOME:-$HOME/.codex}/skills/"
```

Restart or refresh your assistant's skill discovery, then invoke a skill by name. Install either skill independently; neither requires the other. Installation copies the instructions and helpers, but does not install runtime dependencies.

### From a release ZIP

Download either package from [Releases](https://github.com/eust-w/video-production-skills/releases), extract it, and place its top-level `product-demo-video` or `vibe-motion-meta` directory in your assistant's skills directory. Keep the scripts, references, assets, and metadata together. Release assets include `SHA256SUMS` for archive verification.

For other assistants, consult their documentation for the installation directory and invocation syntax. Compatibility with every assistant has not been tested.

## Dependencies

### Product demo pipeline

| Dependency | Purpose |
| --- | --- |
| Python 3.10+ | Narration, composition, and verification helpers |
| Python packages in `assets/requirements.txt` | `edge-tts`, Pillow, and fonttools |
| Node.js | Playwright recording helper; choose a version compatible with your installed Playwright |
| Playwright and a browser | Recording real application interactions |
| FFmpeg and FFprobe, available on `PATH` | Encoding, audio processing, probing, and media checks |
| Fonts covering the caption language | Readable captions; Chinese captions require Chinese glyph coverage |
| Network access for online TTS | Synthesizing narration through the configured speech service |

From the repository root, create an isolated environment for the Python helpers and install Playwright locally:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r skills/product-demo-video/assets/requirements.txt
npm install playwright
npx playwright install chromium
ffmpeg -version
ffprobe -version
```

Install FFmpeg/FFprobe separately using your operating system's package manager. Linux browser environments may also require system libraries for Playwright. On Windows, adapt the shell commands and use `.venv\Scripts\python.exe` for the virtual environment.

The recording helper accepts explicit Playwright module and browser executable paths when automatic discovery is insufficient. Run each helper with `--help` for its options. See [Media contracts and commands](skills/product-demo-video/references/media-contracts.md) for plan schemas, recording, synthesis, composition, and verification commands.

The bundled voice is Mandarin Chinese `zh-CN-XiaoxiaoNeural`. Voice settings are configurable; explicitly request a different language and matching voice when needed. Online synthesis uses the third-party `edge-tts` client to access Microsoft's speech service, requires connectivity, and has no availability guarantee. Review the service terms and send only reviewed narration text. Offline plan validation and local media editing do not require online synthesis.

### Motion workflow

`vibe-motion-meta` provides creative guidance and tool routing rather than a standalone rendering engine. Dependencies depend on the chosen project and renderer. It does not bundle upstream projects or media; inspect their dependencies and licenses before use.

For new videos or substantial visual redesigns, the skill requires an actual attempt to browse MotionFace and study playable references. If access is unavailable, record the limitation and continue with accessible sources. Its delivery audit helper uses Python's standard library.

Both skills load English `SKILL.md` instructions and English reference documents by default. Each document links to its complete Simplified Chinese counterpart (`*.zh-CN.md`), whose internal references stay in Chinese. UI metadata is also English by default; `agents/openai.zh-CN.yaml` preserves the Chinese version for optional manual replacement of `agents/openai.yaml`. Documentation language does not change the bundled Mandarin voice or the language of existing sample assets. Request your preferred narration language and voice explicitly.

## Usage examples

Invoke these prompts in your assistant after installing the relevant skill. Provide the application location or source material needed for the task.

### Record a product demonstration

```text
Use $product-demo-video to make a two-minute introduction to my application
at http://localhost:3000. Show real interactions and their visible results.
Use Mandarin Chinese narration with the bundled default voice.
Deliver an MP4, synchronized SRT captions, and a narration script.
```

### Request English narration

```text
Use $product-demo-video to create an English onboarding walkthrough for
this project. Select an available English neural voice and keep captions
consistent with the narration. Clearly label any simulated data.
Deliver the final video, SRT, and script.
```

### Create a technical explainer

```text
Use $vibe-motion-meta to turn the attached technical script into a
90-second explainer in English. Show how tasks move through a scheduler
using continuous objects and readable labels. Deliver a playable video,
editable source, and instructions for rendering it again.
```

### Validate a narration plan offline

From the repository root, copy the example plan to a task directory and edit its product name, chapters, and narration:

```sh
mkdir -p ../demo-artifacts
cp skills/product-demo-video/assets/plan.example.json ../demo-artifacts/plan.json
.venv/bin/python skills/product-demo-video/scripts/narrate.py \
  --plan ../demo-artifacts/plan.json \
  --output ../demo-artifacts/audio
```

This validates the plan without contacting the speech service. Add `--generate` only when you intend to synthesize the reviewed narration online. Use a new output directory for a new version, and consult the [media workflow reference](skills/product-demo-video/references/media-contracts.md) for resume behavior and the remaining pipeline.

Recordings and generated media belong in a task-specific output directory. These skills do not grant authorization to change production systems, publish externally, or send real notifications.

## Validation

With the dependencies installed, run these checks from the repository root:

```sh
.venv/bin/python -m unittest discover -s skills/product-demo-video/scripts -p 'test_*.py'
node --check skills/product-demo-video/scripts/record.cjs
python3 skills/vibe-motion-meta/scripts/audit_delivery.py --help
```

The composition regression tests use locally generated video and tones; they do not contact a real product or online speech service. Automated checks do not replace reviewing the actual video, captions, narration, and transitions.

## Attribution and license

Original instructions, scripts, and templates in this repository are available under the [MIT License](LICENSE). This public edition was adapted from local workflows, with private paths and project-specific preferences removed while retaining reusable defaults and source attribution.

`vibe-motion-meta` is an independent research-based workflow. It is not an official release or endorsement by 浙大猫学长, MotionFace, or Vibe Motion. See the [source evidence](skills/vibe-motion-meta/references/evidence.md) and [resource index](skills/vibe-motion-meta/references/resources.md) for attribution and scope. Historical website and interface observations do not guarantee current availability.

Linked code, fonts, audio, media, and services retain their own licenses and terms. This repository's MIT License does not grant redistribution or commercial-use rights to those external resources.
