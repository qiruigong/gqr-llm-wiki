import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta


@pytest.fixture(autouse=True)
def clean_registry(tmp_path, monkeypatch):
    registry_file = tmp_path / "registry.json"
    sources = [
        {
            "id": "aabbccdd",
            "type": "url",
            "path_or_url": "https://example.com/article",
            "ingested_at": datetime.now(timezone.utc).isoformat(),
            "affected_pages": ["page.md"],
            "status": "ingested",
            "mode": "persona",
            "content_hash": "oldhash1",
            "last_modified": "Mon, 01 Jan 2026 00:00:00 GMT",
            "etag": '"old-etag"',
        },
        {
            "id": "11223344",
            "type": "url",
            "path_or_url": "https://example.com/no-headers",
            "ingested_at": datetime.now(timezone.utc).isoformat(),
            "affected_pages": ["page2.md"],
            "status": "ingested",
            "mode": "persona",
            "content_hash": "oldhash2",
            "last_modified": None,
            "etag": None,
        },
        {
            "id": "stale0000",
            "type": "url",
            "path_or_url": "https://example.com/old",
            "ingested_at": (datetime.now(timezone.utc) - timedelta(days=400)).isoformat(),
            "affected_pages": [],
            "status": "ingested",
            "mode": "persona",
            "content_hash": None,
            "last_modified": None,
            "etag": None,
        },
    ]
    registry_file.write_text(
        json.dumps({"sources": sources}, ensure_ascii=False), encoding="utf-8"
    )
    monkeypatch.setattr("scripts.registry.REGISTRY_PATH", registry_file)
    monkeypatch.setattr("scripts.check_updates.REGISTRY_PATH", registry_file)
    return registry_file


def make_head_response(etag=None, last_modified=None, status_code=200):
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = {}
    if etag:
        resp.headers["ETag"] = etag
    if last_modified:
        resp.headers["Last-Modified"] = last_modified
    resp.raise_for_status = MagicMock()
    return resp


def make_get_response(content="page content", status_code=200):
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = content
    resp.content = content.encode()
    resp.raise_for_status = MagicMock()
    return resp


def test_unchanged_by_etag():
    from scripts.check_updates import check_url
    head_resp = make_head_response(etag='"old-etag"')
    with patch("requests.head", return_value=head_resp):
        result = check_url("aabbccdd", "https://example.com/article")
    assert result == ("UNCHANGED", "")


def test_unchanged_by_last_modified():
    from scripts.check_updates import check_url
    head_resp = make_head_response(last_modified="Mon, 01 Jan 2026 00:00:00 GMT")
    with patch("requests.head", return_value=head_resp):
        result = check_url("aabbccdd", "https://example.com/article")
    assert result == ("UNCHANGED", "")


def test_changed_by_etag():
    from scripts.check_updates import check_url
    head_resp = make_head_response(etag='"new-etag"')
    get_resp = make_get_response("new content")
    with patch("requests.head", return_value=head_resp), \
         patch("requests.get", return_value=get_resp):
        result = check_url("aabbccdd", "https://example.com/article")
    assert result == ("CHANGED", "")


def test_unchanged_by_hash_when_no_headers():
    from scripts.check_updates import check_url
    import hashlib
    content = "same content"
    content_hash = hashlib.sha256(content.encode()).hexdigest()[:8]

    import scripts.registry as reg
    reg.update_status("11223344", "ingested", content_hash=content_hash)

    head_resp = make_head_response()
    get_resp = make_get_response(content)
    with patch("requests.head", return_value=head_resp), \
         patch("requests.get", return_value=get_resp):
        result = check_url("11223344", "https://example.com/no-headers")
    assert result == ("UNCHANGED", "")


def test_changed_by_hash_when_no_headers():
    from scripts.check_updates import check_url
    head_resp = make_head_response()
    get_resp = make_get_response("completely new content xyz")
    with patch("requests.head", return_value=head_resp), \
         patch("requests.get", return_value=get_resp):
        result = check_url("11223344", "https://example.com/no-headers")
    assert result == ("CHANGED", "")


def test_error_on_request_failure():
    from scripts.check_updates import check_url
    import requests
    with patch("requests.head", side_effect=requests.RequestException("timeout")):
        result = check_url("aabbccdd", "https://example.com/article")
    assert result[0] == "ERROR"


def test_scan_excludes_entries_older_than_365_days():
    from scripts.check_updates import get_candidates
    candidates = get_candidates()
    ids = [c["id"] for c in candidates]
    assert "stale0000" not in ids
    assert "aabbccdd" in ids


def test_error_format_in_scan_output(capsys):
    from scripts.check_updates import scan
    import requests
    with patch("requests.head", side_effect=requests.RequestException("timeout")):
        scan()
    captured = capsys.readouterr()
    lines = [l for l in captured.out.strip().split("\n") if l.startswith("ERROR")]
    assert len(lines) > 0
    # 格式应为 ERROR:<id>:<url>:<reason>
    parts = lines[0].split(":")
    assert parts[0] == "ERROR"
    assert parts[1] == "aabbccdd"   # 第一个候选条目的 id
