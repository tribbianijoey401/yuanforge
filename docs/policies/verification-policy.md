# Verification Policy — 知识验证规则

> **适用范围**：所有 `docs/knowledge/` 文件的置信度检查。
> **目标**：确保 Knowledge 不凌驾于 Code。

---

## 一、核心原则

> **Code is always the ultimate source of truth. Knowledge is a cached interpretation.**

当 Knowledge 与 Code 不一致时，Code 总是对的。

---

## 二、verified_commit 检查

### Agent 启动时

```
每次 Agent 读取 knowledge/ 文件:
  1. 检查 frontmatter.verified_commit
     ├─ 不存在 → confidence=draft，标记「未验证」
     ├─ 存在但 HEAD != verified_commit → confidence=stale，标记「可能过期」
     └─ HEAD == verified_commit → confidence=verified，直接使用

  2. 如果 confidence=stale:
     a. 发出警告："⚠️ [id] 可能已过期（HEAD != verified_commit）"
     b. 检查 git log verified_commit..HEAD → 判断影响范围
     c. 如果涉及此文件的相关文件有变更 → 重新扫描代码 → 更新 frontmatter
     d. 如果无关文件变更 → 更新 verified_commit = HEAD
```

### Conductor 巡检时

```
定期检查 knowledge/ 文件的 confidence:
  ├─ stale 超过 7 天 → 提升优先级，立即验或标记为 deprecated
  └─ stale 超过 30 天 → 强制标记为 deprecated（未维护 = 不可信）
```

---

## 三、验证操作

| 原 confidence | 验证结果 | 新 confidence | 操作 |
|:---:|---------|:---:|------|
| stale | 与代码一致，无需修改 | verified | 更新 verified_commit = HEAD |
| stale | 代码已变更，需要更新 | stale（保持） | 更新正文，更新 verified_commit → verified |
| verified | 代码变更导致不一致 | stale | 不自动改 — 等待下次读取时标记 |
| draft | 完成设计 | verified | 更新 verified_commit |

---

## 四、过期检测粒度

| 变更类型 | 影响范围 | 检测方式 |
|---------|---------|---------|
| 源文件修改 | 对应 Feature 的 files 字段 | `git diff verified_commit..HEAD -- <file>` |
| API 变更 | 对应 Feature 的 api_endpoints | 扫描路由定义文件 |
| 依赖变更 | depends 指向的 ADR 状态变更 | 读 depends 列表中每个对象的 status |
| 模块重构 | Module 的 directory 字段 | 检查目录是否存在 |

---

## 五、禁止事项

- ❌ confidence=stale 的文件不经验证直接用于决策
- ❌ 手动修改 confidence 字段而不更新 verified_commit
- ❌ 蒸馏时 confidence 设为 verified 但不填 verified_commit
