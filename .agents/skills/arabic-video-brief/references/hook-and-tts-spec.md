# Hook & TTS Specification (V2 Pipeline)

## Hook Generation & Selection
- **Role:** An independent, curiosity-inducing conversational Arabic hook (5–10 words).
- **Candidates:** 10 internal Arabic candidates generated and scored across 6 criteria:
  1. Immediate clarity
  2. Curiosity & tension
  3. Specificity
  4. Emotional relevance
  5. Transcript fidelity
  6. Connection to the 4 summary pages
- **Prohibitions:**
  - No repeat or literal translation of the YouTube title.
  - No mention of the guest or channel name.
  - No clichés (`لن تصدق`, `معلومة خطيرة`, `شاهد حتى النهاية`, `في هذا الفيديو`).
  - No emojis, English words, or hashtags.
- **Visual Styling:** Max 2 lines; one key phrase highlighted in Gold (`#F5C518`).

## ElevenLabs TTS Narration
- **Configuration:**
  - `ELEVENLABS_API_KEY`: API key.
  - `ELEVENLABS_VOICE_ID`: Voice identifier (default: George / Conversational).
  - `ELEVENLABS_MODEL_ID`: `eleven_multilingual_v2`.
  - `ELEVENLABS_LANGUAGE_CODE`: `ar`.
- **Audio Processing:**
  - Leading/trailing silence trimmed.
  - Duration strictly bounded under 2.40s.
  - Audio loudness normalized.
- **Fallback:** If API key is unconfigured or request fails, the pipeline automatically proceeds with a visual-only hook without crashing.
