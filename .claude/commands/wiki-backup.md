# /wiki-backup

将知识库数据（`wiki/`、`sources/`、`persona.md`）打包备份到指定目录（默认备份到云盘同步目录）。

**用法：**
- `/wiki-backup` — 备份到 persona.md 中配置的默认备份目录
- `/wiki-backup <目录路径>` — 备份到指定目录

---

## 执行前规划

在开始执行前，用 TodoWrite 列出本次任务的具体步骤，等待用户确认后再执行。每完成一步立即用 TaskUpdate 标记完成。

## 执行步骤

### 第一步：确定备份目标目录

若用户提供了目录路径，使用该路径。

否则，读取 `persona.md` 中 `## 备份目录` 章节的路径。
若该章节不存在，询问用户：
> 请提供备份目标目录路径（建议使用云盘同步目录，如 OneDrive 或坚果云文件夹）：

等待用户输入后继续。

### 第二步：执行备份

运行：
```bash
python scripts/backup.py <目标目录>
```

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
