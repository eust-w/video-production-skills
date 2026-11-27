# Rendering and QA

English | [简体中文](rendering-and-qa.zh-CN.md)

## Template layout (`assets/template/`)

| File | Role |
| --- | --- |
| `storyboard.json` | All content and timing: brand, theme, hook, steps, captions, shots, lockup. Copy it from `storyboard.example.json` |
| `public/main.js` | three.js scene and 2D overlay; exposes `window.renderFrame(t)` and `window.ready` |
| `public/index.html` | Import map that loads `three` from `node_modules` |
| `render.mjs` | Local static server + Playwright + FFmpeg pipe: `--stills` or `--video`, `--lang`, `--storyboard`, `--browser` |
| `gen-audio.mjs` | Storyboard-driven synthesized soundtrack, written to `music.wav` |
| `sample/` | A fictional UI and `make-sample-shots.mjs`, so the template renders before real footage exists |

Requirements: Node.js 18+, `npm install` (three, playwright), FFmpeg on `PATH`, and Google Chrome or `npx playwright install chromium`. Fonts: PingFang or Noto CJK for Chinese, Avenir or Inter for Latin; the stacks fall back automatically.

## Shot fields

- `img`: path relative to the project root, or a prefix with `seq: N` (+ optional `ext`) for `img0.png … imgN-1.png`, played across the shot. Use sequences for real progress, such as a stage bar advancing.
- `frame`: the rect the camera frames; `frame2` + `pan: [t0, t1]` glide to a second rect inside the same shot (for example from a review comment to the Approve button).
- `spot`: the highlighted rect (everything else is dimmed), with `call` as the chip text. `checks: {x, ys, start, gap}` animates ticks on a checklist.
- All rects are in screenshot pixels (`screen.width × screen.height`; every image in a project must share that size).

Frame tightly: a 700–900 px wide `frame` gives about a 2.5× zoom, which makes 14 px UI text readable. A wide frame is a common mistake.

## Determinism

- Never use `Math.random()` or wall-clock time in `update`/`composite`; use the seeded `rng()` and `t`. Canvas textures redraw only when a state key changes.
- The renderer warms up a frame before each still. Video frames are rendered in order, so texture uploads are already warm.
- To preview live, open `public/index.html?play&lang=en` through any static server rooted at the project.

## Known pitfalls (all hit in practice)

- **Canvas state leaks** between redraws (for example `textAlign` left as `center` shifts the next draw). The template calls `ctx.reset()` in `upd()`; keep it.
- **Light UI blooms** if it exceeds the bloom threshold. Screens use color `0xeeeeee` with threshold 0.9; only HDR accents (`color × k > 1`) glow.
- **White UI between shots** looks harsh in a dark style; the template dims the screen until the spotlight appears.
- **Callouts colliding** with the header or captions: chips flip above or below the spot and are clamped between y = 165 and H − 220.
- **Long captions** overflow; the template shrinks them to 86 % of the width, but rewrite rather than rely on it.
- **`server.listen()` is asynchronous**: await it before reading the port (fixed in `render.mjs`).
- **FFmpeg without `drawtext`** (common in Homebrew builds): contact sheets use only `scale` and `tile`; identify tiles by index (`t = step × k`).
- **Glob order of stills**: names are zero-padded (`t012.60.jpg`) so `-pattern_type glob` sorts by time.
- **Headless WebGL speed**: use installed Chrome (`channel: 'chrome'`, ANGLE/Metal on macOS); a 30 s 1080p cut renders in about 35–45 s there. The bundled Chromium falls back to SwiftShader and is much slower.

## QA checklist before delivery

1. Stills at every beat (start, middle, and end of each shot) for each language, tiled into a sheet. Check readability, overlaps, the header and stepper, and caption collisions.
2. Full render: `scripts/contact_sheet.sh out.mp4`. Check the duration equals the storyboard and loudness is about −14 to −13 LUFS; adjust `norm` in `gen-audio.mjs` if needed.
3. Look at transition frames (the 0.5 s after each cut) for empty or blown-out frames.
4. Confirm secrets are blurred in the final frames, not just the source stills.
5. In the report, say whether you watched and listened to the full cut. If you only inspected stills, say so.
