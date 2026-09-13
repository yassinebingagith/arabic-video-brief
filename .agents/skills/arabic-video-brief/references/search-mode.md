# Search mode

When starting in search mode or when prompted, collect the search requirements:

1. Topic(s) or theme(s) (single or multiple).
2. Ranking style: `trending`, `recent`, `popular`, `classic`, `rated`, or `relevant` (default: `recent` or `popular`).
3. Two-letter content region and preferred source language (default: `US` / `ar`).
4. Duration: `any`, `short`, `medium`, or `long`.

Call the engine's `search` command. The official YouTube Data API v3 is used with `YOUTUBE_API_KEY` from `.env`.

Present candidates clearly with title, channel, publication date, duration, and live view count. Once candidates are chosen, render them strictly **sequentially one-by-one**.
