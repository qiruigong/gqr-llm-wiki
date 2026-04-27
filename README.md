# LLM Wiki

基于 Claude Code slash commands 的本地个人知识库。你提供资料，LLM 负责整理、提炼、归档成结构化 Markdown；知识在使用中持续积累，不再一次性消耗。

---

## 核心理念

- **知识复利**：每次 ingest 的内容都以 Markdown 沉淀下来，下次查询可以直接复用
- **persona 驱动**：根据你在 `persona.md` 中填写的背景和目标，自动过滤无关内容
- **Obsidian 兼容**：`wiki/` 目录即是一个 Obsidian vault，双链、Graph View、标签全部可用

---

## 目录结构

```
.
├── CLAUDE.md              # Agent 宪法：Wiki 格式规范、行为准则（供 LLM 读取）
├── persona.md             # 你的个人设定：背景、偏好、关注领域、订阅站点
├── requirements.txt       # Python 依赖
├── .env.example           # 环境变量模板
│
├── wiki/
│   ├── index.md           # 所有页面目录（自动维护）
│   ├── log.md             # 操作日志（追加 only）
│   ├── pages/             # Wiki 页面（*.md）
│   └── assets/            # 图片等附件
│
├── sources/
│   ├── registry.json      # 已处理资料的状态记录
│   └── files/             # 本地上传文件存储
│
├── scripts/
│   ├── fetch.py           # URL 抓取 + 本地文件读取
│   ├── registry.py        # registry.json 读写
│   ├── lint.py            # Wiki 健康检查（调用 Anthropic API）
│   └── backup.py          # 打包备份为带时间戳 ZIP
│
└── .claude/
    └── commands/          # Slash commands 定义文件
```

---

## 快速开始

### 1. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
cp .env.example .env
```

用编辑器打开 `.env`，填入你的 Anthropic API Key：

```
ANTHROPIC_API_KEY=sk-ant-...
```

### 3. 验证环境

```bash
# 验证 fetch.py：应输出 SOURCE_ID: 开头的行
python scripts/fetch.py https://example.com

# 验证 registry.py：应输出 NOT_FOUND
python scripts/registry.py nonexistent
```

### 4. 填写个人设定

编辑 `persona.md`，填入你的背景、关注领域和发展目标。这是 persona 筛选模式的依据，填得越具体，筛选越精准。

完成以上步骤后，在 Claude Code 中即可使用所有 `/wiki-*` 命令。

---

## 命令参考

### `/wiki-ingest` — 导入资料

将 URL 或本地文件的内容提炼进 Wiki。

```
/wiki-ingest <url或文件路径>         # persona 筛选模式（默认）
/wiki-ingest <url或文件路径> --all   # 全量 ingest，跳过筛选
```

**两种模式的区别：**

| 模式 | 行为 |
|------|------|
| 默认（persona） | 根据 `persona.md` 过滤，只保留对你有价值的内容 |
| `--all` | 全量处理，不做筛选，适合你明确知道整篇都有用的资料 |

**示例：**

```
/wiki-ingest https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
/wiki-ingest sources/files/paper.pdf --all
```

**自动完成的事：**
- 检查是否已处理过（重复时会询问是否重新处理）
- 写入 / 更新 `wiki/pages/*.md`（追加不覆盖，冲突标注 ⚠️ 待验证）
- 更新 `wiki/index.md`
- 追加 `wiki/log.md`
- 更新 `sources/registry.json`

---

### `/wiki-query` — 查询知识库

用自然语言向 Wiki 提问，获取综合答案。

```
/wiki-query <问题>
```

**示例：**

```
/wiki-query 什么是 RAG？它的核心组件有哪些？
/wiki-query Transformer 的注意力机制和 RNN 的本质区别是什么？
```

**行为说明：**
- 自动检索最相关的页面（最多 5 个），综合回答
- 每个关键信息标注来源：`（来源：[[页面名]]）`
- 若多页面有冲突，列出冲突不擅自判断
- 若答案有独立知识价值，会询问是否保存为新 Wiki 页面

---

### `/wiki-explore` — 主动探索

比 ingest 更主动——Claude 会判断页面中哪些内容值得收录，并说明理由。

```
/wiki-explore <url>    # 探索单个页面
/wiki-explore          # 批量探索 persona.md 中的订阅站点列表
```

**与 `/wiki-ingest` 的区别：**

| | `/wiki-ingest` | `/wiki-explore` |
|---|---|---|
| 触发方式 | 你指定资料，Claude 处理 | Claude 主动判断价值 |
| 额外输出 | 无 | 每个页面额外写"为什么对你有用" |
| 批量支持 | 无 | 支持，读取 persona.md 订阅站点列表 |

**配置订阅站点（用于批量模式）：**

在 `persona.md` 的 `## 订阅站点` 章节下添加 URL，然后直接运行 `/wiki-explore` 即可批量处理。

---

### `/wiki-sync` — 检测更新并维护待消化列表

检测已 ingest 的 URL 来源是否有内容变化，重新 ingest 有更新的来源，并推荐关联链接。

```
/wiki-sync
```

**检测逻辑：**
1. 优先用 HTTP `ETag` / `Last-Modified` 头快速判断（无需下载全文）
2. 无头部信息时 fallback 为全文 hash 对比

**待消化列表：**  
推荐的关联链接可选择加入待消化列表（存于 `sources/registry.json`，`status=pending`）。  
消化时直接运行：`/wiki-ingest <url>`

**扫描范围：** registry 中 365 天内 ingest 过的所有 URL 来源。

---

### `/wiki-backup` — 备份项目

将整个项目打包为带时间戳的 ZIP 文件。

```
/wiki-backup                  # 备份到 persona.md 中配置的备份目录
/wiki-backup <目录路径>        # 备份到指定目录
```

备份内容包含所有文件，自动排除 `.env`（含密钥）和 `.git/`。

**配置默认备份目录：**

在 `persona.md` 的 `## 备份目录` 章节填入路径，建议使用云盘同步目录：

```
## 备份目录

- C:/Users/你的用户名/OneDrive/Backups/llm-wiki
```

---

## Wiki 健康检查

`lint.py` 独立于 Claude Code 运行，直接调用 Anthropic API，检查 Wiki 中的矛盾、孤立页面和知识缺口。

```bash
python scripts/lint.py
```

报告保存到 `wiki/lint-report.md`。建议在 Wiki 内容积累到一定量后定期运行。

---

## Obsidian 集成

直接用 Obsidian 打开 `wiki/` 目录作为 vault：

**Obsidian → Open folder as vault → 选择 `wiki/`**

所有 `[[双括号]]` 链接自动变为可跳转链接，Graph View 可视化页面关联，frontmatter 中的 `tags` 字段在 Tags 面板中可浏览。

---

## 在新机器上恢复

1. 解压备份 ZIP 到目标目录
2. 在 Claude Code 中打开该目录
3. 按"快速开始"章节重新初始化（安装依赖 → 配置 API Key → 验证环境）
4. `persona.md` 和所有 Wiki 页面已在备份中，无需重填

---

## 脚本直接使用

slash commands 内部调用这些脚本，你也可以直接运行：

```bash
# 抓取 URL 内容（输出纯文本）
python scripts/fetch.py https://example.com

# 抓取本地 PDF
python scripts/fetch.py path/to/paper.pdf

# 查询某个 source_id 的处理记录
python scripts/registry.py <source_id>

# 备份到指定目录
python scripts/backup.py ./backups

# Wiki 健康检查
python scripts/lint.py

# 检测所有 365 天内 URL 来源的更新
python scripts/check_updates.py

# 只检测指定 URL
python scripts/check_updates.py https://example.com/article
```
