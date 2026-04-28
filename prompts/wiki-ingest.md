# wiki-ingest prompt

将资料 ingest 进 Wiki 知识库。

**参数：**
- `SOURCE`：URL 或本地文件路径
- `FILTER`：`persona`（默认，按个人设定筛选）或 `all`（全量处理）
- `RECOMMEND`：`true`（默认，ingest 后推荐关联链接）或 `false`（跳过推荐）

---

## 执行步骤

### 第一步：解析参数

从用户输入中提取 `SOURCE`、`FILTER`、`RECOMMEND`。

### 第二步：检查是否已处理

执行 shell 命令：`python scripts/fetch.py <SOURCE>`

获取输出第一行的 `SOURCE_ID:xxxxx`，再执行：`python scripts/registry.py <source_id>`

若返回非 `NOT_FOUND`，告知用户该资料已处理过（显示时间和影响页面），询问是否重新处理。若跳过则停止。

### 第三步：抓取内容

执行 shell 命令：`python scripts/fetch.py <SOURCE>`

若失败，告知用户错误原因，记录到 `wiki/log.md`，停止执行。

**若 SOURCE 为本地文件**，将文件复制到 `wiki/assets/`：`cp <SOURCE> wiki/assets/<文件名>`
后续来源引用使用 `../assets/<文件名>` 路径，确保 Obsidian 可直接打开。

### 第四步：读取规范文件

读取 `CLAUDE.md`（Wiki 格式规范和行为准则）。若 FILTER 为 `persona`，读取 `persona.md`。

### 第五步：处理内容

**若 FILTER 为 `persona`：**
根据 `persona.md` 判断内容哪些部分对用户有价值，只提取有价值的部分。若内容完全无关，告知用户并停止执行（建议使用 `--all`）。

**若 FILTER 为 `all`：**
直接处理全部内容，不做筛选。

### 第六步：写入 Wiki 页面

按 `CLAUDE.md` 规范，对每个主题：
1. 检查 `wiki/pages/` 中是否已有对应页面
   - 已有：追加新信息，不覆盖旧内容；冲突信息标注 `⚠️ 待验证`
   - 没有：创建新页面，文件名用小写英文加连字符
2. 每个页面包含完整 frontmatter（tags、updated、sources）
3. 页面间链接使用 `[[页面名]]` 格式

记录所有影响到的页面名称（`affected_pages`）。

### 第七步：更新 wiki/index.md

在 `## 页面列表` 章节下为每个新页面添加：
```
- [页面标题](pages/文件名.md) — 一行中文摘要
```
若页面已存在，更新摘要。

### 第八步：追加 wiki/log.md

```
[YYYY-MM-DDTHH:MM:SS UTC] ingest | <SOURCE> | <affected_pages逗号分隔> | <FILTER>模式
```

### 第九步：更新 sources/registry.json

在 `sources` 数组中添加或更新条目：

```json
{
  "id": "<source_id>",
  "type": "url 或 file",
  "path_or_url": "<SOURCE>",
  "ingested_at": "<ISO时间>",
  "affected_pages": ["<页面1>", "<页面2>"],
  "status": "ingested",
  "mode": "<FILTER>",
  "content_hash": "<正文SHA-256前8位，file类型为null>",
  "last_modified": "<HTTP Last-Modified头，无则null，file类型为null>",
  "etag": "<HTTP ETag头，无则null，file类型为null>"
}
```

### 第十步：推荐关联链接

若 `RECOMMEND` 为 `false`，跳过。

读取 `affected_pages` 中每个页面的 `## 来源引用` 章节，过滤掉已在 registry 中的 URL 和非 http/https 链接，结合 `persona.md` 选出最多 3 条推荐，每条附一句理由。

用户选择：a（立刻 ingest）/ b（加待消化列表）/ c（跳过）

对 `b` 条目在 registry 中新增 `status: "pending"` 条目。

### 第十一步：汇报结果

```
✅ Ingest 完成
- 来源：<SOURCE>
- 模式：persona 筛选 / 全量
- 新增/更新页面：[[页面1]]、[[页面2]]
- 加入待消化列表：B 条（若有）
```
