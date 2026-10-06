# scripts

A personal collection of command-line utilities, packaged as the `scripts` Python package and managed with [uv](https://docs.astral.sh/uv/).

The main use is a small music pipeline:

```
YouTube ──add-music──▶ ~/shared/music (Mac) ──rclone──▶ S3 bucket ──FolderSync──▶ Android phone
```

1. `add-music` downloads a YouTube video as a tagged MP3 into the local music folder and uploads it to S3.
2. `sync-music` mirrors the whole local folder to S3 (deletions included).
3. The **FolderSync** app on Android pulls from the same S3 bucket onto the phone.

## Commands

### `add-music`

Download a YouTube video as an MP3, tagged with title, artist, and cover art.

```sh
uv run add-music <youtube-url>
```

- Accepts `watch?v=…`, `youtu.be/…`, `/shorts/…`, and `music.youtube.com` links (playlist/radio context is dropped). Quote the URL or paste it as-is — shell backslash escapes are handled.
- Skips the download if a file for that title already exists.
- Best-effort tags the resulting MP3 with title, artist, and a square-cropped cover thumbnail.
- Uploads just the new file to S3 after a successful download (non-destructive `rclone copy`).

### `sync-music`

Mirror the local music library to S3.

```sh
uv run sync-music
```

The local folder is the source of truth: the bucket is made to match it exactly, so **files removed locally are also removed from S3** (and then from the phone on its next FolderSync run). `.DS_Store` and `.stfolder/` are excluded.

## Setup from scratch (macOS)

These steps assume a fresh Mac with nothing installed.

### 1. Homebrew

```sh
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Follow the "Next steps" it prints to add `brew` to your `PATH`, then open a new terminal.

### 2. Host tools

```sh
brew install git uv ffmpeg node rclone awscli
```

| Tool | Why |
| --- | --- |
| `uv` | Installs Python (3.12, pinned in `.python-version`) and the project's dependencies |
| `ffmpeg` | MP3 extraction and cover-art cropping (`ffprobe` is also used by the tests) |
| `node` | Builds/runs the YouTube PO-token generator (step 5) |
| `rclone` | Uploads/mirrors the music folder to S3 |
| `awscli` | Provides the AWS credentials rclone reuses |

### 3. Clone the repo and install dependencies

```sh
git clone <this-repo-url> ~/projects/scripts
cd ~/projects/scripts
uv sync
```

`uv sync` downloads Python 3.12 if needed and creates `.venv` with `yt-dlp`, `mutagen`, and `bgutil-ytdlp-pot-provider`.

### 4. Point the code at your music folder

The music folder path is hardcoded. Edit `MUSIC_DIR` in `scripts/music_sync.py` to match the new machine (e.g. `/Users/<you>/shared/music`). **Do this first** — `add-music` fails on a stale path, not just `sync-music`.

### 5. Build the YouTube PO-token server

YouTube blocks downloads without a "PO token". The pip plugin installed in step 3 only talks to a token generator, which has to be built separately at this exact path:

```sh
git clone --branch 1.3.1 https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git ~/bgutil-ytdlp-pot-provider
cd ~/bgutil-ytdlp-pot-provider/server
npm ci
npx tsc
```

Match the `--branch` tag to the `bgutil-ytdlp-pot-provider` version in `uv.lock`. yt-dlp finds the built server automatically; if this directory is missing, downloads start failing with HTTP 403.

### 6. AWS credentials

You need an IAM user/access key with read/write access to the music bucket (`musicsyncstack-musicbucket99400322-v1ttjodlqwlb`).

```sh
aws configure          # enter access key, secret, and default region
aws s3 ls s3://musicsyncstack-musicbucket99400322-v1ttjodlqwlb   # sanity check
```

### 7. rclone remote

Create `~/.config/rclone/rclone.conf`:

```ini
[music-s3]
type = s3
provider = AWS
env_auth = true
region = us-east-2
no_check_bucket = true
```

`env_auth = true` makes rclone reuse the credentials from `~/.aws/credentials` instead of storing a second copy. If the bucket ever moves, check its region with `aws s3api get-bucket-location --bucket <bucket>`.

Verify:

```sh
rclone lsf music-s3:musicsyncstack-musicbucket99400322-v1ttjodlqwlb | head
```

### 8. Try it

```sh
cd ~/projects/scripts
uv run add-music "https://www.youtube.com/watch?v=<id>"
uv run sync-music
```

## Phone setup (Android, FolderSync)

The phone doesn't talk to the Mac directly — it pulls from the S3 bucket.

1. Install **FolderSync** (Tacit Dynamics) from the Play Store.
2. **Accounts → Add account → Amazon S3.** Enter the same access key and secret (a separate read-only IAM key is fine for the phone), and set the region to `us-east-2`.
3. **Folderpairs → Add folderpair:**
   - **Account:** the S3 account above; **Remote folder:** the music bucket.
   - **Local folder:** e.g. `/storage/emulated/0/Music`.
   - **Sync type:** *To local folder* (one-way, S3 → phone).
   - Enable **Sync deletions** if you want songs removed from the Mac (via `sync-music`) to disappear from the phone too.
4. Set a **schedule** (e.g. daily, Wi-Fi only), or tap **Sync** manually after adding music.
5. Point your music player at the local folder.

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

This is a single-user, personal toolkit — `MUSIC_DIR` and `RCLONE_REMOTE` in `scripts/music_sync.py` are specific to this setup. See `CLAUDE.md` for architecture notes, including the YouTube anti-bot workarounds.
