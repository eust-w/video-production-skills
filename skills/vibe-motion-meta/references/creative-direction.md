# Content, script, and storyboard

English | [简体中文](creative-direction.zh-CN.md)

This is creative guidance, not a verbatim account of the methods of 浙大猫学长. Adapt it to the subject, available material, and user's goals. See [resources](resources.md) for tool selection.

Before new work or a substantial visual redesign, complete the [website study](website-study.md) and turn actual observations into shot choices. For implementation problems involving clarity, camera work, and transitions, see [production lessons](production-lessons.md).

## From source material to a story

Extract the claim, supporting facts, key objects, relationships/mechanisms, and limitations. Slide order is an input structure, not necessarily the video sequence. Preserve factual sources; avoid inventing performance numbers or causal links for drama.

| Content | Possible progression | Role of the visuals |
| --- | --- | --- |
| Mechanism explainer | Interesting phenomenon → simplified model → incremental rules → explanation | Show what each rule changes |
| Product/solution | Use context → concrete obstacle → operation → result and evidence | Demonstrate real actions or verifiable mechanisms |
| Case/story | Goal → constraints → choices → consequences | Maintain continuous state changes for people/objects |
| Brand motion graphics | Core claim → a few visual motifs → memorable resolution | Reinforce brand information through typography, composition, and rhythm |
| Music/lyrics | Musical structure/imagery → motif development → climax and return | Support beats and emotion without imposing a scientific argument |

A subject may expose an unfamiliar mechanism behind a familiar outcome, or complex behavior arising from a few rules. Every section does not need an exaggerated hook. The film must deliver on its title.

## Narration and information density

Turn written points into speech: prioritize concrete objects, actions, and outcomes. Give new terms an operational meaning on first use, then retain necessary technical language. Abstract noun lists cannot replace demonstrations.

For existing narration/SRT, inspect meaning and timing first. Rewrite only when requested or necessary to correct a problem. Preserve protected lyrics, exact caption wording, and established timing. One shot may span several sentences; each sentence does not need its own card.

If the script is unfinished, resolve facts and logic before polishing animation. For a direct request for a finished video, this is an internal iteration sequence, not an approval gate.

## Minimum shot description

Use a brief table or structured note, scaled to the work's complexity, covering:

- What the shot communicates and its narration/caption time range.
- Objects, initial state, and intended focus of attention.
- Action/rule, visible outcome, and relationship retained into the next shot.
- Required code components, assets, and sound; factual and asset sources.

Example mechanism shot:

> Topic: why scheduling rules matter. Initial state: tasks queue while some nodes are idle. Action: change the task-to-node matching rule. Outcome: tasks enter suitable nodes and the queue changes. Handoff: retain the same tasks to explain resource constraints. Label: illustrative animation; show no efficiency-improvement percentage without measurements.

This illustrates explanatory storytelling, not a compulsory domain metaphor. Important rule changes must be visible; decorative bouncing is not causal explanation.

## Visuals and motion

Start with the most complex key frame: are hierarchy, text size, paths, and relationships clear? In explanatory scenes, states, colors, and shapes need stable meanings. Camera movement guides attention and scale. Preserve object identity across shots or establish a clear handoff so viewers need not identify everything again.

Choose motion by purpose: anticipation supports prediction, easing suggests inertia, follow-through and delay convey weight, and pauses allow comprehension. Use squash/stretch, hand-drawn line variation, or exaggeration only when suitable. A Disney-principles skill does not require personifying every UI element.

Hand-drawn, 3D, paper, neon, and interface aesthetics are options. Establish consistency from the user's brand and references. Attribute third-party references and community recreations accurately rather than claiming them as the creator's original designs.

## Sound and beats

For narration-led work, preserve understandable speech and pauses, then place actions near key words, reveals, and conclusions. Music-led work may follow beats and sections. Add transition, collision, or completion sounds when useful; every movement need not make a sound.

If the first SRT entry starts after zero, distinguish global recording time from local shot time. If clip production resets captions to zero, restore the same lead-in before combining with the original recording, or apply one consistent trim offset to audio, captions, and visuals. Do not concatenate zero-based visuals with untrimmed narration or hide unchecked duration differences using shortest-stream truncation.

Listen to the actual result and check audiovisual relationships. Waveforms, loudness, and spectra are diagnostic aids. Sound selection, procedural synthesis, and mixing are different tasks; load relevant sound subskills only as needed. A single notification sound does not justify an entire synthesizer stack.

## Before finishing

Does the film answer its opening question or fulfill its promise? Do visuals explain relationships beyond the words? Are any numbers unsupported, objects confused, or details unreadable? Do movement and sound consume attention needed for understanding? Inspect the output the user actually needs and deliver that result.
