# YuanCore Capability Schema

> **定位**：统一 Capability 声明格式，所有平台 Adapter 必须遵循。
> **核心原则**：Capability 决定"怎么做"，Core 决定"做什么"。Platform Goal 不成为完成事实源。

---

## 六大标准 Capability

| Capability | 说明 | 有 | 降级 |
|-----------|------|----|------|
| `persistent_goal` | 持久化目标执行（跨会话） | 写入 STATE.md 恢复 | 每会话重新读取 STATE |
| `subagent` | 派发独立子 Agent | 并行派发子 Agent | 同一 Agent 角色切换 |
| `background_execution` | 后台/异步执行 | terminal(background=true) | 同步执行 |
| `file_protection` | 文件原子写入/保护 | write_file/patch 原子操作 | 手动备份后写入 |
| `command_execution` | 任意命令执行 | terminal/子进程 | 受限命令集 |
| `checkpoint_resume` | 执行状态保存与恢复 | STATE.md + Attempt 快照 | 手动 checkpoint 文件 |

---

## Capability 等级

| 等级 | 含义 | 行为 |
|------|------|------|
| `native` | 平台原生支持 | 直接调用 |
| `emulated` | 通过文件模拟 | 写文件/读文件实现 |
| `manual` | 需人工介入 | 提示用户手动操作 |
| `none` | 不支持 | 该能力不可用，流程降级 |

---

## 平台 Goal 映射规则

每个平台的 Goal 必须映射为以下 Core 操作：

```
Goal Tick:
  1. 读取 STATE.md → 获取当前状态和待执行工作
  2. 执行一次 Core Tick（validator → reducer → state update）
  3. 若 Reducer 返回 COMPLETE → 停止，报告完成
  4. 若 Reducer 返回 BLOCKED/WAIT_AUTH/BUDGET_EXIT → 暂停，等待外部输入
  5. 若 Reducer 返回 CONTINUE → 继续下一个 Tick
```

**关键约束**：
- 平台 Goal 的完成 ≠ Core 的 COMPLETE
- Core Reducer 是唯一完成判定源
- 平台 Goal 失败时，Core STATE 保持 BLOCKED 而非 COMPLETE

---

## 降级矩阵

| 缺失 Capability | 降级行为 | 影响 |
|----------------|---------|------|
| no `persistent_goal` | 每会话重读 STATE | 会话切换时需重新加载上下文 |
| no `subagent` | 同 Agent 角色切换 (Tier 3) | 并行降级为串行，效率降低 |
| no `background_execution` | 同步执行 | 无法后台运行，阻塞主会话 |
| no `file_protection` | 写前备份 → 写入 → 验证 | 额外步骤，但功能不变 |
| no `command_execution` | 受限命令集（只读 + 有限写） | 部分任务无法执行 |
| no `checkpoint_resume` | STATE.md 替代 | 恢复粒度变粗（Workspace 级） |

---

## 平台适配验证

每个平台 Adapter 必须通过以下测试：

```
T1: 无 persistent_goal → 新会话可从 STATE 完全恢复
T2: 无 subagent → 串行执行所有 Task，结果一致
T3: 无 background → 同步执行，Core Tick 不阻塞
T4: 无 file_protection → 文件写入正确，无数据丢失
T5: 无 command_execution → 受限模式下 Core Tick 仍推进
T6: 无 checkpoint_resume → STATE.md 包含足够恢复信息
T7: Platform Goal 完成 ≠ Core COMPLETE（独立验证）
T8: Core COMPLETE 时 Platform Goal 正确终止
```

---

## 版本

| 字段 | 值 |
|------|-----|
| schema | yuan.capability/v1 |
| core_dependency | INVARIANTS, REDUCER |
| required_in_core | false |
