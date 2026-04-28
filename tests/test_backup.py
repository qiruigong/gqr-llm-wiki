import zipfile
from pathlib import Path
from scripts.backup import create_backup


def _make_knowledge(tmp_path: Path) -> Path:
    """Create a minimal knowledge base under tmp_path (acts as project root)."""
    (tmp_path / "wiki" / "pages").mkdir(parents=True)
    (tmp_path / "wiki" / "index.md").write_text("# index")
    (tmp_path / "sources").mkdir()
    (tmp_path / "sources" / "registry.json").write_text("{}")
    (tmp_path / "persona.md").write_text("# persona")
    return tmp_path


def test_zip_contains_knowledge_prefix(tmp_path):
    project_root = _make_knowledge(tmp_path / "project")
    out_dir = tmp_path / "out"
    backup_path, _, _items = create_backup(str(out_dir), project_root=project_root)
    with zipfile.ZipFile(backup_path) as zf:
        names = zf.namelist()
    assert all(n.startswith("knowledge/") for n in names)


def test_zip_contains_all_three_items(tmp_path):
    project_root = _make_knowledge(tmp_path / "project")
    out_dir = tmp_path / "out"
    backup_path, _, _items = create_backup(str(out_dir), project_root=project_root)
    with zipfile.ZipFile(backup_path) as zf:
        names = zf.namelist()
    assert any("wiki/index.md" in n for n in names)
    assert any("sources/registry.json" in n for n in names)
    assert "knowledge/persona.md" in names


def test_zip_excludes_project_framework_files(tmp_path):
    project_root = _make_knowledge(tmp_path / "project")
    # Add framework files that should NOT be included
    (project_root / "scripts").mkdir()
    (project_root / "scripts" / "backup.py").write_text("# script")
    (project_root / "README.md").write_text("# readme")
    out_dir = tmp_path / "out"
    backup_path, _, _items = create_backup(str(out_dir), project_root=project_root)
    with zipfile.ZipFile(backup_path) as zf:
        names = zf.namelist()
    assert not any("scripts/" in n for n in names)
    assert "README.md" not in names


def test_missing_sources_skipped_silently(tmp_path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / "wiki" / "pages").mkdir(parents=True)
    (project_root / "wiki" / "index.md").write_text("# index")
    # No sources/, no persona.md
    out_dir = tmp_path / "out"
    backup_path, _, backed_up = create_backup(str(out_dir), project_root=project_root)
    assert backup_path.exists()
    assert "sources" not in backed_up
    assert "persona.md" not in backed_up


def test_zip_filename_uses_knowledge_prefix(tmp_path):
    project_root = _make_knowledge(tmp_path / "project")
    out_dir = tmp_path / "out"
    backup_path, _, _items = create_backup(str(out_dir), project_root=project_root)
    assert backup_path.name.startswith("llm-wiki-knowledge-")
