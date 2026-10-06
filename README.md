# scripts

A personal collection of command-line utilities, packaged as the `scripts` Python package and managed with [uv](https://docs.astral.sh/uv/).

## Commands

### `add-music`

Download a YouTube video as an MP3, tagged with title, artist, and cover art.

```sh
uv run add-music <youtube-url>
```

- Accepts `watch?v=…`, `youtu.be/…`, `/shorts/…`, and `music.youtube.com` links (playlist/radio context is dropped).
- Skips the download if a file for that title already exists.
- Best-effort tags the resulting MP3 with title, artist, and a square-cropped cover thumbnail.
- Uploads the new file to cloud storage after a successful download (see `sync-music` below).

### `sync-music`

Mirror the local music library to cloud storage (S3, via `rclone`).

```sh
uv run sync-music
```

This makes the remote match the local library exactly — files removed locally are also removed from the remote.

## Setup

```sh
uv sync
```

### Requirements

- **Python** — version pinned in `.python-version`, managed via `uv`.
- **[ffmpeg](https://ffmpeg.org/)** — required by `add-music` for MP3 extraction and cover art cropping (`ffprobe` is also used by the test suite).
- **[rclone](https://rclone.org/)** — required by `sync-music`, with a `music-s3` remote configured at `~/.config/rclone/rclone.conf`.
- **[Node/npm](https://nodejs.org/)** — required to build the `bgutil-ytdlp-pot-provider` server component (see below), which `add-music` needs to avoid YouTube 403 errors.

See `CLAUDE.md` for full architecture notes, including the YouTube anti-bot workarounds and cloud sync details.

## Development

```sh
uv run pytest
```

The test suite synthesizes images and a silent MP3 using `ffmpeg`/`ffprobe`, so those must be installed to run it.

### Adding a new utility

1. Create `scripts/<name>.py` with a `main() -> None` entry point.
2. Register it under `[project.scripts]` in `pyproject.toml` as `<command-name> = "scripts.<name>:main"`.
3. Run `uv sync` to make the console command available via `uv run`.

## Notes

This is a single-user, personal toolkit — some paths (e.g. `MUSIC_DIR` in `scripts/music_sync.py`) are hardcoded to this machine. See `CLAUDE.md` for details.
