# /wiki-ingest

将资料 ingest 进 Wiki 知识库。

**用法：**
- `/wiki-ingest <url或文件路径>` — persona 筛选模式（默认），ingest 后推荐关联链接
- `/wiki-ingest <url或文件路径> --all` — 全量 ingest，跳过筛选
- `/wiki-ingest <url或文件路径> --no-recommend` — 跳过关联链接推荐步骤

---

## 执行步骤

### 第一步：解析参数

从用户输入中提取：
- `SOURCE`：URL 或文件路径
- `FILTER`：若包含 `--all` 则为 `all`，否则为 `persona`
- `RECOMMEND`：若包含 `--no-recommend` 则为 `false`，否则为 `true`

### 第二步：检查是否已处理

运行：
```bash
python scripts/fetch.py <SOURCE>
```

先获取 source_id（输出第一行 `SOURCE_ID:xxxxx`），然后运行：
```bash
python scripts/registry.py <source_id>
```

若返回非 `NOT_FOUND`，告知用户：
> 该资料已于 `[ingested_at]` 处理过，影响页面：`[affected_pages]`。是否重新处理？

等待用户确认后再继续。若用户选择跳过，停止执行。

### 第三步：抓取内容

运行：
```bash
python scripts/fetch.py <SOURCE>
```

若命令失败（URL 无法访问、文件不存在、PDF 解析失败），明确告知用户错误原因，记录到 `wiki/log.md`，停止执行。

**若 SOURCE 为本地文件**，将文件复制到 `wiki/assets/`：
```bash
cp <SOURCE> wiki/assets/<文件名>
```
后续来源引用使用 `../assets/<文件名>` 路径（相对于 `wiki/pages/`），以确保 Obsidian 可直接打开。

### 第四步：读取规范文件

读取以下文件：
- `CLAUDE.md`（Wiki 格式规范和行为准则）
- 若 FILTER 为 `persona`：读取 `persona.md`

### 第五步：处理内容

**若 FILTER 为 `persona`：**
根据 `persona.md` 中的背景、偏好、关注领域，判断内容哪些部分对用户有价值。
- 若内容完全与用户无关，告知用户：
  > 未发现对你有价值的内容（基于 persona.md 的判断）。建议使用 `--all` 标志进行全量 ingest。
  停止执行。
- 若有价值内容，只提取有价值的部分继续处理。

**若 FILTER 为 `all`：**
直接处理全部内容，不做筛选。

### 第六步：写入 Wiki 页面

按照 `CLAUDE.md` 中的格式规范，为每个主题：
1. 检查 `wiki/pages/` 中是否已有对应页面
   - 已有：追加新信息，不覆盖旧内容；冲突信息标注 `⚠️ 待验证`
   - 没有：创建新页面，文件名使用小写英文+连字符
2. 每个页面包含完整 frontmatter（tags、updated、sources）
3. 页面间链接使用 `[[文件名]]` 或 `[[文件名|显示文字]]` 格式

记录所有影响到的页面名称（`affected_pages`）。

### 第七步：更新 wiki/index.md

在 `## 页面列表` 章节下，为每个新页面添加：
```
- [页面标题](pages/文件名.md) — 一行中文摘要
```
若页面已存在，更新摘要。

### 第八步：追加 wiki/log.md

在文件末尾追加：
```
[ISO时间] ingest | <SOURCE> | <affected_pages逗号分隔> | <FILTER>模式
```

### 第九步：更新 registry.json

运行以下逻辑（直接调用 Python 或手动更新文件）：
在 `sources/registry.json` 的 `sources` 数组中添加或更新条目：

> **注意：** 抓取 URL 时，`python scripts/fetch.py` 只返回正文文本。`content_hash` 由 Claude 对该正文的 bytes 计算 SHA-256 前 8 位得出；`last_modified` 和 `etag` 需在抓取时额外发送一次 HEAD 请求获取（或从 fetch 响应头中读取）。file 类型来源三个字段均写 `null`。

```json
{
  "id": "<source_id>",
  "type": "url 或 file",
  "path_or_url": "<SOURCE>",
  "ingested_at": "<ISO时间>",
  "affected_pages": ["<页面1>", "<页面2>"],
  "status": "ingested",
  "mode": "<FILTER>",
  "content_hash": "<抓取时正文内容的SHA-256前8位，file类型为null>",
  "last_modified": "<抓取URL时HTTP响应的Last-Modified头，无则null，file类型为null>",
  "etag": "<抓取URL时HTTP响应的ETag头，无则null，file类型为null>"
}
```

### 第十步：推荐关联链接

若 `RECOMMEND` 为 `false`，跳过此步。

读取 `affected_pages` 中每个 `wiki/pages/*.md` 文件的 `## 来源引用` 章节，收集所有外部 URL。

过滤掉：
- 已在 registry 中（`status` 为 `ingested` 或 `pending`）的 URL
- 非 http/https 链接

结合 `persona.md` 判断剩余链接的价值，选出最多 3 条，每条附一句理由：

```
以下链接与本次 ingest 相关，是否要处理？

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

若无符合条件的推荐链接，静默跳过此步（不向用户展示空列表）。

### 第十一步：汇报结果

向用户汇报：
> ✅ Ingest 完成
> - 来源：`<SOURCE>`
> - 模式：persona 筛选 / 全量
> - 新增/更新页面：`[[页面1]]`、`[[页面2]]`
> - 加入待消化列表：B 条（若有）
