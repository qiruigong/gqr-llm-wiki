# /wiki-sync

检测已 ingest 的 URL 来源是否有更新，重新 ingest 变化内容，并推荐关联链接加入待消化列表。

**用法：**
```
/wiki-sync
```

---

## 执行前规划

在开始执行前，用 TodoWrite 列出本次任务的具体步骤，等待用户确认后再执行。每完成一步立即用 TaskUpdate 标记完成。

## 执行步骤

### 第一步：运行更新检测

```bash
python scripts/check_updates.py
```

解析每行输出：
- `CHANGED:<id>:<url>` — 有更新
- `UNCHANGED:<id>:<url>` — 无变化
- `ERROR:<id>:<url>:<原因>` — 抓取失败（`<id>` 可能为 `NONE`；`<原因>` 为 `NOT_ELIGIBLE:...` 时含第五段字段，忽略第五段即可）

向用户展示扫描摘要：
> 扫描 N 个 URL：M 个有更新，P 个无变化，K 个失败

若存在失败条目，列出失败 URL 和原因，继续处理其余条目（不因失败中断）。

若 M = 0（无更新），告知用户：
> 所有来源均无更新。

停止执行。

### 第二步：逐条重新 ingest 有更新的来源

对每个 `CHANGED` 条目，按该条目原来的 `mode`（`persona` 或 `all`）执行完整 `/wiki-ingest` 流程（从抓取内容开始，跳过"检查是否已处理"步骤直接重新处理）。

ingest 完成后，调用 registry 更新：将该条目 `status` 改回 `ingested`。

记录本次被更新的所有 wiki 页面名称（`updated_pages`）。

### 第三步：推荐关联链接

读取 `updated_pages` 中每个 `wiki/pages/*.md` 文件的 `## 来源引用` 章节，收集所有外部 URL。

过滤掉：
- 已在 registry 中（`status` 为 `ingested` 或 `pending`）的 URL
- 非 http/https 链接

读取 `persona.md`，对剩余链接判断价值，选出最多 3 条，每条附一句理由：

```
以下链接与本次更新相关，是否要处理？

[1] https://... — 理由（与 persona 的关联）
[2] https://... — 理由
...

每条请输入：a（立刻 ingest）/ b（加待消化列表）/ c（跳过）
```

若无符合条件的推荐链接，跳过此步。

### 第四步：处理用户选择

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

### 第五步：追加 wiki/log.md

在文件末尾为每个重新 ingest 的来源追加一条记录（格式与 wiki-ingest 一致）：
```
[ISO时间] sync | <url> | <affected_pages逗号分隔> | <mode>模式
```

### 第六步：汇报结果

```
✅ Sync 完成
- 重新 ingest：M 个来源，更新 X 个页面
- 立刻 ingest 推荐：A 条
- 加入待消化列表：B 条
- 待消化列表当前共 Z 条（可用 /wiki-ingest <url> 处理）
```

Z 通过读取 registry 中 `status=pending` 的条目数量获得。
