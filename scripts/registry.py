"""Read and write sources/registry.json."""
import json
from datetime import datetime, timezone
from pathlib import Path

REGISTRY_PATH = Path("sources/registry.json")


def load() -> dict:
    try:
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise FileNotFoundError(f"Registry file not found: {REGISTRY_PATH}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Registry file is corrupted: {e}") from e


def save(data: dict) -> None:
    REGISTRY_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def find(source_id: str) -> dict | None:
    data = load()
    for entry in data["sources"]:
        if entry["id"] == source_id:
            return entry
    return None


def list_by_status(status: str) -> list[dict]:
    data = load()
    return [e for e in data["sources"] if e.get("status") == status]


def upsert(
    source_id: str,
    source_type: str,
    path_or_url: str,
    affected_pages: list[str],
    status: str,
    mode: str,
    content_hash: str | None = None,
    last_modified: str | None = None,
    etag: str | None = None,
) -> None:
    data = load()
    existing_entry = next((e for e in data["sources"] if e["id"] == source_id), {})
    entry = {
        "id": source_id,
        "type": source_type,
        "path_or_url": path_or_url,
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "affected_pages": affected_pages,
        "status": status,
        "mode": mode,
        "content_hash": content_hash if content_hash is not None else existing_entry.get("content_hash"),
        "last_modified": last_modified if last_modified is not None else existing_entry.get("last_modified"),
        "etag": etag if etag is not None else existing_entry.get("etag"),
    }
    others = [e for e in data["sources"] if e["id"] != source_id]
    others.append(entry)
    data["sources"] = others
    save(data)


def update_status(
    source_id: str,
    status: str,
    content_hash: str | None = None,
    last_modified: str | None = None,
    etag: str | None = None,
) -> None:
    data = load()
    for entry in data["sources"]:
        if entry["id"] == source_id:
            entry["status"] = status
            if content_hash is not None:
                entry["content_hash"] = content_hash
            if last_modified is not None:
                entry["last_modified"] = last_modified
            if etag is not None:
                entry["etag"] = etag
            break
    else:
        raise KeyError(f"source_id '{source_id}' not found in registry")
    save(data)


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 2:
        result = find(sys.argv[1])
        if result:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("NOT_FOUND")
