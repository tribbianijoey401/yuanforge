---
name: knowledge-injection
description: >
  Conductor 派发 Task 前的知识注入 Skill。
  根据 Task 模块标签匹配 Pitfall，把摘要注入到子 Agent 的 context 中。
  任何人都能在任何阶段调用。
version: 1.0.0
---

# Knowledge Injection — 知识注入 Skill

> **让知识从"写了不读"变成"不读不行"。**
> Conductor 派发 Task 前，自动匹配相关 Pitfall 并注入 context。

---

## 触发条件

- Conductor 派发任何 Task 前（Tier 1/2/3 均可用）
- Doc Engineer 整理知识时查询相关 Pitfall

---

## 执行步骤

### 步骤 1：提取 Task 模块标签

从 Dispatch Table 或 Task 描述中提取模块关键词：

**来源 1：角色标签**
- `frontend-dev` → `frontend, react, ui`
- `backend-dev` → `backend, sdk, api`
- `db` → `database, migration, schema`
- `sync` → `sync, cloud, aliyun`

**来源 2：Task summary 提取**
- 提取名词：`"pagination"` → `pagination, table, frontend`
- 提取动词+名词：`"fix blank page"` → `blank-page, rendering, frontend`
- 提取专有名词：`"Aliyun SDK"` → `aliyun, sdk, cloud`

**来源 3：上游产出物**
- 如果 Task 依赖某个 Feature → 从 FEATURE.md 提取模块标签
- 如果 Task 修复某个 Bug → 从 BUG-NNN.md 提取关键词

### 步骤 2：匹配 Pitfall

扫描 `knowledge/pitfalls/` 下所有文件，检查 frontmatter 的 `modules` 字段是否匹配：

```bash
# 方法 1：grep frontmatter 中的 modules 字段
for f in docs/knowledge/pitfalls/PIT-*.md; do
    if grep -q "modules:.*<keyword>" "$f"; then
        echo "匹配: $f"
    fi
done

# 方法 2：用 Python 解析 YAML frontmatter（更精确）
python3 -c "
import yaml, glob
keywords = {'frontend', 'table', 'render'}
for f in glob.glob('docs/knowledge/pitfalls/PIT-*.md'):
    with open(f) as fh:
        fm = yaml.safe_load(fh.readline(fh.read().find('---', 3)))
        if fm and keywords & set(fm.get('modules', [])):
            print(f'{f}: {fm[\"summary\"]}')
"
```

### 步骤 3：拼接摘要

对每个匹配的 Pitfall，提取：
- **id**（如 PIT-007）
- **summary**（frontmatter 中的摘要）
- **severity**（frontmatter 中的严重级别）

**摘要格式**（一行一条）：
```
⚠️ 相关 Pitfall:
- [PIT-007] [🔴] 前端空白页：列缺少 dataIndex + localStorage 丢失 render
- [PIT-005] [🟡] 阿里云 SDK：NewClient 缺少 Endpoint 参数
```

**如果无匹配**：
```
ℹ️ 无相关 Pitfall 记录。
```

### 步骤 4：注入 context

将摘要拼接到子 Agent 的 context 中，放在"必读"段之前：

```markdown
## 相关 Pitfall（已读取）
⚠️ 相关 Pitfall:
- [PIT-007] [🔴] 前端空白页：列缺少 dataIndex + localStorage 丢失 render

## 必读
- 角色合约: contracts/{role}.md
- 铁律: .yuan/rules/iron-rules.md
- 上游产出: {file paths}

## 产出
- {expected output files}
```

**关键**：
- 摘要放在最前面 → Agent 第一眼就能看到
- 标注"已读取" → 表明这是 Conductor 主动注入的，不是 Agent 自己找的
- 如果 Pitfall 较多（>5 个），只保留 severity 为 🔴 和 🟡 的

### 步骤 5：可选 — 追加图谱查询结果

配合 `graph-query` Skill 使用：
- 调用 `graph-query` 获取相关知识
- 将图谱结果追加到 Pitfall 摘要之后

```markdown
## 相关知识图谱
FEAT-AUTH → depends: [ADR-003, PIT-005, PIT-007]
```

---

## Pitfall frontmatter 要求

每个 Pitfall 必须包含 `modules` 字段，否则无法被匹配：

```yaml
---
id: PIT-007
object_type: pitfall
modules: [frontend, react, table, render]  ← 必须包含
severity: 🔴 High
---
```

**模块标签规范**：
- 用小写英文，逗号分隔
- 至少 2 个标签：1 个模块名 + 1 个关键词
- 示例：`[frontend, table, pagination]`、`[backend, sdk, aliyun]`、`[auth, security, permission]`

---

## 示例

### 场景 1：派发 Frontend Dev 做分页改造

**提取标签**：`frontend, table, pagination`

**匹配结果**：
```
⚠️ 相关 Pitfall:
- [PIT-007] [🔴] 前端空白页：列缺少 dataIndex + localStorage 丢失 render
- [PIT-012] [🟡] 分页组件：pageState 未持久化导致刷新丢失
```

**注入 context**：
```markdown
## 相关 Pitfall（已读取）
⚠️ 相关 Pitfall:
- [PIT-007] [🔴] 前端空白页：列缺少 dataIndex + localStorage 丢失 render
- [PIT-012] [🟡] 分页组件：pageState 未持久化导致刷新丢失

## 必读
- 角色合约: contracts/frontend-dev.md
- 铁律: .yuan/rules/iron-rules.md
- 上游产出: docs/YYYYMMDD-描述/PLAN.md
```

### 场景 2：派发 Backend Dev 修复 SDK 问题

**提取标签**：`backend, sdk, aliyun, openapi`

**匹配结果**：
```
⚠️ 相关 Pitfall:
- [PIT-005] [🔴] 阿里云 SDK：NewClient 缺少 Endpoint 参数
- [PIT-006] [🟡] 阿里云 SDK：Describe 系列 API 参数命名差异
```

---

## Pitfalls

- **不要注入过多 Pitfall** — 超过 5 个时只保留 🔴 和 🟡，🟢 降级为"可选读"
- **摘要必须准确** — 不要自己编 summary，直接从 frontmatter 复制
- **modules 字段是关键索引** — 没有 modules 字段的 Pitfall 无法被匹配
- **图谱和 Pitfall grep 互补** — Pitfall grep 做精确匹配，图谱做扩展发现
