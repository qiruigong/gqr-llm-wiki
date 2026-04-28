# Wiki Agent 宪法

本文件定义知识库管理的格式规范和行为准则，供所有 slash commands 执行时遵守。
人类操作指南见 `README.md`。

---

## Wiki 页面格式规范

每个 `wiki/pages/*.md` 页面必须包含以下结构：

```markdown
---
tags: [标签1, 标签2]
updated: YYYY-MM-DD
sources: [来源URL或文件名]
---

# 页面标题

## 摘要
一到两句话概括本页核心内容。

## 关键要点
- 要点1
- 要点2

## 详细内容
正文...

## 相关页面
- [[相关页面名1]]
- [[相关页面名2]]

## 来源引用
- [来源标题](URL或文件路径)
```

---

## 文件命名规则

- 小写英文 + 连字符
- 示例：`transformer-architecture.md`、`rag-retrieval.md`
- 不使用中文、空格、下划线

---

## 链接规范

- 页面间链接**统一使用** `[[文件名]]` 双括号格式，文件名不含路径和 `.md` 后缀（Obsidian 兼容）
- 需要可读别名时使用 `[[文件名|显示文字]]` 格式，例如：`[[sap-business-ai-platform|SAP Business AI Platform (BAIP)]]`
- **禁止**使用相对路径链接（如 `[文字](pages/xxx.md)`）
- index.md 中使用标准 Markdown 链接：`- [页面标题](pages/文件名.md) — 一行摘要`

---

## 来源引用规范

- **URL 来源**：直接写完整 URL
  ```markdown
  - [来源标题](https://example.com/article)
  ```
- **本地文件来源**：ingest 时将文件复制到 `wiki/assets/`，引用使用相对路径 `../assets/文件名`
  ```markdown
  - [来源标题](../assets/paper.pdf)
  ```
- **禁止**在来源引用中使用 `sources/files/` 路径（vault 外部，Obsidian 无法打开）

---

## 内容更新原则

- **追加不覆盖**：已有页面新增信息时追加到相关章节，不删除旧内容
- **冲突处理**：两个来源说法冲突时，两者都保留，标注 `⚠️ 待验证`
- **新主题**：创建新页面，同时在 index.md 添加条目

---

## index.md 维护规范

每次新增或更新 Wiki 页面后，必须同步更新 `wiki/index.md`：

```
- [页面标题](pages/文件名.md) — 一行中文摘要
```

---

## log.md 记录规范

每次操作结束后追加一条记录：

```
[2026-04-27T10:30:00] ingest | https://example.com/article | transformer.md, attention.md | persona筛选模式
[2026-04-27T11:00:00] query  | "什么是RAG？" | rag-retrieval.md | -
[2026-04-27T12:00:00] explore | https://blog.example.com | llm-scaling.md | 新增1页
```

---

## 行为准则

1. **不静默失败**：所有错误必须明确告知用户，不能悄悄跳过
2. **不自作主张**：遇到矛盾或不确定时，列出选项让用户决定
3. **遇矛盾存疑**：冲突信息两者保留，标注 `⚠️ 待验证`，不擅自判断哪个正确
4. **引用来源**：每个 Wiki 页面必须记录信息来源
5. **persona 优先**：默认模式下，按 persona.md 的用户背景和偏好组织内容
