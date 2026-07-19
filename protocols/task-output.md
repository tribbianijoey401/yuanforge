# Task 产出物协议

> Dev/Reviewer/Tester 完成 Task 后，按此规范输出结果。Conductor 依此判断 Task 是否通过。

---

## Dev 产出物

### 1. 代码文件

提交到仓库，路径与 Dispatch Table 中「产出物」一致。

```bash
git add <files>
git commit -m "feat(task-NNN): <标题>"
```

### 2. 测试结果

```
✅ Task task-003 完成
- 测试: 12 passed, 0 failed
- 覆盖: src/api/users.py 94%
- Commit: a1b2c3d
```

### 3. 踩坑记录

如有，在当前 Workspace 创建或更新 `BUG-NNN.md`；会复用的经验在会话关闭时蒸馏到 `docs/knowledge/pitfalls/`：

```markdown
### PIT-NNN: FastAPI middleware 顺序问题
**日期:** 2026-06-29
**类型:** 后端
**严重程度:** 🟡
**现象:** CORS 不生效
**原因:** middleware 注册顺序错误，CORS 必须在路由前
**修复:** 调整 app.add_middleware() 顺序
**教训:** FastAPI middleware 按注册逆序执行
```

---

## Reviewer 产出物

### Stage 1 — Spec Review

```markdown
## Spec Review: task-003 用户管理 API

| 检查项 | Plan 要求 | 实现 | 判定 |
|--------|----------|------|------|
| POST /users | 返回 201 | ✅ 已实现 | ✅ |
| GET /users/:id | 返回 200 | ✅ 已实现 | ✅ |
| 文件路径 | src/api/users.py | 匹配 | ✅ |

**Verdict:** ✅ SPEC REVIEW PASS
```

### Stage 2 — Quality Review

```markdown
## Quality Review: task-003 用户管理 API

### Critical Issues
- 无

### Important Issues
- [ ] email 校验用正则，建议用 `email-validator` 库

### Verdict: ✅ QUALITY APPROVED
```

---

## Tester 产出物

```markdown
## 测试报告: 用户系统集成

| 指标 | 值 |
|------|-----|
| 总测试数 | 47 |
| 通过 | 47 |
| 失败 | 0 |
| 覆盖率 | 91% |
| 边界覆盖 | ✅ |
| 异常路径覆盖 | ✅ |

**Verdict:** ✅ G3 PASS
```

---

## Conductor 判定逻辑

| Task 状态 | 判定条件 | Conductor 动作 |
|-----------|---------|---------------|
| **done** | Review 输出 APPROVED | 标记 done，检查下游 |
| **retry** | Review 输出 REJECT / 测试 FAIL | 重试（最多 3 次） |
| **blocked** | 3 次仍失败 | PROGRESS.md 记录阻塞，等人工 |
