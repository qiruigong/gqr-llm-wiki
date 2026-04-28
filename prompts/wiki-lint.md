# wiki-lint prompt

对 Wiki 知识库进行健康检查，找出矛盾、孤立页面和知识缺口。

---

## 执行步骤

### 第一步：运行结构扫描

执行 shell 命令：`python scripts/lint.py`

解析输出：
- `EMPTY_WIKI` — Wiki 为空，告知用户先运行 wiki-ingest，停止
- `TOTAL:<n>` — 共 n 个页面
- `ORPHANS:<page1,page2,...>` — 孤立页面（`none` 表示无）
- `MISSING_SECTIONS:<page>:<section1,section2>` — 缺少必要章节的页面
- `MISSING_FRONTMATTER:<page>` — 缺少 frontmatter 的页面

### 第二步：读取所有 Wiki 页面内容

逐一读取 `wiki/pages/*.md` 完整内容。

### 第三步：读取个人设定

读取 `persona.md` 了解用户的关注领域和知识偏好。

### 第四步：综合分析

1. **矛盾**：同一概念在不同页面中描述冲突（列出具体页面和冲突内容）
2. **知识缺口**：某个概念被多次提及但没有专属页面
3. **结构问题**：孤立页面、缺失章节、缺失 frontmatter（来自第一步）
4. **改善建议**：结合 persona.md 给出具体的 Wiki 扩展建议

### 第五步：保存报告

将健康报告保存到 `wiki/lint-report.md`：

```markdown
# Wiki 健康报告

**生成时间：** YYYY-MM-DD HH:MM UTC
**检查页面数：** N
**孤立页面数：** M

---

## 结构问题

## 矛盾

## 知识缺口

## 改善建议
```

### 第六步：汇报

向用户展示报告摘要，告知报告已保存到 `wiki/lint-report.md`。
