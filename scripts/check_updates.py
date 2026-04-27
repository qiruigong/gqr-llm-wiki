"""Detect updates for ingested URL sources via HTTP headers + hash fallback."""
import sys
import hashlib
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import scripts.registry as registry

REGISTRY_PATH = registry.REGISTRY_PATH
MAX_AGE_DAYS = 365


def compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:8]


def get_candidates() -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)
    data = registry.load()
    result = []
    for entry in data["sources"]:
        if entry.get("type") != "url":
            continue
        if entry.get("status") != "ingested":
            continue
        try:
            ingested_at = datetime.fromisoformat(entry["ingested_at"])
        except (KeyError, ValueError):
            continue
        if ingested_at < cutoff:
            continue
        result.append(entry)
    return result


def check_url(source_id: str, url: str) -> str:
    """Return 'CHANGED', 'UNCHANGED', or 'ERROR:<reason>'."""
    entry = registry.find(source_id) or {}

    try:
        head_resp = requests.head(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"},
                                  allow_redirects=True)
        head_resp.raise_for_status()
    except requests.RequestException as e:
        return f"ERROR:{e}"

    stored_etag = entry.get("etag")
    stored_lm = entry.get("last_modified")
    resp_etag = head_resp.headers.get("ETag")
    resp_lm = head_resp.headers.get("Last-Modified")

    if resp_etag and stored_etag and resp_etag == stored_etag:
        return "UNCHANGED"

    if resp_lm and stored_lm and resp_lm == stored_lm:
        return "UNCHANGED"

    try:
        get_resp = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        get_resp.raise_for_status()
    except requests.RequestException as e:
        return f"ERROR:{e}"

    new_hash = compute_hash(get_resp.text)
    stored_hash = entry.get("content_hash")

    if stored_hash and new_hash == stored_hash:
        registry.update_status(source_id, "ingested",
                                last_modified=resp_lm,
                                etag=resp_etag)
        return "UNCHANGED"

    registry.update_status(source_id, "pending_update",
                            content_hash=new_hash,
                            last_modified=resp_lm,
                            etag=resp_etag)
    return "CHANGED"


def scan(specific_url: str | None = None) -> None:
    candidates = get_candidates()

    if specific_url:
        candidates = [c for c in candidates if c["path_or_url"] == specific_url]
        if not candidates:
            print(f"ERROR:NOT_IN_REGISTRY:{specific_url}")
            return

    for entry in candidates:
        source_id = entry["id"]
        url = entry["path_or_url"]
        result = check_url(source_id, url)
        if result == "CHANGED":
            print(f"CHANGED:{source_id}:{url}")
        elif result == "UNCHANGED":
            print(f"UNCHANGED:{source_id}:{url}")
        else:
            reason = result[len("ERROR:"):]
            print(f"ERROR:{source_id}:{url}:{reason}")


if __name__ == "__main__":
    specific = sys.argv[1] if len(sys.argv) > 1 else None
    scan(specific)
