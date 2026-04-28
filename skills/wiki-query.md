---
name: wiki-query
description: 向本地 Wiki 知识库提问，获取综合答案。Wiki 根目录为包含 CLAUDE.md 的项目目录（由调用上下文推断）。支持 --interactive 参数（slash command 透传时使用），控制是否询问用户保存答案为 Wiki 页面。不传 --interactive 时默认跳过保存询问，适合 agent 调用。用法：wiki-query <自然语言问题> [--interactive]
---

# wiki-query skill

Wiki 根目录为当前项目目录（包含 `CLAUDE.md` 的目录，即 Claude Code 的工作目录）。
下文用 `<WIKI_ROOT>` 表示该目录。

从调用参数中提取：
- `QUESTION`：问题文本（`--interactive` 之前的全部内容）
- `INTERACTIVE`：若参数包含 `--interactive` 则为 true，否则为 false

---

## 第一步：检查 Wiki 是否为空

读取 `<WIKI_ROOT>/wiki/index.md`。

若页面列表章节为空（无任何 `- [` 条目），告知用户：
> Wiki 暂无内容，请先运行 `/wiki-ingest <url或文件>` 添加资料。

停止执行。

---

## 第二步：读取用户背景

读取 `<WIKI_ROOT>/persona.md`，了解用户背景和知识偏好，用于后续答案组织方式。

若文件不存在或内容为空，跳过个性化，以通用技术读者风格组织答案。

---

## 第三步：搜索相关页面

读取 `<WIKI_ROOT>/wiki/index.md`，根据 `QUESTION` 判断哪些页面最相关（按相关度排序，最多取 5 个）。

然后逐一读取这些 `<WIKI_ROOT>/wiki/pages/*.md` 文件的完整内容。

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

若用户同意，按 `<WIKI_ROOT>/CLAUDE.md` 规范创建新页面，更新 `<WIKI_ROOT>/wiki/index.md`。
（不在此步追加 log.md，统一由第六步处理。）

---

## 第六步：追加 wiki/log.md

在 `<WIKI_ROOT>/wiki/log.md` 文件末尾追加（将 `YYYY-MM-DDTHH:MM:SS` 替换为当前 UTC 时间）：
```
[YYYY-MM-DDTHH:MM:SS] query | "<QUESTION>" | <引用页面逗号分隔> | -
```
