---
name: threejs-promo-video
description: Build a short (20–60 s) product promo or investor video in three.js that walks a real product path (idea → execution → result) with spotlighted screenshots, bilingual captions, a matched house style, a synthesized soundtrack, and deterministic frame-by-frame MP4 rendering. Use for "make a 30-second promo/launch/pitch video", "match our company's promo style", "Chinese and English versions", or "show the real product flow"; not for screen-recorded walkthroughs with narration (use product-demo-video) or open-ended motion design.
---

# three.js promo video

English | [简体中文](SKILL.zh-CN.md)

Produce a clear, credible promo cut: a one-line problem, then the product doing real work in three steps, then the brand. Everything is code (three.js scene + 2D overlay), every frame is a pure function of time, and a headless browser renders frames straight into FFmpeg, so re-renders are exact and take about a minute.

## When to read references

- Planning the story, captions, claims, or matching a company's existing promo style: read [story and style](references/story-and-style.md).
- Building, rendering, or debugging the scene, and before delivery QA: read [rendering and QA](references/rendering-and-qa.md).

## Workflow

1. **Collect inputs.** Product recordings or screenshots (the more real, the better), the audience (users, investors, conference), length, languages, and any company reference videos. Ask only for what you cannot find yourself.
2. **Study the reference style** if one exists: run `scripts/contact_sheet.sh <ref.mp4>` and look at full-resolution frames of the header, captions, panels, and ending. Write down the palette, header layout, caption system, panel treatment, and lockup. Match that system rather than inventing a new look.
3. **Write the story first** (see references): problem hook → ① input → ② execution and control → ③ result → lockup. One message per shot. Every number on screen needs a source and a label such as "measured" or "trial reference".
4. **Pick real frames.** Prefer clean source recordings without burned-in subtitles. Extract stills with FFmpeg, read each one at full resolution, and note pixel rects for the camera `frame` and the `spot` highlight. Blur secrets such as internal hosts, IPs, tokens, and customer data before using a frame.
5. **Scaffold** by copying `assets/template/` into a work directory outside the user's repository, running `npm install`, and copying `storyboard.example.json` to `storyboard.json`. The template renders immediately with fictional sample shots (`npm run sample-shots`).
6. **Edit `storyboard.json`**: brand, theme colors, logo, hook, steps, captions (per language), shots (`img` or an image sequence, `frame`, optional `frame2` and `pan`, `spot`, `call`, optional `checks`), and the lockup. Change `public/main.js` only for new visual devices.
7. **Render QA stills** with `node render.mjs --stills 2,5,8,... --lang <code>`, tile them, and inspect. Fix overlaps, unreadable text, and collisions; repeat until clean.
8. **Generate audio** with `node gen-audio.mjs`. It derives its cues from the storyboard, so re-run it whenever timings change.
9. **Render each language** with `node render.mjs --video out-<lang>.mp4 --audio music.wav --lang <lang>`, then run `scripts/contact_sheet.sh` on the result to check duration, loudness (about −14 to −13 LUFS), and the frames.
10. **Report honestly**: what you inspected (stills or sheets) versus what you did not (full playback or listening), which frames come from a different run than the story implies, what you blurred, and which figures are labeled as estimates.

## Rules that matter

- Clarity over spectacle: if a shot needs a sentence of explanation, it needs a caption or a callout. Cut effects that do not carry meaning.
- Show the real product. Mark it ("Real screen recording"), and never fake UI that looks real. Re-enactments, such as an animated typing line, must use the product's actual text.
- Text must stay readable at 1080p: about 28 px minimum on screen. Zoom real UI about 2–3×; a full-width screenshot is unreadable.
- Keep the caption band (bottom about 200 px) and the header band (top about 160 px) free of content. Callout chips flip above or below the highlighted region automatically.
- Publishing and branding: use the company's official logo file when available. If you redraw a mark, say so.
- Bilingual output means each language has its own captions and callouts. The product UI language in screenshots does not change; say so if it matters.
