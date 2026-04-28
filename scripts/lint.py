"""Wiki structural scan: find orphan pages and pages missing required sections."""
import json
from pathlib import Path

WIKI_PAGES_DIR = Path(__file__).parent.parent / "wiki" / "pages"
REGISTRY_PATH = Path(__file__).parent.parent / "sources" / "registry.json"


def load_all_pages() -> dict[str, str]:
    pages = {}
    for p in WIKI_PAGES_DIR.glob("*.md"):
        pages[p.name] = p.read_text(encoding="utf-8")
    return pages


def load_registry() -> list[dict]:
    if not REGISTRY_PATH.exists():
        return []
    data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return data.get("sources", [])


def find_orphan_pages(pages: dict[str, str]) -> list[str]:
    orphans = []
    for page_name in pages:
        stem = Path(page_name).stem
        referenced = any(
            f"[[{stem}]]" in content or f"[[{stem}|" in content
            for name, content in pages.items()
            if name != page_name
        )
        if not referenced:
            orphans.append(page_name)
    return orphans


def find_missing_sections(pages: dict[str, str]) -> dict[str, list[str]]:
    # Must stay in sync with the page format spec in CLAUDE.md
    required = ["## 摘要", "## 关键要点", "## 来源引用"]
    missing = {}
    for name, content in pages.items():
        absent = [s for s in required if s not in content]
        if absent:
            missing[name] = absent
    return missing


def find_pages_without_frontmatter(pages: dict[str, str]) -> list[str]:
    return [name for name, content in pages.items() if not content.startswith("---")]


def run_scan() -> dict:
    pages = load_all_pages()
    return {
        "total_pages": len(pages),
        "orphan_pages": find_orphan_pages(pages),
        "missing_sections": find_missing_sections(pages),
        "missing_frontmatter": find_pages_without_frontmatter(pages),
        "page_names": list(pages.keys()),
    }


if __name__ == "__main__":
    result = run_scan()
    if result["total_pages"] == 0:
        print("EMPTY_WIKI")
    else:
        print(f"TOTAL:{result['total_pages']}")
        print(f"ORPHANS:{','.join(result['orphan_pages']) if result['orphan_pages'] else 'none'}")
        for page, sections in result["missing_sections"].items():
            print(f"MISSING_SECTIONS:{page}:{','.join(sections)}")
        for page in result["missing_frontmatter"]:
            print(f"MISSING_FRONTMATTER:{page}")
