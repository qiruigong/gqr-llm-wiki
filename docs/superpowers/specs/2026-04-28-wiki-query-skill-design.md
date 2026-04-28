# wiki-query Skill 设计文档

**日期：** 2026-04-28  
**状态：** 待实现

---

## 背景

现有 `/wiki-query` 是一个 slash command，只能由用户手动触发，无法被 agent 程序化调用。目标是将逻辑提取到 skill 中，同时保留用户体验不变。

---

## 目标

- `wiki-query` 逻辑只维护一份（在 skill 里）
- 用户仍可通过 `/wiki-query 问题` 精确触发（slash command 作为薄包装）
- Agent 可通过 `Skill` 工具调用，跳过交互步骤

---

## 架构

```
用户输入 /wiki-query <问题>
    → .claude/commands/wiki-query.md（薄包装，追加 --interactive）
    → ~/.claude/skills/wiki-query.md（完整逻辑）

Agent 调用 Skill("wiki-query", "问题")
    → ~/.claude/skills/wiki-query.md（完整逻辑，--interactive 默认 false）
```

---

## 行为差异

| 场景 | 触发方式 | `--interactive` | 第五步保存询问 | log.md 追加 |
|------|----------|-----------------|----------------|-------------|
| 用户手动 | slash command | true | 保留 | 是 |
| agent 调用 | Skill 工具 | false（默认） | 跳过 | 是 |

---

## 文件变更

### 1. 新建 `~/.claude/skills/wiki-query.md`

完整逻辑从现有 slash command 迁移，新增：
- frontmatter（`name`、`description`、`type`）
- 硬编码 wiki 根路径：`C:\SAPDevelop\kaparthy`
- `--interactive` 参数判断：控制第五步（保存询问）是否执行

**skill 参数格式：**
```
wiki-query <问题>           # agent 调用，非交互
wiki-query <问题> --interactive  # slash command 透传，保留交互
```

### 2. 改写 `.claude/commands/wiki-query.md`

精简为薄包装：读取用户输入的问题，调用 wiki-query skill，追加 `--interactive` 标志。

### 3. 更新 `README.md`

在"命令参考"章节：
- `/wiki-query` 条目下新增"Agent 调用"小节，说明 skill 用法和调用示例
- 更新架构说明，说明 skill 与 slash command 的关系

### 4. 更新 `CLAUDE.md`

无需改动（格式规范与行为准则不涉及调用方式）。

---

## 不在范围内

- 其他 wiki-* 命令的 skill 化（独立任务）
- wiki-query 功能逻辑本身的修改
- 多 wiki 项目路径支持（当前硬编码，够用）
