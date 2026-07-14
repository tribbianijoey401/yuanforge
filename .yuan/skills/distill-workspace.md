---
name: distill-workspace
description: >
  Workspace 知识蒸馏 Skill。覆盖即时蒸馏（Bug 修复时触发）和批量蒸馏（Workspace Close 时触发）。
  即时蒸馏：判断 BUG-NNN.md 是否通用 → 调用 distill-pitfall.sh 生成 PIT-NNN.md。
  批量蒸馏：打勾式 Checklist，确保 FEATURE/ADR 蒸馏、归档、图谱重建。
  任何人能在任何阶段调用。
version: 1.0.0
---

# Distill Workspace — 知识蒸馏 Skill

> **YuanForge 的知识蒸馏引擎。** 把 Runtime 数据转化为长期知识。
> **核心原则**：人类做判断（是否通用），脚本做搬运（填 frontmatter、分段）。

---

## 触发条件

| 类型 | 触发时机 | 执行者 |
|------|---------|--------|
| **即时蒸馏** | 任何 Agent 修复 Bug 后，标记 `BUG-NNN.md` 状态为完成 | 发现者 / Conductor |
| **批量蒸馏** | Conductor 检测到所有 Task 终态，进入 Workspace Close | Conductor |

---

## 即时蒸馏（Bug 修复时）

### 执行步骤

1. **读取 BUG-NNN.md**
   ```
   打开 docs/YYYYMMDD-描述/BUG-NNN-xxx.md
   ```

2. **判断是否蒸馏**（回答三个问题，任一"是"即蒸馏）
   - 这个 Bug 的根因会在其他项目中重复出现？
   - 这个 Bug 的修复模式值得新 Agent 提前知道？
   - 这个 Bug 的教训可以形成一条规则？

3. **调用脚本自动化**
   ```bash
   bash scripts/distill-pitfall.sh docs/YYYYMMDD-描述/BUG-NNN-xxx.md
   ```
   - 脚本自动提取 frontmatter 和正文段落
   - 自动生成 PIT-NNN.md（含完整 frontmatter）
   - 输出 PIT-NNN.md 的路径

4. **标记已蒸馏**
   - 在 BUG-NNN.md 末尾追加：`→ distilled to knowledge/pitfalls/PIT-NNN.md`
   - 避免重复蒸馏

5. **更新 SESSION_LOG**
   - 在 `SESSION_LOG.md` 的「踩坑」段追加：`[PIT-NNN] BUG-NNN 的教训已蒸馏`

### 判断标准速查

| Bug 类型 | 是否蒸馏 | 理由 |
|---------|---------|------|
| 第三方 SDK 参数差异 | ✅ 是 | 通用，新项目也会踩 |
| 特定业务逻辑错误 | ❌ 否 | 一次性，不会重复 |
| API 返回 null 导致渲染崩溃 | ✅ 是 | 通用模式 |
| 配置文件写错路径 | ❌ 否 | 一次性环境错误 |
| 权限模型设计缺陷 | ✅ 是 | 会在新项目中重复出现 |

---

## 批量蒸馏（Workspace Close 时）

### 打勾式 Checklist

> 每个 `- [ ]` 是一步，做完打勾。PIT 标注"即时蒸馏已完成的"，避免重复。

```
## 知识蒸馏 Checklist

- [ ] **FEATURE.md → knowledge/features/FEAT-NNN.md**
  - 读取 docs/YYYYMMDD-描述/FEATURE.md
  - 生成对象 ID: FEAT-{简短名}
  - 创建 knowledge/features/FEAT-NNN.md，填 frontmatter:
      id: FEAT-xxx
      object_type: feature
      lifecycle: knowledge
      owner: architect
      status: verified
      summary: "一句话描述"
      depends: [ADR-xxx]  ← 从 FEATURE.md 关联段提取
      verified_commit: <git log -1 --oneline>
      confidence: verified
      updated_by: <当前角色>
      updated_at: <ISO8601>
      acceptance_criteria: []  ← 从验收标准提取
      api_endpoints: []        ← 从 API 段提取
      files: []                ← 从修改文件段提取
      session: "YYYYMMDD-描述"
  - 正文: 需求描述 + 设计思路 + API 端点表 + 关键文件列表 + 关联链接

- [ ] **ADR-NNN.md → knowledge/decisions/ADR-NNN.md（如有）**
  - 遍历会话中所有 ADR-NNN.md
  - 完整复制正文 + 加 frontmatter:
      id: ADR-NNN
      object_type: decision
      lifecycle: knowledge
      owner: architect
      status: accepted
      date: YYYY-MM-DD
      summary: "一句话描述"
      verified_commit: <当前HEAD>
      confidence: verified
  - 如果 ADR supersedes 旧 ADR → 更新旧 ADR 的 superseded_by

- [ ] **PIT-NNN.md（即时蒸馏已完成，确认即可）**
  - 扫描 knowledge/pitfalls/ 确认无遗漏
  - 如果 BUG-NNN.md 未标注"→ distilled to PIT-NNN" → 执行即时蒸馏

- [ ] **backlog.md 更新（如有未完成任务）**
  - 读 TASK_BOARD.md → 所有非终态任务
  - 追加到 docs/workspace/backlog.md:
      | Task ID | 任务名 | 角色 | 原会话 | 原因 |
      |---------|--------|------|--------|------|
      | T05 | xxx | xxx | YYYYMMDD-描述 | 会话结束未完成 |

- [ ] **归档 Workspace**
  - mv docs/YYYYMMDD-描述/ → docs/archive/YYYYMMDD-描述/

- [ ] **更新 PROGRESS.md**
  - 移除「当前会话」指针（如果指向此会话）
  - 更新「历史会话」表（功能现在在 knowledge/ 中）

- [ ] **蒸馏报告写入 SESSION_LOG**
  - 在 SESSION_LOG 追加 ## 知识蒸馏 段
  - 包含: 蒸馏产出表 / 未蒸馏表 / 未完成任务表

- [ ] **重建图谱**
  - python scripts/build-graph.py --incremental
```

### 蒸馏报告格式

```markdown
## 知识蒸馏

> 蒸馏时间: YYYY-MM-DD HH:MM
> 蒸馏者: Conductor

### 蒸馏产出
| 源 | 目标 | 类型 | ID |
|----|------|------|-----|
| FEATURE.md | knowledge/features/ | feature | FEAT-AUTH |
| ADR-003.md | knowledge/decisions/ | decision | ADR-003 |
| BUG-005.md | knowledge/pitfalls/ | pitfall | PIT-012 |

### 未蒸馏
| 源 | 原因 |
|----|------|
| BUG-006.md | 一次性环境问题，不会重复 |
| TASK_BOARD.md | Runtime 状态，不蒸馏 |

### 未完成任务
| Task ID | 状态 | 已写入 |
|---------|------|--------|
| T05 | 🔨进行中 | workspace/backlog.md |
```

---

## 验证

蒸馏完成后，确认以下各项：

- [ ] knowledge/ 下生成了新文件（至少 1 个）
- [ ] 每个新文件的 frontmatter 包含 id / object_type / lifecycle / status / verified_commit / confidence
- [ ] verified_commit 确实是当前 git HEAD
- [ ] archive/ 下有 Workspace 完整快照
- [ ] PROGRESS.md 不再指向此会话

---

## Pitfalls

- **不要只归档不蒸馏** — 只 mv 到 archive/ = 知识永远困在 archive 中
- **PIT-NNN 编号递增** — 扫描 knowledge/pitfalls/ 下已有文件，取最大序号 +1
- **verified_commit 必须准确** — 蒸馏前执行 `git log -1 --oneline`，不要猜
- **蒸馏 ≠ 归档** — 归档是冻起来，蒸馏是提取有价值的事实
- **即时蒸馏优先于批量蒸馏** — Bug 修完就蒸馏，不等 Close
