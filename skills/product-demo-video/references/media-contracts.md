# Media contracts and commands

All paths below are task-specific. Keep the installed skill source and templates unchanged during use; copy templates to an artifact directory and pass explicit inputs. Helpers use explicit input paths and have no project-specific directory dependency.

## Dependencies

Python 3.10+, Node.js, FFmpeg/FFprobe, and a usable browser are needed for the complete pipeline. Python dependencies are in `assets/requirements.txt`. Use an existing compatible environment or an isolated task environment, not global package changes.

```sh
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/product-demo-video"
TASK_MEDIA_DIR="/absolute/path/to/demo-artifacts"
python3 -m venv "$TASK_MEDIA_DIR/.venv"
"$TASK_MEDIA_DIR/.venv/bin/pip" install -r "$SKILL_DIR/assets/requirements.txt"
```

Discover Playwright/browser installations through available runtime tooling, the project's dependency resolution, or an explicitly supplied module/executable. For Codex desktop, `load_workspace_dependencies` can locate bundled Node packages. Record those discovered paths in task-local commands, not in the skill. FFmpeg builds without `libass` are supported: the compositor renders captions as PNG overlays.

A Chinese-capable font is required for Chinese narration captions. Pass a font explicitly when automatic platform discovery cannot find one; a missing glyph/font should fail clearly instead of producing squares. Use the helpers' `--help` for current options.

## Plan

Copy `assets/plan.example.json`. Keep chapter IDs unique and safe as filenames. Order in `chapters` is film order. The product name and duration are examples, not requirements.

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

`video.height` is the footage height; the final height is `height + caption_band`. For a 1920×1080 deliverable with a 120-pixel caption band, use width 1920 and footage height 960.

`narration` is the exact displayed text. `pronunciations` changes only how specified terms are spoken. Declare acronym pronunciations explicitly. If `pronunciation_script`/`voice_text` is present, it must agree with those declared substitutions rather than silently changing the narration.

## Narration and captions

The default speaker and settings come from `assets/voice-profile.json`. The provider is online; only reviewed narration is sent. The bundled client is a third-party Edge neural-speech client, not a guarantee of service availability. A catalog failure or missing selected voice is an explicit error, not a reason to switch to system speech.

```sh
"$TASK_MEDIA_DIR/.venv/bin/python" "$SKILL_DIR/scripts/narrate.py" \
  --plan "$TASK_MEDIA_DIR/plan.json" --output "$TASK_MEDIA_DIR/audio"

"$TASK_MEDIA_DIR/.venv/bin/python" "$SKILL_DIR/scripts/narrate.py" \
  --plan "$TASK_MEDIA_DIR/plan.json" --output "$TASK_MEDIA_DIR/audio" --generate
```

The first command validates offline; the second synthesizes. Use a new output directory for a new voice/version. For unchanged chapters, `--generate --resume` reuses only current, hash-verified audio and can run offline when all chapters are reusable. After editing a chapter, use `--generate --resume --overwrite` to regenerate the changed material and keep other valid chapters. `--chapters` may select a subset, but the manifest still describes the complete plan: missing or stale chapters prevent a complete status. For a transient connection failure, retain the selected voice and valid chunks, then retry with `--resume` after connectivity recovers; keep TLS verification enabled. Do not hand-edit hashes or claim a partial manifest is a complete film.

The audio manifest has `status`, `plan_sha256`, voice settings, and `chapters`. Each chapter records `id`, `display_text`, `speech_text`, `wav_file`, actual duration, hashes, raw service boundaries, and captions:

```json
{"start_seconds":0.1,"end_seconds":2.8,"text":"这里用演示数据说明操作。"}
```

Caption timestamps are relative to that audio file's start. The compositor adds the actual chapter and narration placement offsets. Keep the raw boundary metadata when reconciling short overlaps or quote glyph omissions. Changed wording needs changed audio.

## Browser recording

Adapt the trusted task-local copy of `assets/scenario.example.cjs` after inspecting the target UI. It exports one async function receiving the page, context, browser, base URL, output directory and a marker function. The wrapper owns capture and cleanup; the scenario owns only the product actions authorized for the task.

```sh
node "$SKILL_DIR/scripts/record.cjs" --help
node "$SKILL_DIR/scripts/record.cjs" \
  --scenario "$TASK_MEDIA_DIR/scenario.cjs" \
  --output "$TASK_MEDIA_DIR/recordings/inspect" \
  --url "http://127.0.0.1:PORT/" \
  --playwright-module "/discovered/playwright/module" \
  --executable "/discovered/browser/executable"
```

Replace `PORT` and discovered paths with observed values. A fresh capture context is not a substitute for app authorization. Do not package cookies, keys or environment-specific credentials in the skill.

## Edit decisions

Copy `assets/edit.example.json`. The top-level object maps chapter IDs to edit decisions. Each source path is relative to the edit JSON directory; trims are seconds measured within the source file, not wall-clock timestamps. Sources can be reused honestly across chapters.

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

A `crop` is `[x,y,width,height]` in source pixels. An optional `speed` changes playback of that actual segment; keep the change visible to the viewer when material. `fit_to_voice` permits limited whole-chapter acceleration. Prefer explicit trims of idle periods over racing through clicks. Inspect crop edges and avoid oversized raster close-ups.

## Compose and verify

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

An explicit font may be supplied with `--font`. Choose a new output filename for a revision, or archive the prior deliverable before intentional `--overwrite`. The original captures remain unchanged.

Composition emits MP4, SRT, chapter metadata/list and a source manifest. Default audio placement is +0.45 seconds, with normalized narration and a separate caption band. The manifest records actual duration, trims, crop/speed/holds, input hashes and the chosen voice. Cache reuse depends on the actual relevant inputs; a changed script/audio/edit must not silently reuse stale output.

Mechanical verification checks the current output and its hashes, decoding, streams, chapters and SRT. Review the extracted frames and important transitions separately; an automatic report cannot establish that a scene is truthful, attractive, anonymous, or pleasant to listen to.

## Delivery

Link/display the checked MP4, provide its SRT and a clean script using final chapter times, and retain the selected edit list and raw material separately. The public-facing script should contain the narration and necessary data labels, not internal source paths, implementation logs or test summaries. Avoid presenting the last successful draft as the final result after a failed rebuild.
