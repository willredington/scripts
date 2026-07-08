import argparse
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import unquote

import yt_dlp


MUSIC_DIR = Path("/Users/willredington/shared/music")
MAX_SLUG_LENGTH = 80


def slugify(text: str, max_length: int = MAX_SLUG_LENGTH) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"['’]", "", text)
    text = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
    if len(text) > max_length:
        text = text[:max_length].rsplit("-", 1)[0]
    return text


def resolve_artist(info: dict) -> str | None:
    for key in ("artists", "artist", "creator", "uploader", "channel"):
        value = info.get(key)
        if not value:
            continue
        if isinstance(value, list):
            joined = ", ".join(v for v in value if v)
            if joined:
                return joined
        elif isinstance(value, str) and value.strip():
            return value.strip()
    return None


def get_track_title(url: str) -> str:
    with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
        info = ydl.extract_info(url, download=False)
        return ydl.prepare_filename(info, outtmpl="%(title)s")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download a YouTube video as MP3")
    parser.add_argument("url", help="YouTube URL")
    args = parser.parse_args()

    # Remove shell backslash escapes (e.g. \? \& \=) then percent-decode
    url = unquote(re.sub(r"\\(.)", r"\1", args.url))

    MUSIC_DIR.mkdir(parents=True, exist_ok=True)

    slug = slugify(get_track_title(url))
    output_path = MUSIC_DIR / f"{slug}.mp3"

    if output_path.exists():
        print(f"Already exists: {output_path.name}")
        sys.exit(0)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(MUSIC_DIR / f"{slug}.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    print(f"Saved: {output_path.name}")
