# Verification Policy — 知识验证规则

> **适用范围**：所有 `docs/knowledge/` 文件的置信度检查 + 知识治理全流程验证。
> **目标**：确保 Knowledge 不凌驾于 Code，所有事实面独立验证。

---

## 一、核心原则

> **Code is always the ultimate source of truth. Knowledge is a cached interpretation.**

当 Knowledge 与 Code 不一致时，Code 总是对的。

> **优先级链**：用户规则 > 项目规则 > Yuan 框架 > Skill（包括 neat-freak）。本 policy 不扩大操作权限。

---

## 二、事实面六维矩阵（← NF-02 吸收）

每次知识治理必须覆盖以下 6 面，每面独立标记状态。小项目不必硬凑 6 面：没有部署就没有运行态面，如实标 `not-applicable`，不要编造证据。

| 事实面 | 验证内容 | 可用状态 |
|--------|---------|---------|
| 代码 | 现在真正实现了什么？ | `verified-current` / `changed-and-verified` / `pending` / `out-of-scope` / `not-applicable` |
| 运行态 | 用户实际得到什么？ | 同上 |
| 文档 | 人和下游看到的是不是现役答案？ | 同上 |
| 规则 | Agent 收到的约束是否同源、可执行、无死引用？ | 同上 |
| 记忆 | 快照是否仍准确且允许修改？ | 同上 |
| 工作区 | 是否仍有未集成或未审计的残留？ | 同上 |

**关键规则**：
- 不要把 `git status` 干净、PR 已合并或测试通过单独当成「全部同步」
- 发布状态必须区分 `draft`、`PR`、`merged`、`deployed`、`live verified`、`knowledge closed` 和 `cleaned`
- 每一条差异必须写清 `source of truth → stale surfaces → intended action → verification`

---

## 三、证据层级系统（← NF-10 扩展）

原 `verified_commit` 机制保留，新增 9 种结论各自需要的最低证据：

| 结论 | 最低证据 |
|------|---------|
| "文档链接有效" | 项目自己的 doc-link/index check 或逐链接存在性 |
| "规则已同源" | `realpath`/`readlink`/import + 平台实际加载顺序 |
| "代码实现是 X" | 当前目标分支代码、schema、配置与相关测试 |
| "PR 已完成" | PR state=merged + merge commit；**不能推导已部署** |
| "已部署" | deploy marker/release 指向目标 commit + 服务 active |
| "用户已看到新版本" | canonical 用户 URL/API 的真实响应，必要时同时比 origin/cache |
| "可安全清场" | merged + production contains change + knowledge receipt + lane clean + 无唯一未集成文件 |
| "已获准清场" | 完整结果已向用户汇报 + 用户在该汇报后明确确认可以清场 + 现场要求的确认凭证 |
| "整个项目干净" | 项目内所有适用事实面 verified；warning、pending 和 out-of-scope 单列 |

**铁律**：代码直觉、旧 memory、commit message 和 cache-buster URL 都只能当线索，不能单独证明生产终态。

---

## 四、真相矩阵模板（← NF-11 新增）

对每个发现至少记录：

```text
topic: <事实主题>
authority: <当前权威来源>
code: verified-current | stale | n/a
runtime: verified-current | stale | unverified | n/a
docs: verified-current | stale | changed
rules: verified-current | stale | changed | n/a
memory: verified-current | stale | generated-read-only | changed | n/a
action: <做了什么或为什么没做>
verification: <命令、页面或门禁>
```

用户不需要看到完整矩阵，但最终摘要必须保留未闭合状态。

---

## 五、发布状态机（← NF-12 新增）

```text
implemented
  -> locally verified
  -> pushed / PR opened
  -> CI + required backtest/visual review passed
  -> merged
  -> deployed
  -> live verified
  -> knowledge closed + receipt recorded
  -> full result reported while evidence is preserved
  -> user explicitly approved cleanup after the report
  -> workspace cleaned
  -> post-cleanup audit passed
  -> cleanup result appended
```

- 跳过的状态必须有项目规则允许的原因
- 失败停在哪一格，就按那一格汇报，不能用"基本完成"覆盖
- 只验证其中一个表面时，在结论里明确限制范围

---

## 六、缓存和多表面产品验证（← NF-13 新增）

当用户可见内容经过 CDN、边缘缓存、搜索索引、异步 worker 或多客户端时，至少识别：

- origin 是否为新内容
- canonical URL 是否仍为旧缓存
- API/页面/通知/RSS 是否共享同一数据出口
- deploy marker 是否在所有异步进程真正切换之后才写
- cache-buster 是否只是诊断，而非真实用户验收

---

## 七、清场前 Gate（← NF-14 新增）

清场会销毁复盘和用户复核证据，因此顺序固定为：

1. 验证目标工作已集成并上线
2. 同步 docs/rules/获准记忆
3. 记录项目要求的 knowledge closeout receipt
4. 预览待删除 worktree/branch/db/artifact
5. 检查 dirty 文件和 patch equivalence
6. 向用户完整汇报结果并保留上述现场
7. **等待用户在看完汇报后明确确认可以清场**
8. 记录项目要求的用户确认凭证并执行授权的清理
9. 重新运行 workspace audit，补充汇报清场结果

**铁律**：用户最初任务中的"收尾并清理""做完删掉"等预授权**不替代第 7 步**；确认必须发生在完整汇报之后，因为用户要先看到结果才能判断是否需要保留现场继续复核。

---

## 八、verified_commit 检查（保留原有）

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

## 九、验证操作

| 原 confidence | 验证结果 | 新 confidence | 操作 |
|:---:|---------|:---:|------|
| stale | 与代码一致，无需修改 | verified | 更新 verified_commit = HEAD |
| stale | 代码已变更，需要更新 | stale（保持） | 更新正文，更新 verified_commit → verified |
| verified | 代码变更导致不一致 | stale | 不自动改 — 等待下次读取时标记 |
| draft | 完成设计 | verified | 更新 verified_commit |

---

## 十、过期检测粒度

| 变更类型 | 影响范围 | 检测方式 |
|---------|---------|---------|
| 源文件修改 | 对应 Feature 的 files 字段 | `git diff verified_commit..HEAD -- <file>` |
| API 变更 | 对应 Feature 的 api_endpoints | 扫描路由定义文件 |
| 依赖变更 | depends 指向的 ADR 状态变更 | 读 depends 列表中每个对象的 status |
| 模块重构 | Module 的 directory 字段 | 检查目录是否存在 |

---

## 十一、禁止事项

- ❌ confidence=stale 的文件不经验证直接用于决策
- ❌ 手动修改 confidence 字段而不更新 verified_commit
- ❌ 蒸馏时 confidence 设为 verified 但不填 verified_commit
- ❌ 同一失败第二次出现时盲重试 — 停止，重新检查假设、环境和命令名
- ❌ 任何未验证项保持 `pending`，不要为了摘要好看把它降格成 warning

---

## 十二、验证失败时

- 同一失败第二次出现，停止盲重试，重新检查假设、环境和命令名
- 门禁要求机器可读 metadata 时，补正确留痕并触发新事件；不要用人工确认绕过可修复的格式问题
- 失败发生在生产写入前，明确说"尚未影响生产"；发生在切流后，先确认当前 active release 和回滚边界
- 任何未验证项保持 `pending`，不要为了摘要好看把它降格成 warning
