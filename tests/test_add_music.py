import subprocess
from pathlib import Path

from scripts.add_music import crop_to_square, resolve_artist, write_tags


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
