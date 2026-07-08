from scripts.add_music import resolve_artist


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
