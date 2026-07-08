---
name: debug-feedback-loop
description: Debug 前置阶段 — 构建可复现的反馈循环。必须先有能复现 Bug 的 tight loop，才能进入诊断。
trigger: Dev Agent 进入 Debug 模式后，Conductor 注入本协议作为 Phase 0
---

# Debug Feedback Loop — 构建反馈循环

> 来源：Matt Pocock `/diagnosing-bugs` Phase 1，适配 YuanForge Debug 模式诊断协议包。
> **这是修 Bug 的本质。** 没有能复现 Bug 的 tight loop，二分定位和假设验证都是随机试错。

## Phase 0：构建反馈循环（替代原"隔离复现"）

原诊断协议包的"隔离复现"假设 Bug 已经可以复现。Phase 0 是前置步骤——先把 Bug 变成可复现的。

### 按优先级尝试以下 10 种方式

| 优先级 | 方式 | 描述 |
|--------|------|------|
| 1 | **Failing test** | 在能触及 Bug 的 seam 上写单元/集成/e2e 测试，确认 FAIL |
| 2 | **Curl / HTTP 脚本** | 对运行中的 dev server 发请求，检查响应 |
| 3 | **CLI 调用** | 用固定输入调用，diff stdout 和已知正确快照 |
| 4 | **Headless 浏览器** | Playwright/Puppeteer 驱动 UI，assert DOM/console/network |
| 5 | **回放 trace** | 保存真实请求/payload/事件日志到磁盘，隔离回放 |
| 6 | **一次性 harness** | 启最小系统子集 + mock 依赖，单函数调用触发 Bug 路径 |
| 7 | **Fuzz 循环** | 1000 次随机输入，找 failure mode |
| 8 | **Bisection harness** | 自动化 `git bisect run` |
| 9 | **Differential loop** | 同输入跑旧版本 vs 新版本，diff 输出 |
| 10 | **HITL 脚本** | 需要人操作时，用脚本结构化驱动（贴 `scripts/hitl-loop.sh`） |

### Tighten the loop

拿到一个 loop 后，收紧它：

- **更快？** cache setup、跳过无关初始化、缩小测试范围
- **信号更尖锐？** assert 具体症状，不是"没 crash"
- **更确定？** 固定时间、seed RNG、隔离文件系统、冻结网络

30 秒的 flaky loop ≈ 没有 loop。2 秒的确定性 loop = 调试超能力。

### Non-deterministic Bug

目标是**提高复现率**，不是完美复现。Loop 触发 100×，并行化，加 stress，缩小时间窗口，注入 sleep。50% 复现率的 bug 可调试；1% 不可——继续提复现率。

### 当确实无法构建 loop

停止，明确说尝试了什么。向用户请求：
- (a) 接入可复现的环境
- (b) 捕获的 artifact（HAR/log dump/core dump/录屏+时间戳）
- (c) 允许加临时生产 instrumentation

**不得在无 loop 的情况下进入 Phase 1。**

## 完成标准（Phase 0 出口）

- [ ] 有一个命令（脚本路径 / 测试调用 / curl），已实际执行过至少一次
- [ ] 该命令捕获了**用户描述的精确症状**
- [ ] 确定性（每次同样结果）或高复现率（≥50%）
- [ ] 快（秒级，非分钟级）
- [ ] Agent 可独立运行（无需人参与）

全部 ✅ → 进入原诊断协议包 Phase 1（隔离复现 → 二分定位 → 假设记录 → 并行通知）。
