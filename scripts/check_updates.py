"""Detect updates for ingested URL sources via HTTP headers + hash fallback."""
import re
import sys
import hashlib
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import scripts.registry as registry
from scripts.fetch import fetch_url

REGISTRY_PATH = registry.REGISTRY_PATH
MAX_AGE_DAYS = 365


def _norm_header(s: str) -> str:
    return re.sub(r'\s+', ' ', s.strip())


def compute_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()[:8]


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


def check_url(source_id: str, url: str) -> tuple[str, str]:
    """Return (status, reason) where status is 'CHANGED', 'UNCHANGED', or 'ERROR'."""
    entry = registry.find(source_id) or {}

    try:
        head_resp = requests.head(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"},
                                  allow_redirects=True)
        head_resp.raise_for_status()
    except requests.RequestException as e:
        return ("ERROR", str(e))

    stored_etag = entry.get("etag")
    stored_lm = entry.get("last_modified")
    resp_etag = head_resp.headers.get("ETag")
    resp_lm = head_resp.headers.get("Last-Modified")

    # 若双方都有 ETag，ETag 单独决定结果，不再 fallback 到 Last-Modified
    if resp_etag and stored_etag:
        if _norm_header(resp_etag) == _norm_header(stored_etag):
            return ("UNCHANGED", "")
        # ETag 不一致，直接进入 hash 检查，不看 Last-Modified
    elif resp_lm and stored_lm:
        if _norm_header(resp_lm) == _norm_header(stored_lm):
            return ("UNCHANGED", "")
        # Last-Modified 不一致，进入 hash 检查

    try:
        new_content = fetch_url(url)
    except Exception as e:
        return ("ERROR", str(e))

    new_hash = compute_hash(new_content)
    stored_hash = entry.get("content_hash")

    if stored_hash and new_hash == stored_hash:
        registry.update_status(source_id, "ingested",
                                last_modified=resp_lm,
                                etag=resp_etag)
        return ("UNCHANGED", "")

    registry.update_status(source_id, "pending_update",
                            content_hash=new_hash,
                            last_modified=resp_lm,
                            etag=resp_etag)
    return ("CHANGED", "")


def scan(specific_url: str | None = None) -> None:
    candidates = get_candidates()

    if specific_url:
        all_entries = registry.load()["sources"]
        in_registry = any(e["path_or_url"] == specific_url for e in all_entries)
        candidates = [c for c in candidates if c["path_or_url"] == specific_url]
        if not candidates:
            if not in_registry:
                print(f"ERROR:NONE:{specific_url}:NOT_IN_REGISTRY")
            else:
                print(f"ERROR:NONE:{specific_url}:NOT_ELIGIBLE:not ingested or ingested over 365 days ago")
            return

    for entry in candidates:
        source_id = entry["id"]
        url = entry["path_or_url"]
        status, reason = check_url(source_id, url)
        if status == "CHANGED":
            print(f"CHANGED:{source_id}:{url}")
        elif status == "UNCHANGED":
            print(f"UNCHANGED:{source_id}:{url}")
        else:
            print(f"ERROR:{source_id}:{url}:{reason}")


if __name__ == "__main__":
    specific = sys.argv[1] if len(sys.argv) > 1 else None
    scan(specific)
