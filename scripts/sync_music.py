from scripts.music_sync import MUSIC_DIR, mirror_to_cloud


def main() -> None:
    mirror_to_cloud(MUSIC_DIR)
    print("Synced")
