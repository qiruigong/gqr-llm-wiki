"""Read and write sources/registry.json."""
import json
from datetime import datetime, timezone
from pathlib import Path

REGISTRY_PATH = Path("sources/registry.json")


def load() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def save(data: dict) -> None:
    REGISTRY_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def find(source_id: str) -> dict | None:
    data = load()
    for entry in data["sources"]:
        if entry["id"] == source_id:
            return entry
    return None


def upsert(source_id: str, source_type: str, path_or_url: str,
           affected_pages: list[str], status: str, mode: str) -> None:
    data = load()
    entry = {
        "id": source_id,
        "type": source_type,
        "path_or_url": path_or_url,
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "affected_pages": affected_pages,
        "status": status,
        "mode": mode,
    }
    existing = [e for e in data["sources"] if e["id"] != source_id]
    existing.append(entry)
    data["sources"] = existing
    save(data)


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 2:
        result = find(sys.argv[1])
        if result:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("NOT_FOUND")
