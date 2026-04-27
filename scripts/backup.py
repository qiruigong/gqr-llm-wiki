"""Create a timestamped zip backup of the entire project to a target directory."""
import sys
import zipfile
from pathlib import Path
from datetime import datetime, timezone

EXCLUDE_DIRS = {".git", "__pycache__", "backups"}
EXCLUDE_FILES = {".env"}


def create_backup(target_dir: str) -> tuple[Path, float]:
    target = Path(target_dir)
    target.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_name = f"llm-wiki-backup-{timestamp}.zip"
    backup_path = target / backup_name

    project_root = Path(".")
    with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in project_root.rglob("*"):
            if file.is_file():
                parts = set(file.parts)
                if parts & EXCLUDE_DIRS:
                    continue
                if file.name in EXCLUDE_FILES:
                    continue
                zf.write(file)

    size_mb = backup_path.stat().st_size / (1024 * 1024)
    return backup_path, size_mb


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/backup.py <target_directory>", file=sys.stderr)
        sys.exit(1)
    path, size = create_backup(sys.argv[1])
    print(f"备份完成：{path}（{size:.1f} MB）")
