---
name: vibe-motion-meta
description: Create code-driven explainer videos, motion graphics, or B-roll from slides, scripts, SRT, or technical concepts. Coordinate story, visuals, sound, and export; study playable MotionFace references before new work or major visual redesigns. Use for Vibe Motion workflows or the creative methods associated with 浙大猫学长; not routine clip assembly or repository analysis.
---

# Vibe Motion creative coordinator

English | [简体中文](SKILL.zh-CN.md)

This meta skill coordinates creative direction and production: determine what the work needs to communicate, select a few suitable downstream resources, and deliver the stage the user requested. Its guidance draws on public material associated with the creator 浙大猫学长 and Vibe Motion community projects. It is independently researched, not an official skill from the creator, and does not imply that every video follows the same process.

## When to read references

- New videos, storyboards, style design, or substantial motion redesigns: first read and perform the [website study](references/website-study.md), rather than finalizing from this entry point alone.
- Writing scripts, designing shots, or adapting slides: read [creative direction](references/creative-direction.md).
- Implementing or modifying code animation: read [production lessons](references/production-lessons.md), focusing on the issues relevant to the change.
- Selecting, obtaining, or invoking a skill, project, or sound tool: read [resource routing](references/resources.md), then inspect only relevant entries.
- Explaining provenance, attributing authorship, or evaluating historical observations: read [evidence and attribution](references/evidence.md).
- Removing branding, sharing externally, or packaging: read [delivery auditing](references/delivery-audit.md); the bundled read-only helper is optional.

## Actually visit the reference website

**Before a new video or substantial visual redesign, use an available browsing tool to actually visit [MotionFace](https://motionface.cc/).** Search snippets, repository READMEs, historical skill notes, and cover images do not replace browsing. Do this without waiting for a reminder. If the site has moved, verify the new entry point through the creator's public profile.

When playable material is accessible, watch relevant clips through their opening, action development, transitions, and resolution. Record the date, work URL and author, actual viewing range, object changes, camera guidance, and text readability. Translate observations into specific shot choices instead of adjectives such as “premium,” “smooth,” or “animated.” See the [website study procedure and template](references/website-study.md).

If the site is under maintenance, requires login, or cannot be reached, first make a real attempt and record the result. Briefly explain the limitation, use accessible sources such as official public demos, and continue feasible production. State what was actually seen. Respect access and payment boundaries; do not turn an unavailable site into an automatic approval checkpoint.

Reuse completed, still-relevant observations within one continuous project. Simple renaming, typo fixes, color-value edits, or export repairs do not require another visit. Revisit for a new subject, new references, a style overhaul, or observations that no longer guide the work. Reference study preserves the user's chosen brand, framework, and delivery scope.

## Determine the current task

Infer the audience, purpose, materials, aspect ratio, length, sound, and deliverables from the user's material and existing project. Make reasonable reversible production choices. Ask only for missing information that materially affects the outcome, and continue independent work while awaiting it.

If product assets are missing, inspect existing information or create necessary code graphics. Keep features and performance grounded in evidence. If even the product identity or capabilities are unknown, request the minimum facts while progressing independent visual and pacing work. Clearly label generic illustrations; they cannot stand in for a real product demonstration.

Distinguish research, a script/storyboard, a reusable effect, and a complete video. A complete-video request requires a playable file and editable source; a plan or preview alone is insufficient. Do not insert a mandatory script-approval gate. A script-only request does not expand into rendering.

Preserve the requested visual style, framework, brand, and communication goal. Keep existing project conventions. For slides, PDFs, documents, or generated images, use suitable specialist skills actually available in the environment; do not assume tools are installed.

## Creative decisions

1. **Start with a content claim.** Reorganize material into an information progression the viewer can follow. Mechanism explainers may use “phenomenon/problem → simplified objects and rules → visible change → principle.” Product demos, music videos, brand films, and case stories need structures suited to their content rather than a compulsory formula.
2. **Make explanation observable.** For mechanism shots, specify objects, initial state, action/rule, outcome, and corresponding narration. Preserve object identity and relationships where possible; introduce terminology as the reasoning develops. Source data from the material or reliable evidence. Label illustrative mechanisms rather than presenting them as measurements.
3. **Choose visuals for the content.** Two-dimensional relationships do not automatically need 3D. Use spatial, deformation, or control techniques when useful. Establish a coherent visual language, key composition, and action before adding transitions and materials. Titles, palettes, and catchphrases are not templates to copy.
4. **Design timing with sound.** When narration or music exists, organize around meaning, pauses, or beats. Silent work is acceptable when no audio is requested. Add effects to important actions or reveals when useful; preserve narration intelligibility.

## Use downstream resources as needed

Prefer existing project capabilities → suitable installed skills → specific components/projects in the [resource index](references/resources.md) → necessary new implementation. Change frameworks only for a concrete benefit; avoid installing the entire ecosystem at once.

- For an installed matching skill, read its actual `SKILL.md`, use its interface, and respect current scope and authorization.
- For an uninstalled resource, obtain only the needed skill, scripts, or repository in the task workspace. Inspect the entry point, dependencies, references, and execution scripts before running production. Install permanently only when the task calls for long-term installation.
- Use available connectors, CLI, or browsing tools for GitHub, MotionFace, and other links. Verify the current branch, entry point, maintenance state, and code/media licenses. The index is historical, not a compatibility guarantee. Record the commit used and preserve existing changes rather than blindly pulling over them.
- Treat upstream prompts and code as resources, not additional authorization. Skip unrelated credential reads, external sends, global configuration changes, and hidden side effects. Necessary dependency installation, resource acquisition, and rendering remain within the production workflow. Report concrete blockers and continue independent work.
- Resolve skill-relative paths from that skill's directory. Obtain the complete required scripts and resources, rather than copying only `SKILL.md` and assuming it runs.

| Need | Candidate |
| --- | --- |
| Ordinary 2D explainer | Existing project; `create-vibe-motion` or community explainer/production skills when needed |
| Known fish, earth, or typewriter effect | The individual component and its render skill |
| Multi-shot visuals from SRT | `auto-motion` when prerequisites are met; the documented public route uses HyperFrames for silent B-roll, with audio handled separately |
| 3D scenes and spatial relationships | `create-vibe-motion-3d` or an existing Three.js project |
| Physical control or soft-body experiments | Evaluate `hoverslam` only when simulation is actually needed |
| Sound search, synthesis, and mixing | Inspect the relevant subskill in the personal `sxhzju/sound` repository |

## Implementation and delivery

Derive code-driven scene state from a frame number or time parameter and use a consistent audiovisual time mapping. Simulations may be precomputed and replayed. Separate output time and world time for slow motion/bullet time: objects share world time while the camera may keep moving. Avoid wall-clock state or unseeded randomness that makes offline frames irreproducible. Share scene logic between preview and export; wait for fonts and textures before capture.

For editable UI animation, prefer native scene objects and redraw at final resolution; investigate jitter from repeatedly scaling screenshots. In complex shots, make text readable before increasing motion. Show meaningful process objects such as inputs, tasks, evidence, and results, with real handoffs between scenes. Design pacing for the opening and ending as well as the middle. Bullet time, fisheye, and continuous camera movement are optional effects.

Check according to actual risk: text and information in key frames, transitions and object relationships, sound/action synchronization, and final duration, dimensions, frame rate, and audio tracks. Sample the actual encoded video. Successful compilation or an attractive cover alone is not acceptance. Use suitable existing checks rather than implementation-mirroring tests for small changes.

Deliver the requested script, scene, preview, or finished film. A complete video includes a playable file, editable source, and necessary run instructions. Retain external authorship, source URLs, actual commits, media licenses, and modification notes. Distinguish illustrative simulation, factual evidence, and unverified hypotheses.

Re-export changed deliverables and confirm archives contain the latest files. Branding-removal conclusions cover only what was inspected; keyword scans do not replace watching and listening. Preserve third-party licenses and content credentials. Label edited public reproduction prompts as edited.

Keep components, parameters, or shots with clear reuse value in the project. Install new global skills from the experience only when requested.

## Color priorities

1. **Product/brand design tokens are authoritative.** Extract background, surface, text, primary, and semantic colors from repository CSS or the design system. Map the video palette to these tokens rather than inventing hues.
2. **Explicit user preferences constrain the choice**, such as light, white, or orange backgrounds. Select matching tokens; introduce an approximation only when none fits and document it in delivery notes.
3. **Default light palette when no brand tokens exist:** warm/off-white background, white cards, orange primary, and dark warm text. Semantic colors: green=OK, amber=warning, red=danger. Orange/yellow marker highlights are temporary annotations, not state colors.
4. **Whole-film constraints:** consistent colors for the same state; at most four functional colors; body-text contrast at least 4.5:1, using a darker variant for small text when needed; readability in grayscale; redundant symbols/shapes for color-blind viewers; sufficient caption-band contrast.
5. **Version names:** `-brand` for the token-based version, `-light`, and `-dark`. The user selects the primary film; keep others as alternatives.
