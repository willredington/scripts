import subprocess
from pathlib import Path

MUSIC_DIR = Path("/home/will/Music")
RCLONE_REMOTE = "music-s3:musicsyncstack-musicbucket99400322-v1ttjodlqwlb"


def sync_to_cloud(path: Path) -> None:
    subprocess.run(
        ["rclone", "copy", str(path), f"{RCLONE_REMOTE}/"],
        check=True,
    )
