# /wiki-query

向 Wiki 知识库提问，获取综合答案。

**用法：**
`/wiki-query <自然语言问题>`

---

从用户输入中提取问题文本，用 TodoWrite 列出执行步骤，等待用户确认后通过 Skill 工具调用 wiki-query，传入参数：`<问题> --interactive`。每完成一步立即用 TaskUpdate 标记完成。

<!-- 完整逻辑在用户级 skill：~/.claude/skills/wiki-query.md -->
