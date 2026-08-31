# Evidence-driven Frontend Discovery

本 Reference 用于高影响 UI、新产品、重要改版、数据密集界面、关键旅程，或没有可复用设计时。它把需求研究、Repository 事实与 prototype convergence 连接起来；不规定固定访谈轮数，也不预设亮色、暗色、Dashboard 或任何行业视觉配方。

Small Change、已有契约下的局部样式修正和 Complex Bug 默认不进入完整流程；只有变更重新打开页面职责、数据语义或关键 Experience 时才升级。

## 三层真相

设计前持续区分三类信息，禁止互相冒充：

| Layer | Authority | 可以做什么 | 不可以做什么 |
|---|---|---|---|
| Product Truth | canonical Product Contract、Acceptance、Repository Fact | 定义用户、Outcome、Business Rule 与边界 | 被视觉方案或行业建议覆盖 |
| System Capability Evidence | 当前 Repository、API、schema、fixture、运行行为 | 证明系统实际能提供的数据、状态、更新频率与原因 | 把未来规划或推测写成已存在能力 |
| Presentation Decision | Presentation Contract | 决定信息如何分组、排序、比较、反馈与响应 | 创造后端没有的判断、解释或权威结论 |

行业知识只能提供候选和风险提示。即使数据库建议某种风格，已确认的用户偏好、设备约束和 Product Truth 仍优先。

## 研究与收敛顺序

1. **Outcome / Task**：确认目标用户、用户熟练度、主要任务、使用频率、决策成本、设备与语言，以及成功后用户能更快或更准确完成什么。
2. **Product Contract**：冻结 Goal、Scope、Non-goal、Business Rule、关键 Experience、Acceptance、Assumption 与 Risk。不要先从组件或页面外观开始。
3. **Repository Capability Audit**：读取 Repository、API contract、schema、fixture 与运行证据，建立 System Capability Evidence。能从系统确认的事实不要反问用户；无法证明的能力标为 gap / unknown。
4. **Content / Data Model**：列出 entity、关系、priority、co-visibility、volume、states、transitions、freshness 和 actions。对每个数据型 UI 区域完成下方 capability matrix。
5. **View Model / IA**：先声明每个 page responsibility 与 non-responsibility，再选择 Primary View Model、必要的 Secondary View Model、global context 和 navigation；记录至少一个 rejected candidate。
6. **Visual Language**：由内容层级、密度、可访问性、用户偏好、Project token 与真实任务推导视觉语言。行业查询在 View Model 后进行，只作为条件性证据。
7. **Prototype Convergence**：用可浏览原型验证 dominant desktop 与受限宽度；覆盖正常状态和本 Work 相关的 loading、empty、failure、stale、pending、blocked、recovery。根据可区分反馈迭代，不规定机械轮数。
8. **Presentation Contract**：把已经收敛的 derived decisions、source locator、API gap、prototype locator 与 observable acceptance 写入同一 Contract。
9. **Independent Review**：由 UX Reviewer 对照同一 Product Truth、System Capability Evidence 与 Presentation Contract 审查；Reviewer 不另起设计。
10. **Frontend Implementation**：Frontend Dev 只消费 frozen Contract。后端不存在的数据、判断或原因，不得由前端固定文案伪造。

## Data Capability Matrix

每个数据型 UI 区域至少声明：

| UI region / entity | canonical source | fields | freshness | failure / empty semantics | ownership | Frontend boundary |
|---|---|---|---|---|---|---|
| 稳定区域标识 | endpoint、stream、store、fixture 或明确 gap | 原始字段、单位、时间戳、status / reason code | 更新方式、数据时间、stale 阈值 | loading、empty、failure、stale、pending、blocked 的真实含义 | 产生者、校验者、展示者 | 允许的 format / sort / derived display；禁止伪造的判断 |

若一个状态不适用，明确写 `n/a + reason`，不要制造虚假状态。若 source 或字段不存在，把它记录为 API gap，并从当前 UI Acceptance 中降级或移除；不能用“智能判断”“风险说明”等人类化文案掩盖能力缺口。

## Page Boundaries

每个页面或 workspace 都必须说明：

- page responsibility：本页帮助用户观察、比较、研究或执行的唯一主任务；
- non-responsibility：明确哪些任务属于其他页面或后端能力；
- global context：跨页保持的对象、时间范围、模式、数据时效与连接状态；
- entry / exit：如何进入、下一步在哪里、返回时保留哪些 context；
- information priority：首屏 dominant signal、supporting evidence 和 progressive detail。

页面不能因为“有空位”吸收无关任务。任务、下一步、交易执行或审计等内容只有在页面职责要求时才出现。

## Prototype Convergence

- 至少验证 dominant device 的真实可用宽度和一个 constrained width；Web 使用内容驱动断点，不把画布尺寸写死为产品尺寸。
- 用接近真实 volume、长短文本、正负值与时间戳验证 hierarchy 和 density。
- 状态验证以 capability matrix 为准，不为展示完整度凭空添加后端状态。
- 每轮只解决仍会改变结构、语义或关键视觉方向的问题；已确认事实不重复询问。
- 用户说“舒服”“高级”或认可某个原型，只能作为 Visual Language / density 的证据。视觉方向获得认可不等于 Presentation Contract 已完整；仍需检查数据契约、页面边界、状态、响应式、可访问性和实现 locator。

## Freeze Completeness

Presentation Contract 冻结前必须可定位，并至少覆盖：

- Product Truth locator 与稳定 fact / acceptance reference；
- Repository Capability Audit 结果及未解决 API gap；
- page responsibility / non-responsibility、IA、global context；
- Content Model、Data Capability Matrix、Primary / Secondary View Model 与 rejected candidate；
- normal 及适用的 loading、empty、failure、stale、pending、blocked、success、recovery state matrix；
- responsive、accessibility、motion / reduced-motion、Design Token 与 project-owned constraint；
- Visual Language、information priority、detail strategy、context continuity；
- prototype locator、已验证视口 / 状态与未覆盖限制；
- observable acceptance、Non-goal、Review verdict。

`frozen` 是“实现所需语义和证据完整”的状态，不是“有一张漂亮截图”或“用户喜欢这一版”的同义词。
