from scripts.music_sync import MUSIC_DIR, sync_to_cloud


def main() -> None:
    sync_to_cloud(MUSIC_DIR)
    print("Synced")
