# Code animation production and revision lessons

English | [简体中文](production-lessons.zh-CN.md)

This is an engineering retrospective from producing and revising a product explainer. It is not a quotation from 浙大猫学长, an analysis of website source code, or a universal aesthetic rule. Record actual website observations separately with work URLs. Apply these choices to the current subject; bullet time, fisheye, particular characters, palettes, and fixed durations are not defaults.

## Make visuals explain the process

When a scene seems to need more elements, first check whether viewers can see the process. Prefer objects with roles: inputs, tasks, queries, evidence, results, and notifications. Let them change state. Add terminal snippets, trends, or topology only when they clarify the mechanism rather than competing for attention.

Give each key action one main subject. Activate queries in sequence, emphasize the object being processed, and move completed objects into the background. Enter an emphasis shot after evidence appears. Use short labels, states, and actions; avoid permanent explanatory paragraphs when the change already communicates the point.

Continuous transitions preserve object identity: a submitted input becomes a task label, a query line becomes a report divider, an evidence ticket expands into a notification card, or a ring becomes an ending motif. Share position, dimensions, curves, and timing across the handoff rather than independently fading two similar objects without connecting them.

## Common failures and engineering choices

| Symptom | Inspection and treatment |
| --- | --- |
| Jittery text or soft edges when enlarging screenshots | For editable interfaces, prefer native vectors/scene objects and redraw at final resolution. Inspect low-resolution scaling, pixel rounding, resampling, and frame rate before considering stylistic motion; random jitter cannot repair the issue. |
| Strong middle effects but slideshow-like opening/ending | Design restrained pushes, pans, and handoffs with common anchors across sections. Let content determine movement and amplitude; avoid continuously floating every object. |
| Every small panel competes for attention | Separate hierarchy and stagger activation. Keep the main card background opaque while reducing secondary text/lines. Lowering whole-card opacity lets underlying lines show through text. |
| Overlapping text during title changes or report expansion | Clear old text before showing new text; backgrounds and connectors may morph earlier. Sample several frames around the boundary, not just stable endpoints. |
| Complete source strings but missing glyphs in the film | Inspect actual fonts, glyph coverage, clipping, and fallbacks. Read the rendered frame character by character. Source strings, width measurement, and compilation cannot prove glyph completeness. |
| Seams or bright lines in a fisheye mesh | Inspect tile-edge coverage and antialiasing. Use suitable edge expansion or overlap for the renderer and confirm the seam disappears in motion rather than hiding it with stronger distortion. |

## Slow motion, orbiting, and readable text

Bullet time should pause an event worth watching: evidence arrival, structural expansion, or a revealed relationship. Show the event, slow down and orbit, then send the same object into the next scene after resuming. Freezing ordinary cards alone rarely creates a climax.

Separate output and world clocks: `t_world = f(t_output)`. Objects, particles, scan lines, and state share world time; cameras may continue along output time. Use continuous speed changes when slowing and resuming. Preview and export must share the mapping to avoid jumps around the effect.

For perspective and fisheye, consider rendering card geometry first, then drawing text at final resolution using projected anchors, avoiding repeated texture/camera resampling of glyphs. Text must follow its card. Check occlusion, edge exits, and compression throughout the orbit; limit horizontal compression or adjust layout when needed. Higher bitrate alone does not establish readability.

## Sound and evidence boundaries

Sound follows final output time. After extending a freeze or moving an evidence reveal or notification expansion, retime its sound. Lower ambience during pauses; a clean landing on resumption can reinforce speed changes. Sound important actions when useful. Peak, clipping, and loudness checks support, rather than replace, listening and synchronization review.

Demo trends, logs, and traces must not appear to be measurements. An observed increase in stage duration does not establish a specific configuration fault. Reports and notifications should distinguish observations, items to verify, and recommendations. Avoid fictional performance numbers for drama.

## Revision and delivery

Centralize brand, character, channel, and ending copy. Apply the requested rename scope to relevant headers, placeholders, requests, plan items, notifications, loop labels, ending, and transition targets. An ending-only change does not authorize changing every scene. Remeasure widths and centering when name length changes rather than relying on global text replacement.

For branding removal, external sharing, or packaging, inspect filenames, source, images, documents, prompts, paths, media metadata, and archive contents in the delivery scope. Prompts may retain old project names. Keep originals outside the deliverable workspace; label public prompts edited when identifiers were removed, rather than presenting them as verbatim originals. Preserve third-party licenses and AI content credentials.

Inspect the actual encoded film, especially text/action boundaries, intermediate emphasis poses, notification expansion, and ending. Check duration, dimensions, frame rate, audio, and decoding according to the change's risk. Deliver a playable file, editable source, needed assets, and run instructions. Source fixes without re-exporting, or archives containing stale files, are incomplete delivery.
