import subprocess
from pathlib import Path

MUSIC_DIR = Path("/Users/willredington/shared/music")
RCLONE_REMOTE = "music-s3:musicsyncstack-musicbucket99400322-v1ttjodlqwlb"


def sync_to_cloud(path: Path) -> None:
    subprocess.run(
        ["rclone", "copy", str(path), f"{RCLONE_REMOTE}/"],
        check=True,
    )


MIRROR_EXCLUDES = [".DS_Store", ".stfolder/**"]


def mirror_to_cloud(path: Path) -> None:
    """Make the remote match `path` exactly (minus local/OS junk), deleting remote files no longer present locally."""
    exclude_args = []
    for pattern in MIRROR_EXCLUDES:
        exclude_args += ["--exclude", pattern]
    subprocess.run(
        ["rclone", "sync", str(path), f"{RCLONE_REMOTE}/", *exclude_args],
        check=True,
    )
