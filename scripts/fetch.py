"""Fetch content from URLs or local files, return plain text."""
import sys
import hashlib
from pathlib import Path


def fetch_url(url: str) -> str:
    import requests
    from readability import Document

    response = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    doc = Document(response.text)
    import html2text
    h = html2text.HTML2Text()
    h.ignore_links = False
    return h.handle(doc.summary())


def fetch_file(path: str) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"文件不存在: {path}")

    if p.suffix.lower() == ".pdf":
        import pdfplumber
        text = []
        with pdfplumber.open(p) as pdf:
            for page in pdf.pages:
                text.append(page.extract_text() or "")
        return "\n".join(text)

    return p.read_text(encoding="utf-8")


def compute_id(source: str) -> str:
    return hashlib.sha256(source.encode()).hexdigest()[:8]


def fetch(source: str) -> tuple[str, str]:
    """Return (content, source_id)."""
    source_id = compute_id(source)
    if source.startswith("http://") or source.startswith("https://"):
        content = fetch_url(source)
    else:
        content = fetch_file(source)
    return content, source_id


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/fetch.py <url_or_path>", file=sys.stderr)
        sys.exit(1)
    content, source_id = fetch(sys.argv[1])
    print(f"SOURCE_ID:{source_id}")
    print(content)
