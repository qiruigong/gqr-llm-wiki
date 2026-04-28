# wiki-explore prompt

探索网页内容，主动筛选对用户有价值的知识并 ingest 进 Wiki。

**参数：**
- `MODE`：`single`（探索单个 URL）、`add`（将 URL 加入订阅列表）、`batch`（批量探索订阅列表）
- `URL`：目标 URL（`single` 和 `add` 模式必填）

---

## 执行步骤（add 模式）

### 第一步：检查是否已在订阅列表

读取 `persona.md` 中 `## 订阅站点` 章节。若 URL 已存在，告知用户并停止。

### 第二步：追加到 persona.md

在 `## 订阅站点` 章节末尾追加：`- <URL>`

### 第三步：询问是否立刻探索

告知用户已添加，询问是否立刻探索。若是，执行 single 模式。

---

## 执行步骤（single 模式）

### 第一步：检查是否已处理

执行：`python scripts/fetch.py <URL>` 获取 source_id，再执行 `python scripts/registry.py <source_id>`。

若返回非 `NOT_FOUND`，询问是否重新探索。

### 第二步：抓取页面内容

执行：`python scripts/fetch.py <URL>`。若失败，告知用户错误原因并停止。

### 第三步：读取个人设定

读取 `persona.md` 和 `CLAUDE.md`。

### 第四步：主动筛选有价值内容

根据 `persona.md` 判断哪些内容与用户的关注领域和发展目标相关。若无有价值内容，告知用户并停止。

### 第五步：写入 Wiki 页面

按 `CLAUDE.md` 规范创建或更新页面。每个页面在 `## 摘要` 后额外添加：

```markdown
## 为什么对你有用

<根据 persona.md 说明与用户背景、目标的具体关联>
```

### 第六步：更新 index.md、log.md、registry.json

同 wiki-ingest prompt 的第七、八、九步，registry 条目 `mode` 字段记为 `explore`。

### 第七步：推荐关联链接

同 wiki-ingest prompt 第十步的推荐逻辑。

### 第八步：汇报结果

```
✅ Explore 完成
- 来源：<URL>
- 新增/更新页面：[[页面1]]、[[页面2]]
- 筛选理由：[简述为什么这些内容对用户有价值]
```

---

## 执行步骤（batch 模式）

### 第一步：读取订阅列表

读取 `persona.md` 中 `## 订阅站点` 章节。若为空，告知用户并停止。

### 第二步：逐一处理每个 URL

对每个 URL 执行 single 模式的全部步骤。

### 第三步：汇总报告

```
✅ 批量 Explore 完成
- 处理站点数：N
- 新增页面：[[页面1]]、[[页面2]]、...
- 无价值站点：[列出未提取到内容的站点]
```
