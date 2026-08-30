import subprocess
from pathlib import Path

from scripts.add_music import crop_to_square, normalize_url, resolve_artist, write_tags


def _make_image(path: Path, width: int, height: int) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
         "-i", f"color=c=red:s={width}x{height}", "-frames:v", "1", str(path)],
        check=True,
    )


def _dimensions(path: Path) -> tuple[int, int]:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x", str(path)],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    w, h = out.split("x")
    return int(w), int(h)


def test_resolve_artist_prefers_artists_list():
    info = {"artists": ["A", "B"], "artist": "C", "uploader": "U"}
    assert resolve_artist(info) == "A, B"


def test_resolve_artist_falls_back_to_artist_field():
    assert resolve_artist({"artist": "C", "uploader": "U"}) == "C"


def test_resolve_artist_falls_back_to_uploader():
    assert resolve_artist({"uploader": "U", "channel": "Ch"}) == "U"


def test_resolve_artist_falls_back_to_channel():
    assert resolve_artist({"channel": "Ch"}) == "Ch"


def test_resolve_artist_returns_none_when_absent():
    assert resolve_artist({"title": "x"}) is None


def test_resolve_artist_ignores_empty_values():
    assert resolve_artist({"artist": "", "artists": [], "uploader": "U"}) == "U"


def test_crop_to_square_produces_square(tmp_path):
    src = tmp_path / "wide.png"
    _make_image(src, 640, 360)
    dst = tmp_path / "square.jpg"
    crop_to_square(src, dst)
    w, h = _dimensions(dst)
    assert w == h == 360


def _make_silent_mp3(path: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
         "-i", "anullsrc=r=44100:cl=mono", "-t", "1", str(path)],
        check=True,
    )


def test_write_tags_sets_title_artist_and_cover(tmp_path):
    mp3 = tmp_path / "song.mp3"
    _make_silent_mp3(mp3)
    cover = tmp_path / "cover.jpg"
    _make_image(cover, 300, 300)

    write_tags(mp3, "My Title", "My Artist", cover)

    from mutagen.id3 import ID3
    tags = ID3(mp3)
    assert tags["TIT2"].text == ["My Title"]
    assert tags["TPE1"].text == ["My Artist"]
    apic = tags.getall("APIC")
    assert apic and apic[0].data == cover.read_bytes()


def test_write_tags_skips_missing_fields(tmp_path):
    mp3 = tmp_path / "song.mp3"
    _make_silent_mp3(mp3)

    write_tags(mp3, "Only Title", None, None)

    from mutagen.id3 import ID3
    tags = ID3(mp3)
    assert tags["TIT2"].text == ["Only Title"]
    assert "TPE1" not in tags
    assert not tags.getall("APIC")


WATCH_URL = "https://www.youtube.com/watch?v=xdI_3GdLt8g"


def test_normalize_url_strips_playlist_context():
    assert normalize_url(
        "https://www.youtube.com/watch?v=xdI_3GdLt8g&list=RDvpy_OuMZ6Po&index=12"
    ) == WATCH_URL


def test_normalize_url_leaves_bare_watch_url_alone():
    assert normalize_url(WATCH_URL) == WATCH_URL


def test_normalize_url_undoes_shell_escapes():
    assert normalize_url(
        "https://www.youtube.com/watch\\?v=xdI_3GdLt8g\\&list=RDvpy_OuMZ6Po"
    ) == WATCH_URL


def test_normalize_url_percent_decodes():
    assert normalize_url(
        "https://www.youtube.com/watch%3Fv%3DxdI_3GdLt8g%26list%3DRDvpy_OuMZ6Po"
    ) == WATCH_URL


def test_normalize_url_handles_short_links():
    assert normalize_url("https://youtu.be/xdI_3GdLt8g?si=abc123&t=42") == WATCH_URL


def test_normalize_url_handles_shorts_and_music():
    assert normalize_url("https://www.youtube.com/shorts/xdI_3GdLt8g") == WATCH_URL
    assert normalize_url(
        "https://music.youtube.com/watch?v=xdI_3GdLt8g&list=RDAMVMxdI_3GdLt8g"
    ) == WATCH_URL


def test_normalize_url_passes_through_unknown_urls():
    url = "https://example.com/song.mp3?a=1&b=2"
    assert normalize_url(url) == url
