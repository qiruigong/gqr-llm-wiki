# LLM Wiki

基于 LLM agent 的本地个人知识库。你提供资料，LLM 负责整理、提炼、归档成结构化 Markdown；知识在使用中持续积累，不再一次性消耗。

**目录**

- [核心理念](#核心理念)
- [目录结构](#目录结构)
- [快速开始](#快速开始)
- [命令参考](#命令参考)
- [Wiki 健康检查](#wiki-健康检查)
- [Obsidian 集成](#obsidian-集成)
- [在新机器上部署](#在新机器上部署)
- [脚本直接使用](#脚本直接使用)
- [跨 Agent 迁移](#跨-agent-迁移)

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
├── persona.template.md    # 个人设定模板（复制为 persona.md 后填写）
├── persona.md             # 你的个人设定：背景、偏好、关注领域、订阅站点 ⚠️ 已 gitignore
├── pyproject.toml         # Python 依赖声明（uv 管理）
├── uv.lock                # 精确依赖锁（所有传递依赖版本快照）
│
├── wiki/                  # ⚠️ 知识库数据，已 gitignore，用 /wiki-backup 备份
│   ├── index.md           # 所有页面目录（自动维护）
│   ├── log.md             # 操作日志（追加 only）
│   ├── pages/             # Wiki 页面（*.md）
│   └── assets/            # 图片等附件
│
├── sources/               # ⚠️ 知识库数据，已 gitignore，用 /wiki-backup 备份
│   ├── registry.json      # 已处理资料的状态记录
│   └── files/             # 本地上传文件存储
│
├── scripts/
│   ├── fetch.py           # URL 抓取 + 本地文件读取
│   ├── registry.py        # registry.json 读写
│   ├── lint.py            # Wiki 结构扫描（孤立页面、缺失章节）
│   └── backup.py          # 打包备份为带时间戳 ZIP
│
├── prompts/               # agent 无关的通用 prompt（跨 agent 迁移用）
│   ├── wiki-ingest.md
│   ├── wiki-query.md
│   ├── wiki-explore.md
│   ├── wiki-sync.md
│   ├── wiki-lint.md
│   └── wiki-backup.md
│
├── skills/
│   └── wiki-query.md      # wiki-query skill 源文件（需手动复制到 ~/.claude/skills/）
│
└── .claude/
    └── commands/          # Claude Code slash commands（wiki-query 为 skill 薄包装）
```

> **说明：** `wiki-query` 的完整逻辑存放在 `skills/wiki-query.md`，需手动复制到 `~/.claude/skills/` 才能生效（见快速开始第 4 步）。slash command 仅作为触发入口。

> **说明：** `persona.md`、`wiki/`（pages、index、log、assets）、`sources/`（registry.json、files/）均已加入 `.gitignore`，不会进入版本控制。仓库只保存项目框架（脚本、命令定义、规范文档），个人知识积累请使用 `/wiki-backup` 自行备份。

---

## 快速开始

### 1. 安装 Python 依赖

本项目使用 [uv](https://docs.astral.sh/uv/) 管理依赖，`uv.lock` 精确锁定了所有传递依赖版本，保证环境可复现。

**安装 uv（若未安装）：**

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**同步依赖（自动创建虚拟环境 `.venv/`）：**

```bash
uv sync
```

之后所有 `python` 命令通过 `uv run` 调用，无需手动激活虚拟环境：

```bash
uv run python scripts/fetch.py https://example.com
```

> **若不想用 uv：** 也可以用标准 pip，但无法保证传递依赖版本一致：
> ```bash
> pip install requests readability-lxml pdfplumber python-dotenv html2text
> ```

### 2. 验证环境

```bash
# 验证 fetch.py：应输出 SOURCE_ID:xxxxx 开头的行
uv run python scripts/fetch.py https://example.com

# 验证 registry.py：应输出 NOT_FOUND
uv run python scripts/registry.py nonexistent
```

### 3. 填写个人设定

`persona.md` 已加入 `.gitignore`，不会进入版本控制，需要你自行创建：

```bash
cp persona.template.md persona.md
```

然后编辑 `persona.md`，填入你的背景、关注领域和发展目标。填得越具体，persona 筛选模式的结果越精准。

### 4. 安装 wiki-query skill

`/wiki-query` 的完整逻辑以 Claude Code skill 形式实现，需复制到用户级 skills 目录才能生效：

```bash
# macOS / Linux
cp skills/wiki-query.md ~/.claude/skills/wiki-query.md

# Windows (PowerShell)
Copy-Item skills\wiki-query.md $env:USERPROFILE\.claude\skills\wiki-query.md
```

若 `~/.claude/skills/` 目录不存在，先创建：

```bash
mkdir -p ~/.claude/skills   # macOS / Linux
mkdir $env:USERPROFILE\.claude\skills  # Windows (PowerShell)
```

完成以上步骤后，在 Claude Code 中即可使用所有 `/wiki-*` 命令。

---

## 命令参考

### `/wiki-ingest` — 导入资料

将 URL 或本地文件的内容提炼进 Wiki。

```
/wiki-ingest <url或文件路径>                  # persona 筛选模式（默认），ingest 后推荐关联链接
/wiki-ingest <url或文件路径> --all            # 全量 ingest，跳过筛选
/wiki-ingest <url或文件路径> --no-recommend   # 跳过关联链接推荐
```

**两种模式的区别：**

| 模式 | 行为 |
|------|------|
| 默认（persona） | 根据 `persona.md` 过滤，只保留对你有价值的内容，ingest 后推荐关联链接 |
| `--all` | 全量处理，不做筛选，适合你明确知道整篇都有用的资料 |
| `--no-recommend` | 跳过关联链接推荐，适合批量处理时减少交互 |

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
- 追加操作记录到 `wiki/log.md`

**Agent 调用：**

在其他 agent 或 skill 中，可通过 `Skill` 工具程序化调用：

```
Skill("wiki-query", "什么是 RAG？它的核心组件有哪些？")
```

与手动触发的区别：跳过"是否保存为 Wiki 页面"的交互询问，其余行为完全一致（读取 persona、检索页面、综合答案、追加 log.md）。

---

### `/wiki-explore` — 主动探索

比 ingest 更主动——Claude 会判断页面中哪些内容值得收录，并说明理由。

```
/wiki-explore <url>          # 探索单个页面
/wiki-explore --add <url>    # 将 URL 加入 persona.md 订阅站点列表
/wiki-explore                # 批量探索 persona.md 中的订阅站点列表
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

### `/wiki-backup` — 备份知识库

将知识库数据（`wiki/`、`sources/`、`persona.md`）打包为带时间戳的 ZIP 文件。

```
/wiki-backup                  # 备份到 persona.md 中配置的备份目录
/wiki-backup <目录路径>        # 备份到指定目录
```

仅备份知识库数据，项目框架（脚本、commands 等）通过 git 管理，无需重复备份。

**配置默认备份目录：**

在 `persona.md` 的 `## 备份目录` 章节填入路径，建议使用云盘同步目录：

```
## 备份目录

- C:/Users/你的用户名/OneDrive/Backups/llm-wiki
```

---

## Wiki 健康检查

`lint.py` 独立于 Claude Code 运行，对 Wiki 做结构扫描（孤立页面、缺失章节、缺失 frontmatter），输出机器可读结果供 `/wiki-lint` command 进一步分析。矛盾检测和知识缺口分析由 `/wiki-lint` command 中的 Claude 完成。

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

## 在新机器上部署

### 第一步：部署项目框架（通过 git）

```bash
git clone https://github.com/qiruigong/gqr-llm-wiki.git
cd gqr-llm-wiki
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

---

## 脚本直接使用

slash commands 内部调用这些脚本，你也可以直接运行：

```bash
# 抓取 URL 内容（输出纯文本）
uv run python scripts/fetch.py https://example.com

# 抓取本地 PDF
uv run python scripts/fetch.py path/to/paper.pdf

# 查询某个 source_id 的处理记录
uv run python scripts/registry.py <source_id>

# 备份到指定目录
uv run python scripts/backup.py ./backups

# Wiki 结构扫描（孤立页面、缺失章节）
uv run python scripts/lint.py

# 检测所有 365 天内 URL 来源的更新
uv run python scripts/check_updates.py

# 只检测指定 URL
uv run python scripts/check_updates.py https://example.com/article
```

---

## 跨 Agent 迁移

本项目的核心逻辑（`scripts/`、`wiki/`、`sources/`、`CLAUDE.md` 格式规范）不依赖任何特定 agent 软件。真正有 agent 依赖的只有命令入口层：

| 层 | 说明 |
|---|---|
| `scripts/` | 纯 Python，无 agent 依赖 |
| `wiki/`、`sources/` | 纯 Markdown/JSON 数据，无 agent 依赖 |
| `CLAUDE.md` | Wiki 格式规范，无 agent 依赖（其他 agent 可直接读取） |
| `prompts/` | agent 无关的通用 prompt，各 agent 均可直接使用 |
| `.claude/commands/` | Claude Code 专用入口 |
| `skills/` | Claude Code skill 格式（claude-query 特有） |

### 迁移到其他 agent

**第一步：确认 Python 脚本可用**（无需改动，所有 agent 都可以通过 shell 调用）

**第二步：将 `prompts/` 中的 prompt 接入目标 agent 的命令系统**

`prompts/` 目录中每个文件是一份完整的功能 prompt，去掉了所有 Claude Code 专有语法，可直接用于：

| Agent | 接入方式 |
|---|---|
| **Cursor** | 复制 prompt 内容到 `.cursor/rules/`，或粘贴到 Cursor Chat 触发 |
| **Copilot (VS Code)** | 复制到 `.github/copilot-instructions.md`，或在 `#` 引用文件触发 |
| **Windsurf / Cline** | 复制 prompt 内容到对应的 rules 或 system prompt 配置文件 |
| **任意支持系统 prompt 的 agent** | 直接将 prompt 文件内容作为 system prompt 或 user 消息触发 |

**第三步：按目标 agent 的惯例创建命令入口**（可选）

若目标 agent 支持自定义命令或快捷方式，参照 `.claude/commands/` 中的结构，将 `prompts/` 里的逻辑包装为该 agent 的命令格式。

### wiki-query 的特殊处理

`wiki-query` 在 Claude Code 中以 skill 形式实现（`skills/wiki-query.md`），支持通过 `Skill` 工具被其他 agent 程序化调用。迁移到无 skill 系统的 agent 时，直接使用 `prompts/wiki-query.md` 的内容触发即可，行为完全一致。

