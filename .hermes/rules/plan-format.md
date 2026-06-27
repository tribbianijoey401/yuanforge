# Plan 工程化格式规范 (Pipeline as Code)

> YuanForge 的 Implementation Plan 不是自由文本，而是一个**可被机器（Agent）精确解析和执行的工程化 Pipeline**。

---

## Plan 结构总览

```yaml
# 一个完整的 Plan = 元信息 + Stage 序列 + Gate 定义

Plan:
  Meta:           # 元信息
    feature:      # 功能名称
    goal:         # 一句话目标
    mode:         # strict | fast
    stack:        # 技术栈决策（写入 DECISIONS.md）

  Stages:         # 阶段序列（Pipeline）
    - Stage: 1    # 每个 Stage = 一组 Task + 一个 Gate
      purpose:    # Stage 目标
      tasks:      # Task 列表
      gate:       # Stage 出口 Gate

  Gating:         # 全局门禁规则
    max_retries:  # Task 审查最大重试次数（默认 3）
```

---

## Plan 模板

```markdown
# [Feature Name] Implementation Plan

> **Pipeline ID:** YYYY-MM-DD_HHMMSS-<slug>
> **Mode:** strict | fast
> **Stack:** [语言] + [框架] + [数据库] + ...

---

## Stage 1: 基础设施

**Purpose:** 搭建项目骨架，为后续功能铺路
**Gate:** G1-INFRA — 项目必须能启动、通过 health check

### Task 1.1: [任务名]
- **Objective:** [一句话目标]
- **Files:** 
  - Create: `path/to/file`
  - Modify: `path/to/file`
- **Input:** [依赖的前置 Task 或外部条件]
- **Output:** [Task 产出的文件/功能]
- **Test:** `pytest tests/path -v`
- **Gate Check:** [G1-INFRA 的相关检查项]

### Task 1.2: ...
```

---

## Task 规范

每个 Task 必须包含以下字段：

| 字段 | 必需 | 说明 |
|------|------|------|
| `Objective` | ✅ | 一句话目标，Agent 用来判断是否完成 |
| `Files` | ✅ | `Create:` / `Modify:` 精确路径 |
| `Input` | ✅ | 前置依赖：依赖哪个 Task 的产出？ |
| `Output` | ✅ | 交付物：文件/接口/功能 |
| `Test` | ✅ | 验证命令 + 预期结果 |
| `Gate Check` | ✅ | 对应 Gate 的具体检查项 |
| `Code` | 推荐 | 关键代码骨架（非完整实现，给方向） |
| `Pitfalls` | 推荐 | 已知陷阱（从过去项目经验中提取） |

---

## Gate 规范

每个 Stage 出口有一个 Gate，格式：

```markdown
## Gate: G<n>-<NAME>

**Position:** Stage <n> → Stage <n+1>
**Owner:** [Architect | Reviewer | Tester | DevOps]

**Pass Criteria (AND):**
- [ ] 条件 1（可验证的）
- [ ] 条件 2
- [ ] 条件 3

**Fail Action:**
- On 1st failure: 回当前 Stage，修复后重试
- On 3rd failure: 触发架构复盘（Architect 介入）

**Artifacts Required:** [证明通过的文件/日志]
```

---

## 完整示例：「用户认证」的工程化 Plan

```markdown
# User Authentication — Implementation Plan

> **Pipeline ID:** 2026-06-27_210000-user-auth
> **Mode:** strict
> **Stack:** Python 3.11 + FastAPI + SQLite + bcrypt + JWT
> 
> **Gate Strategy:** G1(INFRA) → G2(TASK per-task) → G3(INTEG) → G4(RELEASE)

---

## Stage 1: 基础设施

**Purpose:** 搭建项目骨架，确保可运行
**Gate:** G1-INFRA → 项目启动 + health check 通过

### Task 1.1: 初始化 FastAPI 项目
- **Objective:** 创建 FastAPI 项目骨架，含 health endpoint
- **Files:**
  - Create: `src/main.py`
  - Create: `src/__init__.py`
  - Create: `requirements.txt`
- **Input:** 无
- **Output:** `curl localhost:8000/health → {"status": "ok"}`
- **Test:** `pytest tests/test_health.py -v`
- **Gate Check:** [G1-INFRA] 项目启动不报错
- **Pitfalls:** FastAPI 需要用 `async def`，别忘了 uvicorn

### Task 1.2: 初始化数据库
- **Objective:** 配置 SQLite + SQLAlchemy，创建 User 表
- **Files:**
  - Create: `src/database.py`
  - Create: `src/models/user.py`
- **Input:** Task 1.1（项目骨架）
- **Output:** User 表可 CRUD
- **Test:** `pytest tests/test_database.py -v`
- **Gate Check:** [G1-INFRA] 数据库连接正常、migration 成功

## Gate: G1-INFRA

**Position:** Stage 1 → Stage 2
**Owner:** Architect

**Pass Criteria (AND):**
- [ ] `uvicorn src.main:app` 无报错启动
- [ ] `curl /health` 返回 200
- [ ] 数据库 migration 成功
- [ ] 所有 Stage 1 测试 PASS

**Fail Action:** 回 Stage 1 对应 Task 修复
**Artifacts Required:** `pytest tests/ -q` 输出

---

## Stage 2: 核心功能

**Purpose:** 实现注册 + 登录
**Gate:** G2-TASK（每个 Task 后执行两阶段审查）

### Task 2.1: 密码哈希工具
- **Objective:** 实现 bcrypt 密码哈希和验证函数
- **Files:**
  - Create: `src/auth/hash.py`
  - Create: `tests/test_hash.py`
- **Input:** 无
- **Output:** `hash_password()` / `verify_password()` 函数
- **Test:** `pytest tests/test_hash.py -v`
- **Gate Check:** [G2-TASK] Spec Review + Quality Review
- **Code:**
  ```python
  import bcrypt
  
  def hash_password(password: str) -> str:
      return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
  
  def verify_password(password: str, hashed: str) -> bool:
      return bcrypt.checkpw(password.encode(), hashed.encode())
  ```
- **Pitfalls:** bcrypt 的 `gensalt()` 默认 rounds=12，测试环境可能太慢

### Task 2.2: 注册端点
- **Objective:** POST /register 创建用户
- **Files:**
  - Create: `src/auth/router.py`
  - Modify: `src/main.py`（挂载 router）
  - Create: `tests/test_register.py`
- **Input:** Task 1.2（数据库）+ Task 2.1（密码哈希）
- **Output:** 注册端点可创建用户
- **Test:** `pytest tests/test_register.py -v`
- **Gate Check:** [G2-TASK] Spec Review + Quality Review

## Gate: G3-INTEG

**Position:** Stage 2 → Stage 3
**Owner:** Tester

**Pass Criteria (AND):**
- [ ] 所有 Stage 2 Task 的 G2 全部 PASS
- [ ] `pytest tests/ -q` 全量 PASS
- [ ] 注册 → 登录 端到端流程可走通
- [ ] 无未处理的 Review Issue

**Fail Action:** 回对应 Task 修复
**Artifacts Required:** 全量测试输出 + 端到端手动验证记录

---

## Stage 3: 收尾

### Task 3.1: 补充边界测试
- **Objective:** 补充空输入、超长密码、SQL 注入等边界测试
- **Input:** Stage 2 所有产出
- **Test:** `pytest tests/ -v --cov=src/ --cov-report=term`

### Task 3.2: CI 配置
- **Objective:** GitHub Actions 自动运行测试
- **Files:**
  - Create: `.github/workflows/ci.yml`

## Gate: G4-RELEASE

**Position:** Stage 3 → 交付
**Owner:** DevOps

**Pass Criteria (AND):**
- [ ] 集成测试 PASS
- [ ] CI 配置可运行
- [ ] ARCHITECTURE.md / DECISIONS.md 已更新
- [ ] README 可运行指令准确

**Artifacts Required:** CI 通过截图 + 文档 diff
```

---

## Plan 与铁律的映射

| Plan 元素 | 对应铁律 |
|-----------|---------|
| `Gate Check` 字段 | **Ⅷ. 质量门禁** |
| `Test` 字段 + TDD 流程 | **Ⅱ. TDD 先行** |
| `Input`/`Output` 字段 | **Ⅴ. 上下文隔离**（精确传递依赖） |
| `Pitfalls` 字段 | **Ⅵ. 文档即代码**（经验沉淀） |
| Stage 顺序设计 | **Ⅶ. 渐进式交付** |
| Git commit 策略 | **Ⅳ. 原子提交** |
