"""Create a timestamped zip of knowledge base data (wiki/, sources/, persona.md)."""
import sys
import zipfile
from pathlib import Path
from datetime import datetime, timezone

KNOWLEDGE_ITEMS = ["wiki", "sources", "persona.md"]


def create_backup(
    target_dir: str, project_root: Path | None = None
) -> tuple[Path, float, list[str]]:
    if project_root is None:
        project_root = Path(__file__).parent.parent

    target = Path(target_dir)
    target.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_name = f"llm-wiki-knowledge-{timestamp}.zip"
    backup_path = target / backup_name

    backed_up: list[str] = []

    with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for item_name in KNOWLEDGE_ITEMS:
            item_path = project_root / item_name
            if not item_path.exists():
                continue
            if item_path.is_file():
                zf.write(item_path, f"knowledge/{item_name}")
                backed_up.append(item_name)
            elif item_path.is_dir():
                for file in item_path.rglob("*"):
                    if file.is_file():
                        rel = file.relative_to(project_root)
                        zf.write(file, f"knowledge/{rel}")
                backed_up.append(item_name)

    size_mb = backup_path.stat().st_size / (1024 * 1024)
    return backup_path, size_mb, backed_up


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/backup.py <target_directory>", file=sys.stderr)
        sys.exit(1)
    path, size, items = create_backup(sys.argv[1])
    items_str = "、".join(items) if items else "（无内容）"
    print(f"知识库备份完成：{path}（{size:.1f} MB）")
    print(f"已备份：{items_str}")
