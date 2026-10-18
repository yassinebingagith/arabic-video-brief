# Workflow review — 2026-10-14

Scope: read existing outputs and update workflow/code only. No generation, browser session, API call, video render, or repair of existing content was performed during this review. Runtime tests were deferred at the user's request; verification was limited to source review, Python syntax and skill structure.

## Findings

- The main skill asked for deep-dive and video-thumbnail choices, but the non-interactive CLI defaulted them to false/none. This allowed an agent to skip the questions and still produce a successful MP4. A mixed V1 + V3 request did not explicitly distinguish its initial video setup from its later V3 generation-method choice.
- Both recent video manifests report a 38-second V1 render using `andrea_vanzo_amelie_0030_0100.mp3`. Their deep-dive and thumbnail prompt file fields are null, and the requested files are absent. This is a manifest/file check, not a new audiovisual review.
- `Why-Life-Loses-Its-Magic-How-To-Get-It-Back---Robert-Greene-TQHgk-qft-8`: all six planned images exist. Slide 1 is marked accepted; slides 2–5 and the Facebook image are marked generated, awaiting documented visual acceptance.
- `when-everything-fails-fn5gbP1Fs8U`: slide 1 is marked accepted, slides 2–3 generated, slides 4–5 and the Facebook image missing. This episode is incomplete.
- Both plans select `chatgpt_mcp`, but neither records `generation_session`. The local save helper transfers/registers files; it does not itself generate, wait on, or download images from a browser. The absence of a session record prevents reliable automatic recovery of a previously submitted request without inspecting the actual browser state.

## Changes

- Required, answer-aware setup instructions now apply to all video requests, including mixed video + V3 requests. The CLI requires an explicit version, deep-dive yes/no, and thumbnail none/manual/KIE.ai selection when run non-interactively. `--no-deepdive` is now an explicit opt-out. EOF/cancellation does not silently become a choice. KIE.ai cannot be selected by an empty method response.
- Added the sequential V3 browser/MCP execution procedure: capability check, one persistent session, actual reference uploads, one submission, observed completion, original-file download, local registration, visual acceptance, then the next image. Checkpoints and existing-request recovery precede retries.
- Added read-only `tools/v3_save_image.py next` guidance. It distinguishes unreviewed images, missing images, active requests, unexpected files, changed registered files, and fully accepted packs ready for export.
- API image execution remains conditional on a separately implemented verified adapter and explicit cost authorization. No API fallback is allowed just because browser generation fails.

The updated local helpers and procedure are not proof that a particular connected browser tool can upload/download successfully. That end-to-end capability must be verified when the user later requests a real generation run. Existing packs and their review statuses were left unchanged.
