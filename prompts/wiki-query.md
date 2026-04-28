# wiki-query prompt

向本地 Wiki 知识库提问，获取综合答案；Wiki 无内容时自动 fallback 到 web search 或模型知识。

**参数：**
- `QUESTION`：自然语言问题
- `INTERACTIVE`：`true` 时在回答后询问是否保存为 Wiki 页面（适合交互式调用）；`false`（默认）时跳过询问（适合 agent 程序化调用）

---

## 执行步骤

### 第一步：检查 Wiki 是否为空

读取 `wiki/index.md`。

若文件不存在或页面列表为空（无任何 `- [` 条目），跳到**第三步 fallback**。

### 第二步：搜索相关页面

读取 `persona.md` 了解用户背景（若不存在则跳过）。

读取 `wiki/index.md`，根据 `QUESTION` 判断最相关页面（按相关度排序，最多 5 个），逐一读取完整内容。

若找到相关页面，进入**第四步**。若无相关页面，进入**第三步**。

### 第三步：Fallback — 用自身能力和 Web 搜索回答

1. 若 agent 具备 web search 能力，搜索与 `QUESTION` 相关的资料（最多 3 条），结合结果综合回答
2. 若无 web search 能力，使用自身训练知识回答

在答案末尾标注：`（来源：Web 搜索）` 或 `（来源：模型知识，截止训练日期）`

告知用户：
> Wiki 中暂无相关内容，以上为 fallback 回答。建议将有价值的部分通过 wiki-ingest 收录进 Wiki。

进入**第五步**。

### 第四步：综合答案（Wiki 优先）

根据 Wiki 页面内容，结合 `persona.md` 中用户的背景和偏好综合回答：
- 每个关键信息点标注来源，格式：`（来源：[[页面名]]）`
- 若多个页面有冲突信息，明确列出冲突，不自作主张判断哪个正确

### 第五步：判断是否保存为 Wiki 页面（仅 INTERACTIVE=true）

若 `INTERACTIVE` 为 false，跳过。

若答案具有独立知识价值（跨页面综合分析、fallback 产生了有价值内容等），询问用户是否保存为 Wiki 页面。

若同意，按 `CLAUDE.md` 规范创建新页面，更新 `wiki/index.md`。

### 第六步：追加 wiki/log.md

若 `wiki/log.md` 存在，追加：
```
[YYYY-MM-DDTHH:MM:SS UTC] query | "<QUESTION>" | <引用页面逗号分隔，fallback时写"-"> | -
```
