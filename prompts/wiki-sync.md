# wiki-sync prompt

检测已 ingest 的 URL 来源是否有内容更新，重新 ingest 变化内容，并推荐关联链接。

---

## 执行步骤

### 第一步：运行更新检测

执行 shell 命令：`python scripts/check_updates.py`

解析每行输出：
- `CHANGED:<id>:<url>` — 有更新
- `UNCHANGED:<id>:<url>` — 无变化
- `ERROR:<id>:<url>:<原因>` — 抓取失败

向用户展示扫描摘要（有更新数 / 无变化数 / 失败数）。列出失败条目和原因（不中断整体流程）。

若无更新（M = 0），告知用户并停止。

### 第二步：逐条重新 ingest 有更新的来源

对每个 `CHANGED` 条目，按该条目原来的 `mode` 执行完整 wiki-ingest 流程（跳过"检查是否已处理"步骤）。完成后将该条目 `status` 改回 `ingested`。

记录本次更新的所有 Wiki 页面名称（`updated_pages`）。

### 第三步：推荐关联链接

读取 `updated_pages` 中每个页面的 `## 来源引用` 章节，过滤已在 registry 中的 URL 和非 http/https 链接，结合 `persona.md` 选出最多 3 条推荐，每条附一句理由。

用户选择：a（立刻 ingest）/ b（加待消化列表）/ c（跳过）

### 第四步：追加 wiki/log.md

为每个重新 ingest 的来源追加：
```
[YYYY-MM-DDTHH:MM:SS UTC] sync | <url> | <affected_pages逗号分隔> | <mode>模式
```

### 第五步：汇报结果

```
✅ Sync 完成
- 重新 ingest：M 个来源，更新 X 个页面
- 立刻 ingest 推荐：A 条
- 加入待消化列表：B 条
- 待消化列表当前共 Z 条
```
