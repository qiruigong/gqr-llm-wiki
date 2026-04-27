"""Wiki health check: find contradictions, orphan pages, and knowledge gaps."""
import os
import json
from pathlib import Path
from datetime import datetime, timezone
import anthropic
from dotenv import load_dotenv

load_dotenv()

WIKI_PAGES_DIR = Path("wiki/pages")
REGISTRY_PATH = Path("sources/registry.json")
REPORT_PATH = Path("wiki/lint-report.md")


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
            f"[[{stem}]]" in content
            for name, content in pages.items()
            if name != page_name
        )
        if not referenced:
            orphans.append(page_name)
    return orphans


def run_lint():
    pages = load_all_pages()
    if not pages:
        print("Wiki 为空，无需 lint。请先运行 /wiki-ingest。")
        return

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    registry = load_registry()
    orphans = find_orphan_pages(pages)

    pages_summary = "\n\n".join(
        f"=== {name} ===\n{content[:2000]}" for name, content in pages.items()
    )

    prompt = f"""你是一个 Wiki 健康检查助手。请检查以下 Wiki 页面，找出：

1. **矛盾**：同一概念在不同页面中描述冲突（列出具体页面和冲突内容）
2. **数据缺口**：某个概念被多次提及但没有专属页面（列出概念名称）
3. **建议**：改善 Wiki 质量的具体建议

已检测到的孤立页面（无其他页面链接到它们）：
{chr(10).join(f'- {p}' for p in orphans) if orphans else '无'}

Wiki 页面内容：
{pages_summary}

请用中文输出一份结构化的健康报告，格式为 Markdown。"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    report_content = f"""# Wiki 健康报告

**生成时间：** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
**检查页面数：** {len(pages)}
**孤立页面数：** {len(orphans)}

---

{message.content[0].text}
"""

    REPORT_PATH.write_text(report_content, encoding="utf-8")
    print(f"报告已保存到 {REPORT_PATH}")
    print(f"检查了 {len(pages)} 个页面，发现 {len(orphans)} 个孤立页面")


if __name__ == "__main__":
    run_lint()
