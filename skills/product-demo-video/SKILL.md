---
name: product-demo-video
description: Create or revise product introduction and software demonstration videos from actual application recordings, with natural Chinese narration, synchronized captions, editing, and delivery checks. Use for product demos, narrated walkthroughs, screen recordings, or reworking an existing demo's script or voice. Not for standalone slides, fictional generated video, or general application implementation.
---

# Product demo video

Turn a working product into a user-facing walkthrough: a recognizable problem, a clear action, the visible result, and the next useful step. Deliver a playable video, synchronized SRT, and a clean narration script.

## Defaults and scope

- Use the **bundled default natural female voice** from [assets/voice-profile.json](assets/voice-profile.json): `zh-CN-XiaoxiaoNeural`, normal rate/pitch/volume. The bundled default is configurable; respect the user’s selected language and speaker. An explicit user change overrides this default; if that voice is unavailable, explain the concrete failure rather than substituting macOS `say` or another speaker.
- Default to Chinese product narration. Introduce user problems, benefits, and operation flows. Keep development status, branches, test counts, and implementation reports in separate evidence unless the user asks for that kind of presentation. A product that edits code should still demonstrate its code-related features.
- Choose length and chapter count from the requested scope; the previous project's duration and chapter count are not requirements. Reuse the **method and voice**, not its product name, brand, selectors, resource identifiers, or claims.
- Save recordings, audio, temporary scripts, and final exports in a task-specific artifact directory outside the source repository unless the user requests committed media. Preserve prior delivered versions.

## Working sequence

### 1. Establish what can be shown

Read the product's relevant docs, current UI, and existing artifacts. If testing or local startup is requested, complete the relevant checks separately from the film's story. Use existing authorized services and preserve unrelated processes and data.

Classify proposed demonstrations as actual operation, explicitly simulated data, or unavailable. Tie each scene to an observable result. A simulated adapter or prepared dataset remains visibly labelled **演示数据**; describe a missing integration as a product setup requirement instead of implying success. Recording does not authorize production changes, paid subscriptions, external publication, or real notifications to other people.

**Done:** every proposed capability has a recording source or an explicit boundary; no unsupported promise is in the outline.

### 2. Write the product story

Structure the walkthrough around a user's task, not a tour of internal modules. Use natural questions a user would type, concise spoken sentences, and realistic transitions. Let the narration explain why a visible action matters. Demonstrate uncertainty honestly: evidence, hypotheses, and next steps should remain distinguishable.

Use product-specific branding for a brief opener, optional transitions, and the ending. If a lightweight title card is useful, customize [assets/title-card.html](assets/title-card.html) with that product’s name, copy, and accent color. Prefer actual UI for the main film. Read [references/story-and-review.md](references/story-and-review.md) when planning or revising scripts and deciding which scenes to keep.

Freeze each chapter's `narration` before synthesis. The displayed subtitle is authoritative; an explicit pronunciation map may spell out a product acronym for speech without changing its meaning. Use [assets/plan.example.json](assets/plan.example.json) and [references/media-contracts.md](references/media-contracts.md).

**Done:** the script reads like a product introduction, accurately matches the intended visuals, and can be synthesized without unresolved wording.

### 3. Record actual operations

Prefer available browser/recording integrations that support the required capture. Follow their tool/skill rules. If they are unavailable or cannot record, use regular Playwright and record the reason. Discover installed runtime/browser paths rather than copying paths from a previous computer.

For Playwright, adapt [assets/scenario.example.cjs](assets/scenario.example.cjs) and use `scripts/record.cjs`. Write product-specific selectors only after observing the actual UI. Keep the viewport and screen dimensions aligned; inspect full-screen capture instead of assuming a successful click produced usable footage.

Before recording, prepare a clean authorized demonstration context. Natural product questions and named example conversations usually produce a clearer film than verbose test instructions. Exercise destructive UI features only on disposable records created for this demonstration. Actual external sends need the user's authorization; use labelled simulated delivery otherwise.

Record action and result markers, relevant page errors, and screenshots. Close the recording page/context before treating the video file as complete. Keep failed takes and explicitly select the intended final take. A deliberately shown error must remain labelled as that outcome, not as a successful capability. See [references/recording.md](references/recording.md) for state, streaming, print/export, and timing pitfalls observed in real use.

**Done:** each selected take shows the real operation and its outcome, and the source video is finalized and inspectable.

### 4. Synthesize the selected voice and captions

Use `scripts/narrate.py` with an explicit plan and output directory. Validation is offline by default; `--generate` performs online synthesis. Consult the CLI help and [references/media-contracts.md](references/media-contracts.md) for setup and schemas.

Send only the reviewed narration, never tokens, private configuration, customer records, or raw investigation data. Preserve service sentence/word boundaries. Do not divide audio duration evenly to invent subtitle timing. Small service-boundary overlaps or omitted quote punctuation may be reconciled only while retaining the original metadata and complete text coverage.

A changed script requires regeneration of the affected audio and captions. Check actual decoding and content coverage. Audition a short passage if voice settings or language change, or if the user requests an audition; the established default itself does not need reconfirmation.

**Done:** every selected chapter has the intended voice, complete narration, real timing metadata, and matching text/audio hashes.

### 5. Edit and assemble

Create an explicit edit decision list from the source recordings. Remove dead waiting, keep the visible result long enough to understand, and align actions with the relevant explanation. Use actual media durations and reviewed trim points, not planning estimates or page-creation wall times.

Use `scripts/compose.py` for MP4/SRT/chapters and provenance. Place captions in a separate band so they do not hide controls. Caption size and brand colors should suit the product. Give dialog text and graphs readable time; disclose material speed changes. A short held result frame is acceptable, but long freezes usually call for a tighter script or better recording.

Cropping can focus attention on a result or omit unrelated material. Keep evidence and uncertainty intact. Inspect report bodies, exported documents, and post-delete fallback screens too: unwanted development prose can survive there even after the narration is rewritten. Do not fabricate UI responses or success screens to repair missing footage.

**Done:** one selected version contains the correct takes, current voice and captions, appropriate data labels, and a product-focused opening and ending.

### 6. Verify and deliver

Run `scripts/verify.py` for decoding, stream/chapters/SRT consistency, hashes, and representative frames. Then inspect the frames and key interactions: text and diagrams, full screen, exports, confirmation dialogs, transitions, result frames, and any changed scene. Technical decoding is not visual or voice-quality approval.

If a scene changes, update its edit/audio as appropriate, rebuild, and bind the final checks to the new file/hash. Recheck affected visuals and the resulting file; do not repeatedly rerun unrelated application suites.

Deliver the final MP4 prominently, plus SRT and a narration script with actual chapter times. Keep detailed test/provenance material separate from the user-facing film. State any material remaining limitation concisely. In Codex, use an absolute local Markdown media path to display the video.

**Done:** the delivered filename is the checked final version, opens correctly, and has no unacknowledged missing scene, mismatched audio, or unsupported success claim.

## Reusable helpers

- `scripts/narrate.py`: selected neural voice, service-timed captions, text parity and synthesis manifest.
- `scripts/record.cjs`: browser recording wrapper; scenario supplies the actual product interactions.
- `scripts/compose.py`: edit-list assembly, caption band, audio normalization, chapter metadata and provenance.
- `scripts/verify.py`: media integrity and timestamp checks; human/agent visual review still follows.
- [references/media-contracts.md](references/media-contracts.md): dependencies, commands, schemas, and small end-to-end example.
