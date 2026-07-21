---
name: requesting-code-review
description: >
  代码审查 Skill。4 审查官并行：Spec Reviewer (🔴Blocker) + Security Auditor (🔴Blocker)
  + Quality Auditor (🟢Advisory↗) + UX Reviewer (🟢Advisory↗)。
  触发：Phase 4 质量层、Dev 完成 Task 后、用户说「审查」「review」。
  所有审查官双轨运行（合规路径 + 对抗路径），报告独立呈现。
version: 2.0.0
---

# 代码审查 Skill

> **YuanForge 的四审查官并行审查执行器。**
> 所有审查官同时启动、双轨运行、各自独立报告。

---

## 触发条件

- Phase 4 质量层：所有 Dev Task Complete
- Conductor 收集所有 ✅完成 信号 → 同时派发 4 个审查官
- 用户说「审查」「review」「检查」

---

## 四审查官并行

```
Dev Task ✅完成
  │
  ├── Spec Reviewer     [🔴 Blocker]  — 对照验收标准 + API 契约
  ├── Security Auditor  [🔴 Blocker]  — P0 全量 / P1 关键 / P2 跳过
  ├── Quality Auditor   [🟢 Advisory]  — 代码质量 + 性能 + DB（同类 3 次升级）
  └── UX Reviewer       [🟢 Advisory]  — UI 还原度 + 无障碍（有界面时触发）

并行规则:
  - 四个审查官同时启动，互不等待
  - 任意 Blocker → 通知其他审查官暂停 → 解决后断点恢复
  - 审查报告各自独立呈现，Conductor 不合并/不重排序/不跨轴比较
```

---

## 审查协议

### 双轨运行（所有审查官）

| 路径 | 行为 | 目的 |
|------|------|------|
| 合规路径 | 逐条对照验收标准/安全清单/质量规范/UI 原型 | 确保显式要求满足 |
| 对抗路径 | 主动构造边界条件、异常输入、极端场景 | 发现验收标准未覆盖的漏洞 |

**硬要求**：每份审查报告必须包含至少 1 条对抗路径尝试记录（即使未发现缺陷，也须记录「已尝试 X 边界条件，未发现缺陷」）。

---

## 各审查官详程

### Spec Reviewer — 🔴 Blocker

对照验收标准 + API 契约：

|| 检查项 | 方法 |
||--------|------|
|| 功能完整性 | 所有验收标准是否实现？ |
|| API 契约一致性 | 接口签名是否匹配 freeze 的契约？ |
|| Scope Creep | 有没有超出范围的改动？ |
|| 遗漏 | 有没有遗漏的验收标准？ |

**输出**：PASS 或 BLOCKER（具体差距列表）

### Security Auditor — 🔴 Blocker

按风险分级投入：

|| 风险等级 | 审计范围 |
||---------|---------|
|| R0（高敏） | 全量：输入验证、权限、注入、加密、依赖漏洞 |
|| R1（标准） | 关键路径：认证、授权、敏感数据流 |
|| R2（低敏） | 跳过 |

**输出**：PASS 或 BLOCKER（具体漏洞 + 风险等级）

### Quality Auditor — 🟢 Advisory↗

代码质量 + 性能 + DB：

|| 检查项 | 方法 |
||--------|------|
|| 代码质量 | 可读性、错误处理、测试覆盖 |
|| 性能 | N+1 查询、不必要的循环、内存 |
|| 数据库 | 索引、迁移、schema 变更 |
|| 模块深度 | 同模块深度自检 |

🟠 警告同模块 ≥ 3 次 → 自动升级 🔴 Blocker

### UX Reviewer — 🟢 Advisory↗

有界面时触发。以 UI Designer 的 V/M/D 旋钮值为基准：

|| 检查维度 | 方法 |
||---------|------|
|| 视觉还原度 | 对照原型，逐像素比对 |
|| 交互一致性 | 对照交互规范 |
|| 无障碍 | 键盘导航、ARIA 标签、色对比度 |
|| 响应式 | 移动/平板/桌面 |

🟠 警告同模块 ≥ 3 次 → 自动升级 🔴 Blocker

---

## 审查结果处理

```
Conductor 收集所有审查结果
  │
  ├─ 四个审查官报告各自独立呈现（不合并）
  │
  ├─ 🔴 Blocker → 全部解决 → 打回对应 Dev → 重新审查
  │   └─ 任意 Blocker → 通知其他审查官暂停 → 解决后断点恢复
  │
  ├─ 🟡 Hard Gate (Tester) → 所有 Blocker 解决后触发
  │
  └─ 🟢 Advisory → 采纳的创建 backlog，豁免的写理由
       └─ 🟠 同模块 ≥3 次 → 强制升级 🔴 Blocker
```
