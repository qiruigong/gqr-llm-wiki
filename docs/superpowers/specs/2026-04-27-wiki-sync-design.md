# wiki-sync 功能设计

**日期：** 2026-04-27  
**功能：** `/wiki-sync` — 检测已 ingest 的 URL 来源是否有更新，重新 ingest 变化内容，并推荐关联链接加入待消化列表

---

## 背景与目标

现有系统通过 `/wiki-ingest`、`/wiki-explore` 主动导入资料，但没有机制检测已处理来源的内容变化。`/wiki-sync` 填补这个缺口：定期运行，自动发现更新、重新 ingest，并通过推荐关联链接帮助用户持续扩展知识库。

---

## 新增 / 修改文件

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `scripts/check_updates.py` | 新建 | HTTP 头优先 + hash fallback 的更新检测脚本 |
| `scripts/registry.py` | 扩展 | `upsert` 支持写入新字段 |
| `.claude/commands/wiki-sync.md` | 新建 | `/wiki-sync` slash command |
| `sources/registry.json` schema | 扩展 | 新增 `content_hash`、`last_modified`、`etag` 字段 |

---

## registry.json Schema 扩展

每条 entry 在现有字段基础上新增：

```json
{
  "id": "91fc906a",
  "type": "url",
  "path_or_url": "https://example.com/article",
  "ingested_at": "2026-04-27T10:00:00+00:00",
  "affected_pages": ["llm-wiki.md"],
  "status": "ingested",
  "mode": "persona",
  "content_hash": "a3f8c2d1",
  "last_modified": "Tue, 01 Apr 2026 12:00:00 GMT",
  "etag": "\"abc123\""
}
```

### status 字段取值

| 值 | 含义 |
|----|------|
| `ingested` | 已处理，内容无变化或已是最新 |
| `pending` | 在待消化列表，等待 ingest |
| `pending_update` | 检测到内容变化，等待重新 ingest |

### 新字段说明

- **`content_hash`**：页面正文内容的 SHA-256 前 8 位，用于无 HTTP 头时的 fallback 对比
- **`last_modified`**：上次 ingest 时 HTTP 响应的 `Last-Modified` 头值，没有则为 `null`
- **`etag`**：上次 ingest 时 HTTP 响应的 `ETag` 头值，没有则为 `null`

旧条目（缺少这三个字段）首次 sync 时视为"无历史记录"，直接走全文 hash 流程完成基准建立。

---

## scripts/check_updates.py

### 职责

只负责检测和更新 registry 状态，**不读取 Wiki 页面，不写入任何 Markdown 文件**。

### 扫描范围

registry 中满足以下全部条件的条目：
- `type = "url"`
- `status = "ingested"`
- `ingested_at` 距今不超过 365 天

### 检测逻辑（每条 URL）

```
1. 发 HEAD 请求（timeout=10s）
   ├─ 请求失败 → 输出 ERROR，跳过此条
   ├─ 有 ETag 且与 registry 记录一致 → 输出 UNCHANGED，跳过
   ├─ 有 Last-Modified 且与 registry 记录一致 → 输出 UNCHANGED，跳过
   └─ 头部不一致 / 无历史记录 / 无这两个头
       └─ 发 GET 请求，抓取正文，计算 content_hash
           ├─ hash 与 registry 记录一致 → 输出 UNCHANGED，更新头部字段
           └─ hash 不一致 / 无历史记录 → 输出 CHANGED
               → 更新 registry：status=pending_update，写入新 hash/头部值
```

### stdout 输出格式

每行一条，供 slash command 的 LLM 解析：

```
CHANGED:<source_id>:<url>
UNCHANGED:<source_id>:<url>
ERROR:<source_id>:<url>:<原因>
```

### 命令行用法

```bash
python scripts/check_updates.py          # 扫描全部符合条件的 URL
python scripts/check_updates.py <url>    # 只检测指定 URL
```

---

## scripts/registry.py 扩展

`upsert` 函数签名扩展，新增可选参数：

```python
def upsert(
    source_id: str,
    source_type: str,
    path_or_url: str,
    affected_pages: list[str],
    status: str,
    mode: str,
    content_hash: str | None = None,
    last_modified: str | None = None,
    etag: str | None = None,
) -> None:
```

`content_hash` / `last_modified` / `etag` 传入时写入，不传时保留原有值（不覆盖为 null）。

---

## .claude/commands/wiki-sync.md

### 用法

```
/wiki-sync        # 检测所有 365 天内的 URL 来源
```

### 执行流程

**第一步：运行检测**

```bash
python scripts/check_updates.py
```

向用户展示扫描摘要：
> 扫描 N 个 URL：M 个有更新，P 个无变化，K 个失败

若 M=0，告知用户：
> 所有来源均无更新。

停止执行。

**第二步：逐条重新 ingest 有更新的来源**

对每个 `CHANGED` 条目，按原来的 mode（`persona` 或 `all`）执行完整 `/wiki-ingest` 流程（从抓取内容开始）。

ingest 完成后，更新 registry：`status=ingested`。

**第三步：推荐关联链接**

读取本次被更新的 `wiki/pages/*.md`，提取 `## 来源引用` 章节中的所有外部 URL。

过滤掉已在 registry 中（`status=ingested` 或 `status=pending`）的 URL。

结合 `persona.md` 判断剩余链接的价值，选出最多 5 条推荐，每条附一句理由：

```
以下链接与本次更新相关，是否要处理？

[1] https://... — 理由（与 persona 的关联）
[2] https://... — 理由
...
```

若无符合条件的推荐链接，跳过此步。

**第四步：用户逐条选择**

对每条推荐，用户输入：
- `a` — 立刻 ingest（走完整 `/wiki-ingest` 流程）
- `b` — 加入待消化列表（registry 新增条目，`status=pending`，`type=url`）
- `c` / 回车 — 跳过

**第五步：汇报结果**

```
✅ Sync 完成
- 重新 ingest：M 个来源，更新 X 个页面
- 立刻 ingest 推荐：A 条
- 加入待消化列表：B 条
- 待消化列表当前共 Z 条（可用 /wiki-ingest <url> 处理）
```

---

## /wiki-ingest 配套扩展

每次 ingest 完成后，`registry.py` 的 `upsert` 写入当时抓取时获得的：
- `content_hash`（正文 hash）
- `last_modified`（HTTP 响应头，无则 null）
- `etag`（HTTP 响应头，无则 null）

这为下次 `/wiki-sync` 提供基准，避免首次 sync 将所有旧条目误判为"无法检测"。

---

## 与现有命令的关系

```
/wiki-ingest   主动输入单条资料（URL 或文件）
/wiki-explore  主动探索页面 / 批量订阅站点
/wiki-sync     被动检测已有 URL 来源的更新 + 推荐关联内容  ← 新增
/wiki-query    向已有知识库提问
/wiki-backup   备份整个项目
```

待消化列表（`status=pending`）的消化方式：直接运行 `/wiki-ingest <url>`。

---

## 不在本次范围内

- `/wiki-sync --pending`：批量消化待消化列表（可作为后续迭代）
- 本地文件的更新检测（文件内容通常不变，意义不大）
- 自动定时运行（依赖外部 cron，超出项目范围）
