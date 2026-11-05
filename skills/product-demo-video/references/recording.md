# Recording practicalities

## Capture route

Use an available browser/recording integration if it supports the required work and follow its instructions. Otherwise use the portable Playwright wrapper. Check existing app/package scripts and local ports before starting services. Keep the user's current browser and unrelated services intact.

The wrapper creates a fresh browser context and records only the scenario's actual page. A scenario may use an explicitly authorized saved auth context, but keep it outside the skill and output it nowhere. The helper does not grant app access, seed data, send messages, or implement product features.

## State and correlation

- Set `viewport` and `screen` consistently. A headless full-screen click can enter a smaller display; check `innerWidth/innerHeight`, capture a frame, and compare. A legitimate crop of the real full-screen canvas is possible, but do not claim the discarded gray area was a usable recording.
- A one-time initial session selection must not be unconditionally rewritten by an init script on every reload. That can make a refresh appear to restore the wrong conversation.
- In a streaming product, wait for the **new run's** text or streaming marker, not a pre-existing answer elsewhere on the page. Correlate to the current run/message when possible. A visible old answer does not prove the new response has begun.
- Scope selectors to the active pane. Main chat and management panels can share input labels.
- A zero-height empty message container may be attached but not visible; wait for the meaningful readiness condition rather than a generic visibility assertion.
- Avoid long JSON/program strings through a PTY; canonical input limits can truncate them. Store the scenario as a file and pass its path.

## Timing and preservation

Keep raw takes and explicit edit selections. Marker times based on page creation are approximate: inspect first frames and use actual file duration before setting trim boundaries. Finalize video by closing the page/context. On error, save the failed take and diagnostics, exit with failure, and resume or rerecord narrowly.

If composition uses multiple original takes, preserve their source paths and trim decisions; do not attach one take's wall-clock range to the composite. Avoid silent state manipulation just to manufacture a desired screen.

## Printing and downloads

Exercise the application's actual export control and verify the downloaded artifact. For headless PDF capture, retain the product's print component and browser print engine. If intercepting `window.print()` to save through the browser API, describe that as automated browser printing, not a recording of a system print dialog.

Prematurely forcing print media can remeasure responsive diagrams at the wrong width and clip them in the PDF. Render the saved PDF pages and check all diagram nodes and text. The actual exported document can be shown in a clean preview titled for its user purpose, without tool/runtime implementation labels.
