# 知识库备份与迁移重设计 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `/wiki-backup` 从备份整个项目改为只备份知识库数据（wiki/、sources/、persona.md），ZIP 内加 `knowledge/` 前缀，并同步更新 command 提示和 README 迁移说明。

**Architecture:** `backup.py` 改为只遍历三个知识库路径（`wiki/`、`sources/`、`persona.md`），写入 ZIP 时统一加 `knowledge/` 前缀；缺失的路径静默跳过并在输出中标注。`/wiki-backup` command 的完成提示更新为两阶段恢复流程。README 的迁移章节拆分为"项目框架（git clone）"和"知识库（ZIP 解压）"两个独立步骤。

**Tech Stack:** Python 3、zipfile（标准库）、pytest、Markdown

---

## 文件结构

| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `scripts/backup.py` | 打包范围改为知识库三项，ZIP 加 `knowledge/` 前缀，文件名改 |
| 新建 | `tests/test_backup.py` | backup.py 的单元测试 |
| 修改 | `.claude/commands/wiki-backup.md` | 完成提示改为两阶段恢复说明 |
| 修改 | `README.md` | 目录结构注释 + 迁移章节重写 |

---

### Task 1：改写 backup.py，只打包知识库数据

**Files:**
- Modify: `C:\SAPDevelop\kaparthy\scripts\backup.py`
- Test: `C:\SAPDevelop\kaparthy\tests\test_backup.py`

- [ ] **Step 1：写失败测试**

新建 `tests/test_backup.py`：

```python
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
```

- [ ] **Step 2：运行测试，确认失败**

```bash
uv run pytest tests/test_backup.py -v
```

预期：全部 FAIL（`create_backup` 签名不匹配、ZIP 结构不符）

- [ ] **Step 3：改写 backup.py**

```python
"""Create a timestamped zip of knowledge base data (wiki/, sources/, persona.md)."""
import sys
import zipfile
from pathlib import Path
from datetime import datetime, timezone

KNOWLEDGE_ITEMS = ["wiki", "sources", "persona.md"]


def create_backup(
    target_dir: str, project_root: Path | None = None
) -> tuple[Path, float, list[str]]:
    if project_root is None:
        project_root = Path(__file__).parent.parent

    target = Path(target_dir)
    target.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_name = f"llm-wiki-knowledge-{timestamp}.zip"
    backup_path = target / backup_name

    backed_up: list[str] = []

    with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for item_name in KNOWLEDGE_ITEMS:
            item_path = project_root / item_name
            if not item_path.exists():
                continue
            if item_path.is_file():
                zf.write(item_path, f"knowledge/{item_name}")
                backed_up.append(item_name)
            elif item_path.is_dir():
                for file in item_path.rglob("*"):
                    if file.is_file():
                        rel = file.relative_to(project_root)
                        zf.write(file, f"knowledge/{rel}")
                backed_up.append(item_name)

    size_mb = backup_path.stat().st_size / (1024 * 1024)
    return backup_path, size_mb, backed_up


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/backup.py <target_directory>", file=sys.stderr)
        sys.exit(1)
    path, size, items = create_backup(sys.argv[1])
    items_str = "、".join(items) if items else "（无内容）"
    print(f"知识库备份完成：{path}（{size:.1f} MB）")
    print(f"已备份：{items_str}")
```

- [ ] **Step 4：运行测试，确认通过**

```bash
uv run pytest tests/test_backup.py -v
```

预期：5 个测试全部 PASS

- [ ] **Step 5：确认旧测试未受影响**

```bash
uv run pytest --tb=short -q
```

预期：全部已有测试仍 PASS

- [ ] **Step 6：Commit**

```bash
git -C "C:\SAPDevelop\kaparthy" add scripts/backup.py tests/test_backup.py
git -C "C:\SAPDevelop\kaparthy" commit -m "feat: backup only knowledge data with knowledge/ zip prefix

backup.py now packages only wiki/, sources/, persona.md.
ZIP entries prefixed with knowledge/ for safe extraction.
Filename changed to llm-wiki-knowledge-*.zip.
Missing items are skipped silently and reported in output."
```

---

### Task 2：更新 /wiki-backup command

**Files:**
- Modify: `C:\SAPDevelop\kaparthy\.claude\commands\wiki-backup.md`

- [ ] **Step 1：读取现有文件，定位第三步"汇报结果"**

读取 `.claude/commands/wiki-backup.md`，找到"### 第三步：汇报结果"章节（当前约第 30-38 行）。

- [ ] **Step 2：替换第三步内容**

将"### 第三步：汇报结果"章节替换为：

```markdown
### 第三步：汇报结果

向用户展示备份结果：
> ✅ 知识库备份完成：`<备份文件路径>`（`<大小>` MB）
> 已备份：`<backup.py 输出的项目列表>`
>
> **恢复到新机器：**
> 1. `git clone <仓库地址>` 并运行 `uv sync`（获取项目框架）
> 2. 解压此 ZIP，将 `knowledge/` 内的三项复制到项目根目录：
>    - `knowledge/wiki/`       → `<项目根>/wiki/`
>    - `knowledge/sources/`    → `<项目根>/sources/`
>    - `knowledge/persona.md`  → `<项目根>/persona.md`
```

- [ ] **Step 3：验证文件内容**

读取 `.claude/commands/wiki-backup.md`，确认：
- 包含"知识库备份完成"字样
- 包含两阶段恢复说明（git clone + ZIP 解压）
- 不再包含"按照 README.md 中的'在新机器上恢复'章节操作"旧提示

- [ ] **Step 4：Commit**

```bash
git -C "C:\SAPDevelop\kaparthy" add .claude/commands/wiki-backup.md
git -C "C:\SAPDevelop\kaparthy" commit -m "docs: update wiki-backup command with two-phase restore instructions"
```

---

### Task 3：更新 README.md

**Files:**
- Modify: `C:\SAPDevelop\kaparthy\README.md`

- [ ] **Step 1：更新目录结构中 wiki/ 和 sources/ 的注释**

定位 README.md 第 25 行附近，将：
```
├── wiki/                  # ⚠️ 以下内容已 gitignore，属于个人知识积累
```
改为：
```
├── wiki/                  # ⚠️ 知识库数据，已 gitignore，用 /wiki-backup 备份
```

将：
```
├── sources/               # ⚠️ 以下内容已 gitignore，属于个人知识积累
```
改为：
```
├── sources/               # ⚠️ 知识库数据，已 gitignore，用 /wiki-backup 备份
```

- [ ] **Step 2：将 `/wiki-backup` 命令参考章节的描述更新**

定位 README.md 中"### `/wiki-backup` — 备份项目"章节（约第 222-242 行）：

将：
```
将整个项目打包为带时间戳的 ZIP 文件。
```
改为：
```
将知识库数据（`wiki/`、`sources/`、`persona.md`）打包为带时间戳的 ZIP 文件。
```

将：
```
备份内容包含所有文件，自动排除 `.env`（含密钥）和 `.git/`。
```
改为：
```
仅备份知识库数据，项目框架（脚本、commands 等）通过 git 管理，无需重复备份。
```

- [ ] **Step 3：重写"在新机器上恢复"章节**

定位 README.md 中"## 在新机器上恢复"章节（约第 267-273 行），将整个章节替换为：

```markdown
## 在新机器上部署

### 第一步：部署项目框架（通过 git）

```bash
git clone https://github.com/<你的用户名>/kaparthy.git
cd kaparthy
uv sync
```

### 第二步：恢复知识库（通过备份文件，可选）

若有 `/wiki-backup` 导出的 ZIP，解压后将 `knowledge/` 内三项复制到项目根目录：

- `knowledge/wiki/`       → `wiki/`
- `knowledge/sources/`    → `sources/`
- `knowledge/persona.md`  → `persona.md`

若无备份（全新部署），跳过此步，从空 wiki 开始：

```bash
cp persona.template.md persona.md
```
```

- [ ] **Step 4：验证三处改动均正确**

读取 README.md，逐一确认：
- 第 25 行附近：`wiki/` 注释含"知识库数据"
- 第 31 行附近：`sources/` 注释含"知识库数据"
- `/wiki-backup` 章节：描述为"知识库数据"，不含"所有文件"
- 迁移章节标题为"在新机器上部署"，含两个独立步骤

- [ ] **Step 5：Commit**

```bash
git -C "C:\SAPDevelop\kaparthy" add README.md
git -C "C:\SAPDevelop\kaparthy" commit -m "docs: clarify project framework vs knowledge base migration in README"
```

---

### Task 4：推送到 GitHub

- [ ] **Step 1：确认状态**

```bash
git -C "C:\SAPDevelop\kaparthy" status
git -C "C:\SAPDevelop\kaparthy" log --oneline -5
```

预期：工作区干净，最近 3 条 commit 包含本次三个任务的变更。

- [ ] **Step 2：推送**

```bash
git -C "C:\SAPDevelop\kaparthy" push origin main
```

- [ ] **Step 3：确认推送成功**

```bash
git -C "C:\SAPDevelop\kaparthy" log --oneline origin/main -5
```

预期：远端 HEAD 与本地一致。
