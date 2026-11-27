# Story and style

English | [简体中文](story-and-style.zh-CN.md)

## Two proven structures (30 s)

**A. Real path (recommended default).** Credibility comes from the real product.

| Time | Beat | On screen |
| --- | --- | --- |
| 0–3 s | Problem hook | The pain in one image, e.g. an AI agent claiming "Done, all tests passed", stamped UNVERIFIED |
| 3–10 s | ① Input | The real input screen, zoomed: the one-sentence idea, then AI-structured acceptance criteria ticking in |
| 10–19 s | ② Execution and control | Stages advancing (an image sequence), test evidence (exit code), a human approval gate |
| 19–25 s | ③ Result | Deployed and healthy, rollback available, the traceable release record |
| 25–30 s | Lockup | Logo, product, tagline, "A <company> product" |

A persistent three-step rail (top right) shows where the viewer is. Every product shot gets one spotlight and one callout chip.

**B. Concept explainer.** Use it when there is no presentable UI yet: problem → product in one line → two technical pillars visualized (for example executor/verifier split, signed pull-based delivery across a firewall) → proof cards (numbers) → lockup. Build these as card and diagram scenes in three.js. It is clearer about architecture but less convincing than A; offer A once real footage exists.

## Writing for users and investors

- Lead with the problem in plain words ("AI writes code fast, but nobody dares to ship it blind"), then the one-sentence product promise.
- Technical depth = **named mechanisms plus evidence**, not adjectives: "isolated pod, exit code 0", "signed release, zero inbound ports", "auto-rollback on failed health probe".
- One idea per shot and one caption per beat. If the main caption exceeds about 20 CJK characters or 55 Latin characters, cut words; the template shrinks the font to fit as a last resort.
- Callouts name what the highlighted UI proves, not what it is ("6/6 pass, exit code 0", not "Test log").

## Claims and numbers

- Every number needs a source (document, dashboard, measurement) and a visible qualifier: "measured", "trial reference", "design limit". Put a footnote on screen when values are preliminary, and ask the owner before using soft numbers in investor material.
- Do not stitch frames from different runs into a story that implies one run without saying so to the requester. Prefer frames from the same run, or crop so the difference is not misleading, and note it in the delivery report.
- Blur or crop internal hostnames, IPs, registry paths, tokens, emails, and customer names. FFmpeg: `split → crop → boxblur → overlay` on the still.

## Matching a house style from reference videos

1. Run `scripts/contact_sheet.sh ref.mp4 sheet.jpg 1 6` for the overall rhythm; extract 3–5 full-resolution frames of representative moments (header, caption, panel, data card, ending).
2. Record the system as concrete values: background (for example warm black with a red-brown radial glow), accent color, texture (for example a dot grid brighter at the edges), header layout (logo · product / numbered chapter), caption system (bold main line plus small letter-spaced uppercase English line), panel treatment (dark glass with a glowing accent edge and a bottom light streak), data-card style, and lockup (mark + name + tagline + English line).
3. Map them onto the template: `theme.accent/accent2/background/haze/dots`, `brand.logo` or `monogram`, the caption `sub` lines, and the lockup fields. Reuse their typography stack where possible.
4. Use the company's official logo asset. A redrawn mark is a placeholder and must be disclosed.

## Bilingual versions

- Write captions natively per language, not as literal translations. In CJK versions the template automatically shows the English line in small uppercase under the CJK main line (a common bilingual house style); in the English version use a short tagline in `sub.en` instead.
- Card text, stage names, and callouts all switch with `--lang`. Product screenshots keep their UI language; mention this, or record the UI in the target language.
