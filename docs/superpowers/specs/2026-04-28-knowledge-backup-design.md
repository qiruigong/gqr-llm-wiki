# 知识库备份与迁移重设计

**日期：** 2026-04-28  
**状态：** 待实现

---

## 背景

当前 `/wiki-backup` 打包整个项目（脚本、commands、README 等），而这些文件已由 GitHub 仓库管理，重复备份浪费空间且语义不清。项目框架和知识库是两类不同性质的数据，迁移路径不同，应明确区分：

| 类别 | 内容 | 迁移方式 |
|------|------|----------|
| 项目框架 | 脚本、commands、CLAUDE.md、pyproject.toml 等 | `git clone` |
| 知识库数据 | `wiki/`、`sources/`、`persona.md` | `/wiki-backup` 导出的 ZIP |

---

## 目标

1. `backup.py` 只打包知识库数据，ZIP 内加一层 `knowledge/` 前缀
2. ZIP 文件名改为 `llm-wiki-knowledge-*.zip`
3. `/wiki-backup` command 的完成提示说明两阶段恢复流程
4. README "在新机器上部署"章节拆分为两个独立步骤

---

## backup.py 改动

**打包范围（仅这三项）：**
- `wiki/`（含 index.md、log.md、pages/、assets/）
- `sources/`（含 registry.json、files/）
- `persona.md`

**ZIP 内部结构：**
```
llm-wiki-knowledge-20260428_103000.zip
└── knowledge/
    ├── wiki/
    │   ├── index.md
    │   ├── log.md
    │   ├── pages/
    │   └── assets/
    ├── sources/
    │   ├── registry.json
    │   └── files/
    └── persona.md
```

**文件名格式：** `llm-wiki-knowledge-{YYYYMMDD_HHMMSS}.zip`

**缺失文件处理：** 若某项不存在（如用户尚未创建 `wiki/`），静默跳过，不报错。备份完成后输出实际打包了哪些项。

---

## /wiki-backup command 改动

备份完成提示改为：

```
✅ 知识库备份完成：`<路径>`（`<大小>` MB）
已备份：wiki/、sources/、persona.md

恢复到新机器：
1. git clone <仓库地址> 并运行 uv sync（获取项目框架）
2. 解压此 ZIP，将 knowledge/ 内的三项复制到项目根目录：
   - knowledge/wiki/       → <项目根>/wiki/
   - knowledge/sources/    → <项目根>/sources/
   - knowledge/persona.md  → <项目根>/persona.md
```

---

## README 改动

### 1. 目录结构注释

`wiki/` 和 `sources/` 的注释从"属于个人知识积累"改为：

```
├── wiki/                  # ⚠️ 知识库数据，已 gitignore，用 /wiki-backup 备份
├── sources/               # ⚠️ 知识库数据，已 gitignore，用 /wiki-backup 备份
```

### 2. "在新机器上恢复"→ 改为"在新机器上部署"

```markdown
## 在新机器上部署

### 第一步：部署项目框架（通过 git）

git clone <仓库地址>
cd <目录>
uv sync

### 第二步：恢复知识库（通过备份文件，可选）

若有 /wiki-backup 导出的 ZIP，解压后将 knowledge/ 内三项复制到项目根目录：
- knowledge/wiki/       → wiki/
- knowledge/sources/    → sources/
- knowledge/persona.md  → persona.md

若无备份（全新部署），跳过此步，从空 wiki 开始：
cp persona.template.md persona.md
```

### 3. `/wiki-backup` 命令参考章节

描述从"将整个项目打包为带时间戳的 ZIP 文件"改为"将知识库数据（wiki/、sources/、persona.md）打包为带时间戳的 ZIP 文件"。

备份内容说明从"备份内容包含所有文件，自动排除 `.env` 和 `.git/`"改为"仅备份知识库数据，项目框架通过 git 管理"。

---

## 不在范围内

- `backup.py` 的命令行接口不变（仍接受一个目标目录参数）
- 不添加恢复脚本（解压和复制由用户手动完成，足够简单）
- 不修改其他命令
