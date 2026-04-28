# wiki-backup prompt

将知识库数据（`wiki/`、`sources/`、`persona.md`）打包为带时间戳的 ZIP 文件。

**参数：**
- `TARGET_DIR`：备份目标目录（可选，默认读取 `persona.md` 中 `## 备份目录` 章节的路径）

---

## 执行步骤

### 第一步：确定备份目标目录

若用户提供了 `TARGET_DIR`，使用该路径。

否则，读取 `persona.md` 中 `## 备份目录` 章节的路径。若章节不存在，询问用户提供路径。

### 第二步：执行备份

执行 shell 命令：`python scripts/backup.py <TARGET_DIR>`

### 第三步：汇报结果

```
✅ 知识库备份完成：<备份文件路径>（<大小> MB）
已备份：<backup.py 输出的项目列表>

恢复到新机器：
1. git clone <仓库地址> 并运行 uv sync（获取项目框架）
2. 解压此 ZIP，将 knowledge/ 内的三项复制到项目根目录：
   - knowledge/wiki/       → wiki/
   - knowledge/sources/    → sources/
   - knowledge/persona.md  → persona.md
```
