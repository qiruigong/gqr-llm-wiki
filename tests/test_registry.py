import json
import pytest
from pathlib import Path
from unittest.mock import patch


@pytest.fixture(autouse=True)
def clean_registry(tmp_path, monkeypatch):
    registry_file = tmp_path / "registry.json"
    registry_file.write_text('{"sources": []}', encoding="utf-8")
    monkeypatch.setattr("scripts.registry.REGISTRY_PATH", registry_file)
    return registry_file


def test_upsert_stores_new_fields():
    import scripts.registry as reg
    reg.upsert(
        source_id="abc12345",
        source_type="url",
        path_or_url="https://example.com",
        affected_pages=["page.md"],
        status="ingested",
        mode="persona",
        content_hash="deadbeef",
        last_modified="Mon, 01 Jan 2026 00:00:00 GMT",
        etag='"abc"',
    )
    result = reg.find("abc12345")
    assert result["content_hash"] == "deadbeef"
    assert result["last_modified"] == "Mon, 01 Jan 2026 00:00:00 GMT"
    assert result["etag"] == '"abc"'


def test_upsert_preserves_existing_fields_when_not_passed():
    import scripts.registry as reg
    reg.upsert(
        source_id="abc12345",
        source_type="url",
        path_or_url="https://example.com",
        affected_pages=["page.md"],
        status="ingested",
        mode="persona",
        content_hash="deadbeef",
        last_modified="Mon, 01 Jan 2026 00:00:00 GMT",
        etag='"abc"',
    )
    reg.upsert(
        source_id="abc12345",
        source_type="url",
        path_or_url="https://example.com",
        affected_pages=["page.md"],
        status="ingested",
        mode="persona",
    )
    result = reg.find("abc12345")
    assert result["content_hash"] == "deadbeef"
    assert result["etag"] == '"abc"'


def test_update_status():
    import scripts.registry as reg
    reg.upsert(
        source_id="abc12345",
        source_type="url",
        path_or_url="https://example.com",
        affected_pages=[],
        status="ingested",
        mode="persona",
    )
    reg.update_status("abc12345", "pending_update",
                      content_hash="newhash1",
                      last_modified="Tue, 02 Jan 2026 00:00:00 GMT",
                      etag='"new"')
    result = reg.find("abc12345")
    assert result["status"] == "pending_update"
    assert result["content_hash"] == "newhash1"
    assert result["last_modified"] == "Tue, 02 Jan 2026 00:00:00 GMT"
    assert result["etag"] == '"new"'


def test_update_status_raises_for_missing_id():
    import scripts.registry as reg
    with pytest.raises(KeyError):
        reg.update_status("does_not_exist", "pending")


def test_list_by_status():
    import scripts.registry as reg
    reg.upsert("id1", "url", "https://a.com", [], "ingested", "persona")
    reg.upsert("id2", "url", "https://b.com", [], "pending", "persona")
    reg.upsert("id3", "url", "https://c.com", [], "ingested", "persona")
    results = reg.list_by_status("ingested")
    ids = [r["id"] for r in results]
    assert "id1" in ids
    assert "id3" in ids
    assert "id2" not in ids


def test_find_returns_none_when_registry_missing(tmp_path, monkeypatch):
    import scripts.registry as reg
    missing = tmp_path / "no_registry.json"
    monkeypatch.setattr("scripts.registry.REGISTRY_PATH", missing)
    assert reg.find("any_id") is None


def test_list_by_status_returns_empty_when_registry_missing(tmp_path, monkeypatch):
    import scripts.registry as reg
    missing = tmp_path / "no_registry.json"
    monkeypatch.setattr("scripts.registry.REGISTRY_PATH", missing)
    assert reg.list_by_status("ingested") == []
