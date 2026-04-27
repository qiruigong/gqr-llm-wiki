# /wiki-explore

探索网页内容，筛选对你有价值的知识并 ingest 进 Wiki。

**用法：**
- `/wiki-explore <url>` — 探索单个 URL
- `/wiki-explore --add <url>` — 将 URL 加入 persona.md 订阅站点列表
- `/wiki-explore` — 批量探索 persona.md 中的订阅站点列表

---

## 执行步骤（--add 模式）

### 第一步：校验参数

从用户输入中提取 `URL`。若未提供 URL，告知用户用法并停止执行。

### 第二步：检查是否已在订阅列表

读取 `persona.md` 中 `## 订阅站点` 章节下的所有 URL。

若该 URL 已存在，告知用户：
> 该 URL 已在订阅站点列表中，无需重复添加。

停止执行。

### 第三步：追加到 persona.md

在 `persona.md` 的 `## 订阅站点` 章节末尾追加一行：
```
- <URL>
```

### 第四步：询问是否立刻探索

> ✅ 已将 `<URL>` 加入订阅站点列表。
> 是否立刻探索该 URL？（y/n）

- 用户输入 `y`：执行单个 URL 模式的全部步骤（以该 URL 为输入）。
- 用户输入 `n` 或回车：停止执行，等待下次 `/wiki-explore` 批量触发。

---

## 执行步骤（单个 URL 模式）

### 第一步：检查是否已处理

运行：
```bash
python scripts/fetch.py <URL>
```

先获取 source_id（输出第一行 `SOURCE_ID:xxxxx`），然后运行：
```bash
python scripts/registry.py <source_id>
```

若返回非 `NOT_FOUND`，告知用户：
> 该 URL 已于 `[ingested_at]` 探索过，影响页面：`[affected_pages]`。是否重新探索？

等待用户确认后再继续。若用户选择跳过，停止执行。

### 第二步：抓取页面内容

运行：
```bash
python scripts/fetch.py <URL>
```

若失败，告知用户错误原因，停止执行。

### 第三步：读取个人设定

读取 `persona.md`（背景、关注领域、发展目标）和 `CLAUDE.md`（格式规范）。

### 第四步：主动筛选有价值内容

根据 `persona.md`，判断页面中哪些内容对用户的发展目标有价值：
- 与关注领域相关
- 能帮助实现发展目标
- 符合用户的知识偏好

若无任何有价值内容，告知用户：
> 该页面未发现对你有价值的内容（基于 persona.md 判断）。

停止执行。

### 第五步：写入 Wiki 页面

对每个有价值的内容片段，按 `CLAUDE.md` 规范创建或更新 Wiki 页面。

**重要：** 每个页面在 `## 摘要` 章节后额外添加：

```markdown
## 为什么对你有用

<根据 persona.md 说明这个知识点与用户背景、目标的具体关联>
```

### 第六步：更新 index.md、log.md、registry.json

同 `/wiki-ingest` 的第七、八、九步，模式记录为 `explore`。

### 第七步：推荐关联链接

读取本次写入的 Wiki 页面的 `## 来源引用` 章节，收集所有外部 URL。

过滤掉：
- 已在 registry 中（`status` 为 `ingested` 或 `pending`）的 URL
- 非 http/https 链接

结合 `persona.md` 判断剩余链接的价值，选出最多 3 条，每条附一句理由：

```
以下链接与本次探索相关，是否要处理？

[1] https://... — 理由（与 persona 的关联）
[2] https://... — 理由
...

每条请输入：a（立刻 ingest）/ b（加待消化列表）/ c（跳过）
```

对用户输入 `a` 的条目：执行完整 `/wiki-ingest` 流程。

对用户输入 `b` 的条目：在 `sources/registry.json` 中新增条目：
```json
{
  "id": "<compute_id(url)>",
  "type": "url",
  "path_or_url": "<url>",
  "ingested_at": "<当前ISO时间>",
  "affected_pages": [],
  "status": "pending",
  "mode": "persona",
  "content_hash": null,
  "last_modified": null,
  "etag": null
}
```

对用户输入 `c` 或回车的条目：跳过。

若无符合条件的推荐链接，静默跳过此步。

### 第八步：汇报结果

> ✅ Explore 完成
> - 来源：`<URL>`
> - 新增/更新页面：`[[页面1]]`、`[[页面2]]`
> - 筛选理由：[简述为什么这些内容对用户有价值]

---

## 执行步骤（批量模式）

### 第一步：读取订阅站点列表

读取 `persona.md` 中 `## 订阅站点` 章节下的所有 URL。

若列表为空，告知用户：
> persona.md 中的订阅站点列表为空。请在 `## 订阅站点` 章节下添加 URL。

停止执行。

### 第二步：逐一处理每个站点

对每个 URL，执行单个 URL 模式的全部步骤。

### 第三步：汇总报告

所有站点处理完成后，汇报：
> ✅ 批量 Explore 完成
> - 处理站点数：N
> - 新增页面：[[页面1]]、[[页面2]]、...
> - 无价值站点：[列出未提取到内容的站点]
