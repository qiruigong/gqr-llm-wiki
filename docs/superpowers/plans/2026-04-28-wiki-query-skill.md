# wiki-query Skill 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 wiki-query 逻辑迁移到用户级 skill，slash command 改为薄包装，agent 可通过 `Skill` 工具调用。

**Architecture:** skill 文件 `~/.claude/skills/wiki-query.md` 承载全部逻辑，路径硬编码为 `C:\SAPDevelop\kaparthy`，通过 `--interactive` 参数区分用户手动触发（保留第五步保存询问）和 agent 调用（跳过第五步）。slash command `.claude/commands/wiki-query.md` 精简为一行调用指令，透传用户问题并追加 `--interactive`。

**Tech Stack:** Claude Code skill 系统（Markdown frontmatter）、Claude Code slash command 系统

---

## 文件结构

| 操作 | 文件 | 说明 |
|------|------|------|
| 新建 | `~/.claude/skills/wiki-query.md` | 完整逻辑，含 frontmatter 和 `--interactive` 分支 |
| 改写 | `C:\SAPDevelop\kaparthy\.claude\commands\wiki-query.md` | 薄包装，调用 skill |
| 更新 | `C:\SAPDevelop\kaparthy\README.md` | 新增 Agent 调用章节 |

---

### Task 1：新建用户级 skill 文件

**Files:**
- Create: `C:\Users\I334063\.claude\skills\wiki-query.md`

- [ ] **Step 1：创建 skill 文件**

内容如下（将现有 slash command 逻辑完整迁移，加 frontmatter 和路径硬编码，第五步加 `--interactive` 判断）：

```markdown
---
name: wiki-query
description: 向本地 Wiki 知识库提问，获取综合答案。Wiki 根目录硬编码为 C:\SAPDevelop\kaparthy。支持 --interactive 参数（slash command 透传时使用），控制是否询问用户保存答案为 Wiki 页面。不传 --interactive 时默认跳过保存询问，适合 agent 调用。用法：wiki-query <自然语言问题> [--interactive]
---

# wiki-query skill

Wiki 根目录：`C:\SAPDevelop\kaparthy`

从调用参数中提取：
- `QUESTION`：问题文本（`--interactive` 之前的全部内容）
- `INTERACTIVE`：若参数包含 `--interactive` 则为 true，否则为 false

---

## 第一步：检查 Wiki 是否为空

读取 `C:\SAPDevelop\kaparthy\wiki\index.md`。

若页面列表章节为空（无任何 `- [` 条目），告知用户：
> Wiki 暂无内容，请先运行 `/wiki-ingest <url或文件>` 添加资料。

停止执行。

---

## 第二步：读取用户背景

读取 `C:\SAPDevelop\kaparthy\persona.md`，了解用户背景和知识偏好，用于后续答案组织方式。

---

## 第三步：搜索相关页面

读取 `C:\SAPDevelop\kaparthy\wiki\index.md`，根据 `QUESTION` 判断哪些页面最相关（按相关度排序，最多取 5 个）。

然后逐一读取这些 `C:\SAPDevelop\kaparthy\wiki\pages\*.md` 文件的完整内容。

若无任何相关页面，告知用户：
> Wiki 中暂无与「<QUESTION>」相关的内容。建议 ingest 以下类型资料：[根据问题给出建议]

停止执行。

---

## 第四步：综合答案

根据读取到的 Wiki 页面内容，结合 `persona.md` 中用户的背景和偏好，综合回答 `QUESTION`：
- 按用户偏好的风格组织（重实践则多举例，重理论则多分析）
- 每个关键信息点标注来源页面，格式：`（来源：[[页面名]]）`
- 若多个页面有冲突信息，明确列出冲突并说明，不自作主张判断哪个正确

---

## 第五步：判断是否保存为 Wiki 页面（仅 --interactive 模式）

若 `INTERACTIVE` 为 false，跳过此步。

若 `INTERACTIVE` 为 true，且本次查询的综合答案本身具有独立知识价值（例如：用户的问题涉及跨页面综合分析，答案产生了新洞见），询问用户：
> 这个答案包含有价值的综合分析，是否保存为 Wiki 页面？

若用户同意，按 `C:\SAPDevelop\kaparthy\CLAUDE.md` 规范创建新页面，更新 `C:\SAPDevelop\kaparthy\wiki\index.md`，追加 `C:\SAPDevelop\kaparthy\wiki\log.md`。

---

## 第六步：追加 wiki/log.md

在 `C:\SAPDevelop\kaparthy\wiki\log.md` 文件末尾追加：
```
[ISO时间] query | "<QUESTION>" | <引用页面逗号分隔> | -
```
```

- [ ] **Step 2：确认文件已创建**

打开 `C:\Users\I334063\.claude\skills\wiki-query.md`，检查 frontmatter 的 `name` 字段为 `wiki-query`，`description` 字段完整描述了 skill 用途和参数。

- [ ] **Step 3：Commit**

```bash
git -C "C:\SAPDevelop\kaparthy" add .
git -C "C:\SAPDevelop\kaparthy" commit -m "feat: add wiki-query user-level skill

Extracts wiki-query logic into ~/.claude/skills/wiki-query.md so agents
can invoke it via the Skill tool. Supports --interactive flag to preserve
the save-to-wiki prompt when called from the slash command."
```

> 注意：`~/.claude/skills/` 不在 git 仓库内，此 commit 只记录意图。实际 skill 文件无需 commit。

---

### Task 2：改写 slash command 为薄包装

**Files:**
- Modify: `C:\SAPDevelop\kaparthy\.claude\commands\wiki-query.md`

- [ ] **Step 1：用新内容完全替换 wiki-query.md**

新内容：

```markdown
# /wiki-query

向 Wiki 知识库提问，获取综合答案。

**用法：**
`/wiki-query <自然语言问题>`

---

从用户输入中提取问题文本，调用 wiki-query skill，传入参数：`<问题> --interactive`
```

- [ ] **Step 2：验证文件内容正确**

读取 `C:\SAPDevelop\kaparthy\.claude\commands\wiki-query.md`，确认：
- 文件包含调用 skill 的指令
- 包含 `--interactive` 透传说明
- 不再包含原来的六步执行逻辑

- [ ] **Step 3：Commit**

```bash
git -C "C:\SAPDevelop\kaparthy" add .claude/commands/wiki-query.md
git -C "C:\SAPDevelop\kaparthy" commit -m "refactor: simplify wiki-query command to thin wrapper over skill

Slash command now delegates all logic to the wiki-query skill,
passing --interactive so the save-to-wiki prompt is preserved for
manual use."
```

---

### Task 3：更新 README.md

**Files:**
- Modify: `C:\SAPDevelop\kaparthy\README.md`

- [ ] **Step 1：在 `/wiki-query` 命令章节末尾新增 Agent 调用小节**

定位 README.md 中 `### `/wiki-query` — 查询知识库` 章节（约第 143 行），在该章节末尾（`---` 分隔线之前）插入：

```markdown
**Agent 调用：**

在其他 agent 或 skill 中，可通过 `Skill` 工具程序化调用：

```
Skill("wiki-query", "什么是 RAG？它的核心组件有哪些？")
```

与手动触发的区别：跳过"是否保存为 Wiki 页面"的交互询问，其余行为完全一致（读取 persona、检索页面、综合答案、追加 log.md）。
```

- [ ] **Step 2：在目录结构章节更新 `.claude/` 说明**

定位 README.md 中目录结构部分的 `.claude/` 条目，将：
```
└── .claude/
    └── commands/          # Slash commands 定义文件
```
改为：
```
└── .claude/
    └── commands/          # Slash commands 定义文件（wiki-query 为 skill 薄包装）
```

并在目录结构说明段落后新增一行注释：

```
> **说明：** `wiki-query` 的完整逻辑存放在用户级 skill `~/.claude/skills/wiki-query.md`，slash command 仅作为触发入口。
```

- [ ] **Step 3：验证 README 格式**

读取 README.md 相关章节，确认：
- 新增的"Agent 调用"小节格式与其他小节一致
- 目录结构说明已更新
- 无多余空行或格式错误

- [ ] **Step 4：Commit**

```bash
git -C "C:\SAPDevelop\kaparthy" add README.md
git -C "C:\SAPDevelop\kaparthy" commit -m "docs: document wiki-query skill and agent invocation in README"
```

---

### Task 4：推送到 GitHub

- [ ] **Step 1：确认远端状态**

```bash
git -C "C:\SAPDevelop\kaparthy" status
git -C "C:\SAPDevelop\kaparthy" log --oneline -5
```

预期：工作区干净，最近 3 条 commit 包含本次变更。

- [ ] **Step 2：推送**

```bash
git -C "C:\SAPDevelop\kaparthy" push origin main
```

- [ ] **Step 3：确认推送成功**

```bash
git -C "C:\SAPDevelop\kaparthy" log --oneline origin/main -5
```

预期：远端 HEAD 与本地一致。
