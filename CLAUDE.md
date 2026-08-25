# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A personal collection of command-line utilities, packaged as the `scripts` Python package and managed with [uv](https://docs.astral.sh/uv/). Each utility is a module under `scripts/` exposed as a console command via `[project.scripts]` in `pyproject.toml`. Currently one command exists: `add-music`.

## Commands

- **Sync dependencies / create venv:** `uv sync`
- **Run a console script (without installing):** `uv run add-music <youtube-url>`
- **Add a runtime dependency:** `uv add <package>` (edits `pyproject.toml` + `uv.lock`)
- **Run the tests:** `uv run pytest`

Tests live in `tests/` (pytest). The suite synthesizes images and a silent MP3 with **ffmpeg/ffprobe**, so those must be on the host to run it. There is no linter or formatter configured.

## Adding a new utility

1. Create `scripts/<name>.py` with a `main() -> None` entry point.
2. Register it under `[project.scripts]` in `pyproject.toml` as `<command-name> = "scripts.<name>:main"`.
3. Run `uv sync` to make the console command available via `uv run`.

## Architecture notes

- **Runtime dependency:** `yt-dlp` handles YouTube extraction and download. The MP3 postprocessing (`FFmpegExtractAudio`) requires **`ffmpeg`** to be installed on the host — it is not a Python dependency.
- **Runtime dependency:** `mutagen` writes the ID3 tags (title/artist/cover). ffmpeg is also used to center-crop the thumbnail; `ffprobe` (ships with ffmpeg) is used by the tests.
- **Hardcoded paths:** `add_music.py` writes to `MUSIC_DIR` (`/Users/willredington/shared/music`). Utilities in this repo are single-user by design; expect absolute, machine-specific paths.
- **`add-music` flow:** un-escape shell backslashes + percent-decode the URL → fetch info once via `yt-dlp` (metadata-only) → `slugify` the title into a filename → skip if the `.mp3` already exists (idempotent by slug) → download `bestaudio/best[height<=480]/best` and extract to MP3 → best-effort tag the MP3 with title, artist (`resolve_artist` fallback chain), and the thumbnail center-cropped to a square cover.
- **YouTube anti-bot workarounds (`YDL_NETWORK_OPTS` in `add_music.py`):** YouTube's default `ANDROID_VR` client formats return HTTP 403 even with a valid PO token, so `add_music.py` pins `player_client` to `["web_safari", "android"]` and passes `remote_components: ["ejs:github"]` so yt-dlp fetches its JS-challenge solver script (needed to decrypt `web_safari`/`android` signatures). Format is capped at `height<=480` since those clients no longer expose audio-only tracks (SABR-only streaming) — video is downloaded and discarded during MP3 extraction.
  - **`bgutil-ytdlp-pot-provider`** (pip dependency, auto-discovered by yt-dlp as a plugin) mints the PO token `web_safari` needs. Its actual token-generation code is **not** pip-installable: it lives in a separate TypeScript "server" component cloned to `~/bgutil-ytdlp-pot-provider` and built once with `npm ci && npx tsc` (uses the host's Node/npm — see `~/bgutil-ytdlp-pot-provider/server/README.md` upstream for details, or https://github.com/Brainicism/bgutil-ytdlp-pot-provider). yt-dlp finds it automatically via `script-deno`/`script-node` backends at that default path — no code wiring needed. If this directory is missing, POT generation fails and `web_safari` downloads may 403 again.
- The `scripts.egg-info/` directory is stale generated metadata (references a defunct `main.py`); ignore it and do not edit it by hand.
