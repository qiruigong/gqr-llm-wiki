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

若文件不存在或页面列表章节为空（无任何 `- [` 条目），跳到**第三步 fallback**。

---

## 第二步：搜索相关页面

读取 `<WIKI_ROOT>/persona.md`，了解用户背景和知识偏好（若文件不存在则跳过）。

读取 `<WIKI_ROOT>/wiki/index.md`，根据 `QUESTION` 判断哪些页面最相关（按相关度排序，最多取 5 个），逐一读取这些 `<WIKI_ROOT>/wiki/pages/*.md` 文件的完整内容。

若找到相关页面，进入**第四步**（Wiki 优先回答）。

若无任何相关页面，进入**第三步**（fallback）。

---

## 第三步：Fallback — 用自身能力和 Web 搜索回答

Wiki 中没有与问题直接相关的内容，使用以下方式回答：

1. 若当前 agent 具备 web search 能力，搜索与 `QUESTION` 最相关的资料（最多 3 条），结合搜索结果综合回答
2. 若无 web search 能力，使用自身训练知识回答

回答后，在答案末尾标注来源性质：
> （来源：Web 搜索）或（来源：模型知识，截止训练日期）

然后告知用户：
> Wiki 中暂无相关内容，以上为 fallback 回答。建议将有价值的部分通过 wiki-ingest 收录进 Wiki。

进入**第五步**（跳过第四步）。

---

## 第四步：综合答案（Wiki 优先）

根据读取到的 Wiki 页面内容，结合 `persona.md` 中用户的背景和偏好，综合回答 `QUESTION`：
- 按用户偏好的风格组织（重实践则多举例，重理论则多分析）
- 每个关键信息点标注来源页面，格式：`（来源：[[页面名]]）`
- 若多个页面有冲突信息，明确列出冲突并说明，不自作主张判断哪个正确

---

## 第五步：判断是否保存为 Wiki 页面（仅 --interactive 模式）

若 `INTERACTIVE` 为 false，跳过此步。

若 `INTERACTIVE` 为 true，且本次答案具有独立知识价值（跨页面综合分析、fallback 中产生了有价值的新内容等），询问用户：
> 这个答案包含有价值的内容，是否保存为 Wiki 页面？

若用户同意，按 `<WIKI_ROOT>/CLAUDE.md` 规范创建新页面，更新 `<WIKI_ROOT>/wiki/index.md`。
（不在此步追加 log.md，统一由第六步处理。）

---

## 第六步：追加 wiki/log.md

若 `<WIKI_ROOT>/wiki/log.md` 存在，在文件末尾追加（将 `YYYY-MM-DDTHH:MM:SS` 替换为当前 UTC 时间）：
```
[YYYY-MM-DDTHH:MM:SS] query | "<QUESTION>" | <引用页面逗号分隔，fallback时写"-"> | -
```

若 log.md 不存在（Wiki 为空或首次使用），跳过此步。
