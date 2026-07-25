# MVP 专家团对标与 YuanForge 优化

> 本文记录：分析 MVP 开发专家团（大湾区靓仔团队）的 8 个角色如何协作，并据此对 YuanForge 框架做的最小可行优化。
> 结论：YuanForge 在"流程 + 门禁 + 对抗式审查 + 循环收敛"上领先，MVP 团在"视觉 P0 硬规则 + 结构化裁决 + 代码组织门禁"上更具体。本次优化把后者补齐进 YuanForge。

---

## 一、MVP 开发专家团怎么做

MVP 专家团由 1 名总监 + 7 名专家组成，走 6 阶段（Phase 0→4 + Spec 即契约），核心靠 **P0 绝对规则 + Harness 门禁 + 五源对齐 + DDAD 文档驱动**。

| 角色 | 核心职责 | 关键产出 / 机制 | 与 YuanForge 映射 |
|------|----------|----------------|-------------------|
| 项目总监（Conductor 等价） | 统筹 7 专家，逐 Phase 门禁，决策有迹可循 | Spec 12 章 + 每 Phase P0 扫描 | ≈ Conductor |
| PM（产品） | 竞品调研 + 3 竞品 2 替代 + 差评挖空白，PRD + RICE | 竞品列表 + 用户画像 + PRD | Product Analyst |
| 架构师 | 技术选型 3 方案对比 + 版本锚定 + ADR | API 清单 + openapi.yaml + DB 清单 + ADR | Architect |
| 设计师 | 8 硬红线 / 7 反模式 / 13 自检 + Design Token | Token json+css + 锁定 SVG 图标库 | UI Designer |
| 前端 | Token 化 + emoji SVG + pro-max 打磨 | 单文件 ≤300 行 + lint/type/test ≤3 轮 + UI 11 项 | Frontend Dev |
| 后端 | 安全 checklist + JWT/RBAC | RESTful API + 幂等 | Backend Dev |
| QA | 测试金字塔 单元→集成→E2E | P0 缺陷归零 + RoleVerdict 结构化 | Tester / Spec Reviewer |
| 运维 | CloudBase/Docker + CI/CD + 回滚 | 部署 + health + 交付包 | Doc Engineer / 部署环节 |

**MVP 专家团 5 个可借鉴机制**
1. **P0 视觉绝对规则**：emoji 图标禁令 + 紫粉渐变禁令 + AI 模板味文案禁令，零容忍、可机扫。
2. **自检循环**：lint → type-check → test 机械三连，失败自动修，最多 3 轮。
3. **RoleVerdict 结构化裁决**：`verdict/pass|fail + blocking[] + advisory[] + evidence[]`，机器可消费。
4. **Spec 即契约（12 章）**：范围锁定 + 版本锚定 + Design Token + EARS 验收 + 内嵌坑 + e2e 验证。
5. **OPEN-DECISIONS 登记**：悬而未决项只追加 + 就地关闭，闭环追踪。

---

## 二、对标差距分析

| 维度 | MVP 团 | YuanForge 现状 | 差距 |
|------|--------|----------------|------|
| 阶段 / 门禁 | Phase 0→4 + Spec，P0 硬规则 | G1/G1.5/G2/G3/G4 + HG1~HG4，**已有门禁** | YuanForge 领先 |
| 对抗式审查 | 对抗路径 + 合规路径 | 对抗路径 + 合规路径 + 三档阻塞 | YuanForge 领先 |
| 视觉 P0 | 8 红线 / 7 反模式 / 13 自检 + **emoji/渐变/占位/硬编码/弹跳 5 禁令** | V/M/D 旋钮 + 模板反模式，**缺 P0 硬禁令** | **待补** |
| 裁决协议 | RoleVerdict 结构化 verdict | 自由 Markdown 结论（靠人判打回/升级） | **待补** |
| 自检循环 | lint/type/test ≤3 轮 | TDD + 对抗式自检（未强制机械三连） | 可增强 |
| Spec 即契约 | 12 章含 Token/EARS/坑/e2e | API 契约 freeze + Dispatch Table，**缺 Token/EARS/坑/e2e** | 可增强 |
| 代码组织 | 目录分层 + 单文件 ≤300 行 | Quality Auditor 含 DB/性能/代码质量段 | **待补代码组织段** |
| 像素还原 | 五源对齐（变量/元数据/截图/代码/渲染） | UX Reviewer 还原度审查 | 可增强 |
| 记忆系统 | pitfalls.jsonl + 自学习闭环 | knowledge/pitfalls + knowledge-injection 已覆盖 | 基本等价 |
| 悬而未决 | OPEN-DECISIONS 3 slug | ADR + FEATURE 有"待定"但**无 OPEN-DECISIONS** | **待补** |
| 量化 | role-scorecard 7 维度 | role-scorecard 已有 | YuanForge 领先 |
| 反模式 | — | anti-patterns.md + PTG 提示 | YuanForge 领先 |

**结论**：YuanForge 在"流程骨架 + 门禁 + 对抗式审查 + 循环收敛 + 量化 + 反模式"上领先；MVP 团在"视觉 P0 硬规则 + 结构化裁决 + 代码组织门禁"上更具体。本次优化只补后者，不重复造轮子。

---

## 三、已落地的 YuanForge 优化（待确认）

### 新增 2 个 crown jewels 规则文件
- **`.yuan/rules/visual-absolutes.md`** — P0 视觉绝对禁令 VA-1~VA-5：
  - VA-1 禁止 emoji 作功能图标（含 emoji 检测正则）
  - VA-2 禁止紫粉渐变
  - VA-3 禁止 AI 模板味占位文案
  - VA-4 禁止硬编码颜色（除 #fff/#000）
  - VA-5 禁止弹跳/弹性缓动
  - 绑定 G2/G3 门禁
- **`.yuan/rules/verdict-protocol.md`** — RoleVerdict 结构化裁决协议：`verdict/pass|fail + blocking[] + advisory[] + evidence[]` + 诊断式打回 + 过度设计护栏 + Bounded ≤3 轮

### 改写 5 个合约 + AGENTS.md 的 Checklists（不碰 role-scorecard / anti-patterns.md）
- `contracts/ui-designer.md`：新增「视觉绝对禁令（P0）」段，禁止事项补 VA-1~5，门禁加 emoji 正则扫描
- `contracts/ux-reviewer.md`：新增「Emoji 正则扫描（VA-1）」+「五源对齐」，输出格式前置 verdict-protocol 结构化块，门禁加 VA-1 扫描 + 五源对齐
- `contracts/frontend-dev.md`：禁止事项补 emoji/渐变/硬编码/弹跳，新增「自检循环 lint→type-check→test ≤3 轮」+ emoji 扫描，门禁加自检 + 扫描
- `contracts/quality-auditor.md`：审计表加「代码组织」行（分层/≤300 行/单一职责/入口只装配），新增「代码组织门禁」段，门禁改为五段
- `contracts/architect.md`：新增「Spec 即契约（增强要求）」段（Design Token 锁定 / EARS 验收 / 内嵌已知坑 / e2e 验证 / OPEN-DECISIONS 登记 + 3 slug）
- `AGENTS.md`：核心规则表加 `visual-absolutes.md` / `verdict-protocol.md` 两行；Agent 启动 Checklist 加第 8（UI 任务读视觉禁令）、第 9（审查官读裁决协议）条，原第 8 顺延为第 10

> 说明：**仅新增 + 局部改写**，未触碰任何 YuanForge 既有 G1~G4/HG1~HG4 门禁、role-scorecard、anti-patterns.md 等核心机制。

---

## 四、可选后续增强（未做，待确认）

1. **emoji 正则扫描接入 pre-commit**：把 `visual-absolutes.md` 的正则接到 `scripts/pre-commit`，CI 层拦截（对应 AP-ENV-008 类问题）。
2. **OPEN-DECISIONS 登记**：在 `docs/decisions/` 建 `OPEN-DECISIONS.md`（3 slug + 只追加关闭），由 Doc Engineer 在 Phase 5 蒸馏时归档。
3. **pitfall 自学习闭环**：让 `knowledge-injection` 从"全局注入"升级为"按 package.json 指纹召回相关坑"，对齐 MVP 团的坑触发机制。
4. **Spec 12 章模板**：把 architect.md 的「Spec 即契约」落成 `templates/spec-contract.md`，由 Conductor 在 G1 门禁前要求。
5. **P0 视觉分进 role-scorecard**：在 scorecard 增加"VA 违规数"维度，量化压制模板味。

---

## 五、结论

YuanForge 是"流程框架"，MVP 团是"带 P0 硬规则的实战团"。本次优化把 MVP 团最具体的三块（视觉 P0 禁令、结构化裁决、代码组织门禁）补齐进 YuanForge，不改变其既有门禁与收敛机制，使 YuanForge 在"LLM 即 Runtime"的前提下，多一层可机扫的视觉与裁决硬约束。
