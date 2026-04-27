# /wiki-ingest

将资料 ingest 进 Wiki 知识库。

**用法：**
- `/wiki-ingest <url或文件路径>` — persona 筛选模式（默认）
- `/wiki-ingest <url或文件路径> --all` — 全量 ingest，跳过筛选

---

## 执行步骤

### 第一步：解析参数

从用户输入中提取：
- `SOURCE`：URL 或文件路径
- `MODE`：若包含 `--all` 则为 `all`，否则为 `persona`

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

### 第四步：读取规范文件

读取以下文件：
- `CLAUDE.md`（Wiki 格式规范和行为准则）
- 若 MODE 为 `persona`：读取 `persona.md`

### 第五步：处理内容

**若 MODE 为 `persona`：**
根据 `persona.md` 中的背景、偏好、关注领域，判断内容哪些部分对用户有价值。
- 若内容完全与用户无关，告知用户：
  > 未发现对你有价值的内容（基于 persona.md 的判断）。建议使用 `--all` 标志进行全量 ingest。
  停止执行。
- 若有价值内容，只提取有价值的部分继续处理。

**若 MODE 为 `all`：**
直接处理全部内容，不做筛选。

### 第六步：写入 Wiki 页面

按照 `CLAUDE.md` 中的格式规范，为每个主题：
1. 检查 `wiki/pages/` 中是否已有对应页面
   - 已有：追加新信息，不覆盖旧内容；冲突信息标注 `⚠️ 待验证`
   - 没有：创建新页面，文件名使用小写英文+连字符
2. 每个页面包含完整 frontmatter（tags、updated、sources）
3. 页面间链接使用 `[[页面名]]` 格式

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
[ISO时间] ingest | <SOURCE> | <affected_pages逗号分隔> | <MODE>模式
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
  "mode": "<MODE>",
  "content_hash": "<抓取时正文内容的SHA-256前8位，file类型为null>",
  "last_modified": "<抓取URL时HTTP响应的Last-Modified头，无则null，file类型为null>",
  "etag": "<抓取URL时HTTP响应的ETag头，无则null，file类型为null>"
}
```

### 第十步：汇报结果

向用户汇报：
> ✅ Ingest 完成
> - 来源：`<SOURCE>`
> - 模式：persona 筛选 / 全量
> - 新增/更新页面：`[[页面1]]`、`[[页面2]]`
