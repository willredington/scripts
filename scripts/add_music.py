import argparse
import re
import subprocess
import sys
import tempfile
import unicodedata
import urllib.request
from pathlib import Path
from urllib.parse import unquote

import yt_dlp


MUSIC_DIR = Path("/Users/willredington/shared/music")
MAX_SLUG_LENGTH = 80

# YouTube's default ANDROID_VR client formats return 403s (its direct CDN
# URLs are blocked even with a valid PO token). web_safari/android formats
# require solving a JS challenge (remote_components) but actually work.
YDL_NETWORK_OPTS = {
    "extractor_args": {"youtube": {"player_client": ["web_safari", "android"]}},
    "remote_components": ["ejs:github"],
}


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


def crop_to_square(src: Path, dst: Path) -> None:
    # Commas inside crop(...) must be escaped so ffmpeg's filter parser does
    # not read them as filter-chain separators.
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
         "-vf", "crop=min(iw\\,ih):min(iw\\,ih)", "-frames:v", "1", str(dst)],
        check=True,
    )


def write_tags(
    mp3_path: Path,
    title: str | None,
    artist: str | None,
    cover_path: Path | None,
) -> None:
    from mutagen.id3 import ID3, APIC, TIT2, TPE1
    from mutagen.id3._util import ID3NoHeaderError

    try:
        tags = ID3(mp3_path)
    except ID3NoHeaderError:
        tags = ID3()

    if title:
        tags.setall("TIT2", [TIT2(encoding=3, text=title)])
    if artist:
        tags.setall("TPE1", [TPE1(encoding=3, text=artist)])
    if cover_path:
        tags.setall(
            "APIC",
            [APIC(
                encoding=3,
                mime="image/jpeg",
                type=3,  # front cover
                desc="Cover",
                data=Path(cover_path).read_bytes(),
            )],
        )

    tags.save(mp3_path)


def get_track_info(url: str) -> dict:
    with yt_dlp.YoutubeDL({"quiet": True, **YDL_NETWORK_OPTS}) as ydl:
        return ydl.extract_info(url, download=False)


def download_thumbnail(url: str, dst: Path) -> None:
    urllib.request.urlretrieve(url, dst)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download a YouTube video as MP3")
    parser.add_argument("url", help="YouTube URL")
    args = parser.parse_args()

    # Remove shell backslash escapes (e.g. \? \& \=) then percent-decode
    url = unquote(re.sub(r"\\(.)", r"\1", args.url))

    MUSIC_DIR.mkdir(parents=True, exist_ok=True)

    info = get_track_info(url)
    title = info.get("title") or "unknown"
    slug = slugify(title)
    output_path = MUSIC_DIR / f"{slug}.mp3"

    if output_path.exists():
        print(f"Already exists: {output_path.name}")
        sys.exit(0)

    ydl_opts = {
        "format": "bestaudio/best[height<=480]/best",
        "outtmpl": str(MUSIC_DIR / f"{slug}.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        **YDL_NETWORK_OPTS,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    # Best-effort metadata: never let a tagging failure discard the MP3.
    artist = resolve_artist(info)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        cover_path = None
        thumb_url = info.get("thumbnail")
        if thumb_url:
            try:
                raw = tmp / "thumb"
                download_thumbnail(thumb_url, raw)
                cover_path = tmp / "cover.jpg"
                crop_to_square(raw, cover_path)
            except Exception as err:
                print(f"Warning: could not prepare thumbnail: {err}", file=sys.stderr)
                cover_path = None
        try:
            write_tags(output_path, title, artist, cover_path)
        except Exception as err:
            print(f"Warning: could not write tags: {err}", file=sys.stderr)

    print(f"Saved: {output_path.name}")
