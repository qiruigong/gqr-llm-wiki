# LLM Wiki — 本地个人知识库管理系统设计文档

**日期：** 2026-04-27
**基于：** Andrej Karpathy 的 llm-wiki.md 模式

---

## 概述

基于 Karpathy 的 LLM Wiki 模式，构建一套运行在 Claude Code 内的本地个人知识库管理系统。核心思想：用 LLM 维护一个持久化、不断积累的 Markdown Wiki，让知识复利增长，而非每次查询都从原始资料重新提取。

---

## 目录结构

```
kaparthy/
├── wiki/                        # 知识库核心（Git 管理）
│   ├── index.md                 # 所有页面目录 + 一行摘要（自动维护）
│   ├── log.md                   # 操作日志（追加only，不修改历史）
│   └── pages/                   # Wiki 页面，每个主题一个 .md 文件
│
├── sources/                     # 原始资料永久归档区
│   ├── files/                   # 本地上传文件（PDF、txt、md）
│   └── registry.json            # 每条资料的处理状态记录
│
├── scripts/                     # 核心 Python 脚本
│   ├── ingest.py                # 抓取/读取内容，供 Claude 处理
│   ├── query.py                 # 搜索 Wiki 页面，供 Claude 综合答案
│   └── lint.py                  # 独立健康检查脚本（手动运行）
│
├── .claude/
│   └── commands/                # Claude Code 自定义 slash commands
│       ├── wiki-ingest.md       # /wiki-ingest 命令定义
│       ├── wiki-query.md        # /wiki-query 命令定义
│       └── wiki-explore.md      # /wiki-explore 命令定义
│
├── persona.md                   # 用户个人设定（用户手动维护）
├── CLAUDE.md                    # Wiki Agent 宪法：结构规范与行为准则
└── requirements.txt
```

---

## 三层架构（对应 Karpathy 设计）

| 层级 | 目录/文件 | 说明 |
|------|-----------|------|
| 原始资料层 | `sources/` | 只读输入，永久保留，可供 lint 溯源 |
| 知识库层 | `wiki/` | LLM 维护，持续积累，结构化输出 |
| Schema 层 | `CLAUDE.md` + `persona.md` | 定义行为规范和个人风格 |

---

## 核心文件说明

### CLAUDE.md（Wiki Agent 宪法）

系统总控文档，所有 slash commands 都引用此文件的规则。内容包括：

- **Wiki 页面格式规范**：每个页面必须包含摘要、关键要点、相关页面链接、来源引用
- **文件命名规则**：小写英文 + 连字符，如 `transformer-architecture.md`
- **页面间链接**：统一使用 `[[页面名]]` 双括号格式（Obsidian 兼容），禁止相对路径
- **frontmatter**：每个页面头部加 `tags:` 字段，方便 Obsidian 标签过滤
- **更新原则**：已有页面追加新信息不覆盖；冲突信息两者保留并标注"待验证"
- **index.md 格式**：`- [页面标题](pages/xxx.md) — 一行摘要`
- **log.md 格式**：`[时间] 操作类型 | 资料来源 | 影响页面`
- **行为准则**：不静默失败、不自作主张、遇矛盾呈现选项让用户决定

### persona.md（用户个人设定，用户维护）

```markdown
## 我的背景
（你的职业、技能背景）

## 知识偏好
（重实践/重理论、喜欢例子/类比等）

## 关注领域
（LLM、产品设计、创业等）

## 发展目标
（短期/长期学习目标）

## 订阅站点
- https://example.com/blog
- https://arxiv.org/...
```

### sources/registry.json

```json
{
  "sources": [
    {
      "id": "sha256前8位",
      "type": "url | file",
      "path_or_url": "...",
      "ingested_at": "2026-04-27T10:00:00",
      "affected_pages": ["transformer.md", "attention.md"],
      "status": "ingested | failed | skipped"
    }
  ]
}
```

---

## 核心操作流程

### `/wiki-ingest <url或文件路径> [--all]`

支持两种模式，通过可选标志 `--all` 切换：

| 模式 | 命令 | 行为 |
|------|------|------|
| persona 筛选（默认） | `/wiki-ingest <来源>` | 读取 persona.md，只 ingest 对你有价值的内容 |
| 全量 ingest | `/wiki-ingest <来源> --all` | 跳过 persona 筛选，直接 ingest 全部内容 |

**用法示例：**
```
/wiki-ingest https://example.com/article        # persona 筛选
/wiki-ingest sources/files/work-doc.pdf --all   # 工作文档全量 ingest
```

**执行流程：**
```
1. 检查 registry.json，若已处理则提示，询问是否重新处理
2. 抓取 URL 正文 / 读取本地文件（支持 PDF、txt、md）
3. 读取 CLAUDE.md（格式规范）
4. 若无 --all：读取 persona.md，Claude 筛选有价值内容
   若有 --all：跳过筛选，全量处理
5. Claude 提取关键知识，按用户风格组织内容
6. 创建或更新 wiki/pages/*.md
7. 更新 wiki/index.md（添加或修改对应条目）
8. 追加记录到 wiki/log.md
9. 更新 registry.json（标记已处理，记录影响页面和使用的模式）
```

**内容过长处理**：超过 token 限制时分块处理，每块独立 ingest。

### `/wiki-query <问题>`

```
1. 读取 persona.md（了解用户背景，影响答案表达方式）
2. 扫描 wiki/index.md，找出相关页面
3. 读取相关 pages/*.md
4. Claude 综合答案，标注来源页面
5. 若答案本身有价值，自动保存为新 wiki 页面
```

**Wiki 为空时**：明确提示"Wiki 中暂无相关内容"，建议 ingest 哪类资料。

### `/wiki-explore [url]`

**单个 URL 模式**（提供参数）：
```
1. 抓取页面内容
2. 读取 persona.md（背景、关注领域、发展目标）
3. Claude 主动筛选：哪些内容对你有价值？为什么？
4. 将有价值内容 ingest 进 Wiki
5. 每个 Wiki 页面附上"为什么对你有用"说明
```

**批量模式**（不提供参数）：
```
1. 读取 persona.md 里的"订阅站点"列表
2. 逐一抓取每个站点
3. 同上筛选、处理
4. 汇总报告：处理了哪些站点，新增了哪些 Wiki 页面
```

**无价值时**：告知"未发现对你有价值的内容"，不强行 ingest。

### `python scripts/lint.py`（独立 CLI）

```
1. 读取所有 wiki/pages/*.md
2. 读取 sources/registry.json（可回溯原始资料验证）
3. Claude（通过 Anthropic API 直接调用）检查：
   - 矛盾：同一概念在不同页面的描述冲突
   - 孤立页面：没有任何其他页面链接到它
   - 数据缺口：概念被多次提及但无专属页面
4. 输出报告到 wiki/lint-report.md
```

---

## Slash Commands 实现机制

`.claude/commands/*.md` 文件内容是给 Claude 的指令模板，Claude Code 执行时读取并按步骤操作。

每个 command 文件结构：
1. 引用 `CLAUDE.md` 的规范
2. 引用 `persona.md` 的用户设定
3. 具体操作步骤（对应上述流程）
4. 输出格式要求

Python 脚本（`scripts/`）负责纯技术操作：
- URL 抓取：`requests` + `readability-lxml` 提取正文
- 本地文件读取：支持 `.pdf`（`pdfplumber`）、`.txt`、`.md`
- `registry.json` 的读写管理

---

## 错误处理

| 操作 | 情况 | 处理方式 |
|------|------|----------|
| ingest | URL 无法访问 | 报错提示，记录 log.md，跳过 |
| ingest | PDF 解析失败 | 提示改用文本版，记录失败 |
| ingest | 已处理过的资料 | 提示处理时间，询问是否重新处理 |
| ingest | 内容超 token 限制 | 分块处理 |
| ingest | 默认模式下内容与 persona 无关 | 告知无价值内容，建议改用 --all |
| query | Wiki 无相关内容 | 明确告知，建议 ingest 资料类型 |
| query | 多个矛盾页面 | 列出矛盾，让用户决定 |
| query | Wiki 为空 | 提示先运行 /wiki-ingest |
| explore | 内容与 persona 无关 | 告知无价值内容，不强行 ingest |
| explore | 订阅列表为空 | 提示在 persona.md 添加订阅站点 |

**通用原则：** 不静默失败；不自作主张；所有操作记录到 log.md。

---

## Obsidian 兼容

`wiki/` 目录可直接作为 Obsidian Vault 打开，无需任何额外配置。

### 规范要求（写入 CLAUDE.md）

| 规范 | 说明 |
|------|------|
| 页面间链接 | 统一使用 `[[页面名]]` 双括号格式，禁止使用相对路径链接 |
| 标签 | 每个页面 frontmatter 里加 `tags: [tag1, tag2]`，支持 Obsidian 标签过滤 |
| 附件/图片 | 存放在 `wiki/assets/` 目录 |

### 目录结构补充

```
wiki/
├── index.md
├── log.md
├── assets/          # 图片等附件
└── pages/
    └── *.md
```

### 收益

- **知识图谱**：Obsidian 根据 `[[双括号]]` 链接自动生成页面关联图，孤立页面一目了然
- **标签浏览**：按领域/主题筛选 Wiki 页面
- **本地搜索**：Obsidian 内置全文搜索，补充 `/wiki-query` 的语义搜索

---

## 技术依赖

```
anthropic          # lint.py 直接调用 API
requests           # URL 抓取
readability-lxml   # 网页正文提取
pdfplumber         # PDF 解析
python-dotenv      # 环境变量管理
```
