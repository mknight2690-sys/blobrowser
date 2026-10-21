# BloBrowser sales site: handoff guide for AI coding agents

You are taking over the public sales page for **BloBrowser**, an AI trading bot for the BloFin exchange. This file has everything needed to run, edit, redeploy and finish the project. Read it fully before changing anything.

## What this repo is

- A single-page static sales site (`index.html`, no build step, no framework) hosted on **GitHub Pages** from the `main` branch root.
- A ~66-second promo video with an AI-generated presenter (`media/blobrowser-promo.mp4` plus the poster `media/blobrowser-promo.jpg`), embedded right after the hero.
- `production/`: the scripts and source assets that made the video. GitHub Pages doesn't publish this folder (see `_config.yml`).

Original live URL: https://mknight2690-sys.github.io/blobrowser/

## Product facts (source of truth for all copy)

Only use these facts. Don't invent features, stats or testimonials.

- Exchange: **BloFin** futures. Users paste BloFin API keys into the dashboard, and the **keys are stored in the user's browser**, never in a database.
- Architecture is **hybrid**. The "brain and guts" (decision engine) run on a **cloud VPS**, and trades go through the user's browser. To trade, the user needs:
  1. their computer on, with sleep disabled,
  2. a browser tab open on the BloBrowser page,
  3. a VPN connected to a server in a **BloFin-supported country**.
  If any of these drops, trading pauses. Orders already on the exchange stay there but aren't re-adjusted.
- Brain: **Google Gemini** LLM with **no persistent learning**, so every tick is a fresh read with no memory.
- Four strategies: **Harmonics, Cadence, Momentum, Pulse**.
- Risk engine:
  - **DCA** into losing trades until they flip.
  - **Leverage steps down** as a losing trade goes further underwater.
  - **TP, SL and DCA limit orders** are placed on the exchange at entry and re-adjusted as each DCA fills.
  - **Winner-first harvesting**: profit is taken on winners. Positions *can* close at a loss if the stop-loss is hit.
  - Expect **suppressed unrealized PnL** while underwater trades recover.
- **Matthew Metric (MM)**: withdrawable cash flow. The developer-reported figure is **~$500/week on a $15,000 account**. Always label it developer-reported and not a guarantee.
- Pricing: **$199/mo**, **$1,990/yr** (2 months free, marked "Best Value"), **$3,997 lifetime founder** (limited seats).
- Has an interactive dashboard with charts.

### Compliance guardrails (keep these)

- Keep the footer risk disclosure, the "developer-reported / not a guarantee" labels and the line "Leveraged trading carries serious risk."
- Never claim guaranteed profits, "risk-free" or "never loses".
- Keep the VPN wording as "a server in a BloFin-supported country". Never market it as a way around geo-restrictions. BloFin blocks some jurisdictions (including the US), and its terms forbid circumventing that.

## Repo layout

```
index.html                 the whole site (inline CSS + JS)
media/blobrowser-promo.mp4 promo video (H.264/AAC, faststart, keep < 12 MB)
media/blobrowser-promo.jpg poster frame
_config.yml                tells GitHub Pages (Jekyll) not to publish production/ and the docs
production/                video pipeline (see below)
```

## Run the site locally

```
python -m http.server 8000
```

Open http://localhost:8000. There's no build step; edit `index.html` directly.

## Deploy under your own GitHub account

Use the GitHub CLI (`gh auth login` first):

```
gh repo create blobrowser --public --source . --push
gh api -X POST repos/<OWNER>/blobrowser/pages -f "source[branch]=main" -f "source[path]=/"
```

The site goes live at `https://<OWNER>.github.io/blobrowser/` after about a minute. If the repo was transferred to you instead, just push to `main`. Pages is already enabled.

## Open TODOs (in priority order)

1. **Checkout links.** Every call-to-action is a ghost button (transparent with an outline) whose `href` is `#` or `#pricing`. Wire these up to real checkout URLs (Stripe Payment Links or similar):
   - Pricing cards: "Start Monthly", "Go Annual →", "Claim a Founder Seat".
   - "Book a Live Demo" (final CTA section).
   - Footer: Terms, Privacy, Contact. These need real pages.
2. **Finish the promo lip-sync** (see the "Video pipeline" section). The first ~30 seconds show the presenter talking. Segments 3 to 5 (30–61 s) are branded feature cards because the free GPU quota ran out. Generating `production/head/raw3.mp4` to `raw5.mp4` makes her talk for the whole video.
3. Replace the illustrative dashboard mock in the hero with real dashboard screenshots or recordings if available.
4. Optional: add analytics and a meta/OG share image.

## Video pipeline (`production/`)

How the video is built:

| Step | Tool (all free) | File |
|---|---|---|
| Presenter image (original, fictional) | FLUX.1-schnell via the Hugging Face Space `black-forest-labs/FLUX.1-schnell` | `presenter/p27.png` |
| Voiceover script | hand-written, using only the product facts above | `voiceover.txt` |
| Voice and word timings | `edge-tts`, voice `en-US-AvaNeural` | `tts.py` → `vo.mp3`, `vo.srt` |
| Lip-sync talking head | MoDA via the Hugging Face Space `multimodalart/MoDA-fast-talking-head` (ZeroGPU) | `make_head.py` → `head/raw{0..5}.mp4` |
| Feature-card fill-ins for missing segments | Pillow + ffmpeg | `make_broll.py` |
| Final edit | ffmpeg (title card, crossfades, burned-in captions, end card, under 12 MB) | `build.py` → `../media/` |

### Setup (Windows/PowerShell; adapt for macOS/Linux)

Requirements: Python 3.11+, ffmpeg and ffprobe on PATH, and a Hugging Face account token (`huggingface-cli login`).

```
cd production
py -3 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
```

### Common tasks

- **Finish the lip-sync and publish:** `powershell -ExecutionPolicy Bypass -File upgrade.ps1`
  - It lip-syncs any segment that's missing `head/raw{i}.mp4`, and waits and retries every 20 minutes while the free ZeroGPU quota is empty.
  - Then it rebuilds, checks the duration (65–68 s), the size (under 12 MB) and the audio level, and pushes to `main`.
  - A free Hugging Face account gets roughly 3 lip-sync segments per day. HF PRO ($9/mo) gives 40 GPU-minutes a day and finishes it at once.
- **Rebuild without new lip-sync:** run `.\.venv\Scripts\python make_broll.py`, then `.\.venv\Scripts\python build.py`. That writes straight to `../media/`; commit and push.
- **Change the script or voice:**
  1. Edit `voiceover.txt`, then run `.\.venv\Scripts\python tts.py`. This regenerates `vo.mp3` and `vo.srt`.
  2. Delete `head/raw*.mp4`, because the old lip-sync no longer matches the new audio.
  3. Re-run `upgrade.ps1`.
  4. Update the `CUTS` list in `make_broll.py` to the cut points that `make_head.py` prints.
  5. Update the duration badge in `index.html` (`<span class="promo-dur">`).
- **Change the presenter:** replace `presenter/p27.png` with a 1344x768 image, delete `head/raw*.mp4`, and re-run. Then adjust `FACE_X`/`FACE_Y` in `make_head.py` (the face center as a fraction of width and height) so close-ups stay centered.
- `veo.py` is a Google Veo client. It needs a **paid** Gemini API key, and the Veo 3.1 *preview* models were scheduled to shut down on 2026-10-22, so treat it as reference only.

### Page embed contract

The video section in `index.html` (id `promo`) expects:
- `media/blobrowser-promo.mp4`
- `media/blobrowser-promo.jpg`

It uses `<video controls playsinline preload="metadata" poster=…>` with a custom centered play button (`#promoCover`). The script hides the native controls until playback starts and resets to the poster when the video ends. If you rename the files, update both `src` and `poster`.

## Secrets

This repo contains **no secrets**. Never commit API keys (BloFin, Gemini, Hugging Face, GitHub). Scripts read keys from environment variables or the local Hugging Face login.
