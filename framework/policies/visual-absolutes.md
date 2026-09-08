---
name: visual-absolutes
description: 视觉纪律 — 模板味 UI 的模式识别信号与少数真正 hard constraint，绑定 UI/UX Review 流程
spec_type: rule
version: "2.0.0"
---

# 视觉纪律 Visual Discipline

> **vNext Scope：** 只在 UI Designer 或 UX Reviewer 被 Routing 选中时加载，不进入 Backend、CLI、Document-only 或无 UI Work 的 Context。

> **来源**：参考 MVP 开发专家团的 P0 绝对规则（P0-1 / P0-2 / P0-3），经 Quality v0.2 去绝对化。
> **定位**：本文件区分两类规则——**Hard Constraint**（有上游 Evidence 时才触发，hard fail）与 **Taste Signal / Heuristic**（聚合判断信号，单条不构成 failure）。它不再是一组 universal 禁令：模板味识别知识保留，强度由上游 Evidence 决定。
> **触发角色**：UI Designer 原型产出、Frontend Dev 实现、UX Reviewer 审查，均须对照本文件自检。
> **目的**：防止"看起来能跑"但充满模板套路的 UI 流入主干，同时不因 Yuan 通用偏好改造有 Evidence 支撑的 Project-native 设计。

## Taste 优先级（唯一裁决顺序）

冲突时严格按下列优先级裁决。下层不得覆盖上层：

```text
Product Contract / Acceptance
↓
Accessibility / Platform Hard Constraints
↓
Repository Evidence
↓
Project Design System
↓
Adjacent UI Pattern
↓
Presentation Contract
↓
Industry Evidence
↓
General Taste Heuristics
```

**General Taste cannot override Project-native design.** 本文件中的通用信号全部处于最底层；只有上层的 Evidence 把某个信号升级为 violation 时才 hard fail。

## Hard Constraint（唯一允许 hard fail 的条件）

一条规则只有存在以下上游 Evidence 之一时才 hard fail：

1. **确认的 Product / Brand Contract** —— 例如项目明确声明"functional icons use SVG icon set"，此时 emoji 图标是 violation。
2. **Accessibility requirement** —— 例如对比度、焦点可见、reduced-motion 的明确要求被破坏。
3. **Platform constraint** —— 目标平台的硬性限制被违反。
4. **语义误用影响可用性** —— 结构性元素承载错误语义（如装饰性编号伪装成序列）。

## Taste Signal（聚合判断，不单独构成 failure）

以下模式是 AI 模板味的识别知识。单条 Signal ≠ Failure；只有 **多条信号叠加 + 无 Product/Brand/Repository evidence + 与现有设计明显偏离** 才形成 template-convergence finding：

| Signal | 模式 |
|--------|------|
| 紫粉渐变 | Indigo→Pink 渐变，特别是 + 发光边框 + 毛玻璃的三位一体 |
| emoji 功能图标 | 用 emoji 字符替代统一图标方案 |
| bounce easing | 无 purpose 的弹跳/弹性缓动 |
| glassmorphism | 毛玻璃 + blur + 半透明层叠 |
| large radius | 脱离项目 radius 体系的大圆角 |
| shadow-heavy surfaces | 重阴影堆叠制造层级 |
| card density | 万物皆卡片嵌套 |
| decorative motion | 不服务任务反馈的装饰动效 |
| multiple accent hues | 多强调色混用无角色体系 |

## 保留的 always-hard 规则

以下两条与 taste 无关，是 Product Truth / 可维护性纪律，无条件适用：

## VA-3 禁止 AI 模板味占位 / 文案（hard）

- 禁止 "Lorem ipsum" / "Welcome to Our App" / "Sign up today" 等空洞占位。
- 文案由 `project://docs/WORK.md` 中已确认的 Product Contract 驱动，体现真实业务语义。

## VA-4 禁止硬编码颜色（hard）

- 除 `#fff` `#000` 外，所有颜色通过 Design Token 引用。
- Token 体系由 Architect 在 Plan 的 Spec 段锁定，或沿用 Project Design System。

## 其他信号的判定

### VA-1 emoji 作功能图标（条件性 hard）

- 功能图标优先使用统一描边、可矢量缩放、语义明确的 SVG 图标方案。
- 项目锁定 SVG 图标集 / Product / Accessibility 有明确要求 → violation（Hard Constraint 条款 1）。
- 无上游 Evidence → Taste Signal，交 UX Reviewer 按 Taste 优先级与聚合规则判断。
- **Emoji 检测正则**（信号扫描工具，非自动 fail）：
```
[\x{1F300}-\x{1F9FF}\x{2600}-\x{26FF}\x{2700}-\x{27BF}\x{FE00}-\x{FE0F}\x{1F000}-\x{1F02F}\x{1F0A0}-\x{1F0FF}\x{1F100}-\x{1F64F}\x{1F680}-\x{1F6FF}\x{1F900}-\x{1F9FF}\x{1FA00}-\x{1FA6F}\x{1FA70}-\x{1FAFF}\x{200D}\x{20E3}\x{E0020}-\x{E007F}]
```
- **例外**：emoji 仅允许出现在 UGC / 即时通讯消息中，不作为 UI 功能图标。

### VA-2 紫粉渐变（Taste Signal）

- 识别 `linear-gradient(135deg, #7C3AED→#A855F7→#EC4899)` 及 Indigo→Pink 组合。
- 有 Product/Brand Evidence（品牌禁用色、模板套路冲突）→ violation；否则是 anti-convergence 信号。Indigo `#6366F1` 和 Slate Blue `#4F46E5` 作为纯色使用不构成问题。

### VA-5 弹跳 / 弹性缓动（Taste Signal）

- 识别 `cubic-bezier(0.68, -0.55, 0.265, 1.55)` 等弹跳缓动。
- 项目设计语言本身 playful/bounce → 不得反向改造（Repository Evidence / Project Design System 优先于 General Taste）。
- motion 干扰任务、造成 accessibility 影响或与 visual_intent.motion 冲突 → 升级。

---

## 门禁绑定（触发点）

| 阶段 | 触发角色 | 动作 |
|------|----------|------|
| Phase 2 设计 | UI Designer 原型 + Conductor 抽查 | emoji 正则扫描（Signal 聚合）+ Hard Constraint 核对 |
| Phase 3 实现 | Frontend Dev 实现 + Conductor 联调 | Evidence 冲突的 Signal 修正；VA-3/VA-4 修正 |
| Phase 4 审查 | UX Reviewer 审查 | 按 Taste 优先级与聚合规则出 finding，打回对应角色 |

> *注：`ui-designer.md` 的 AI 模板味反模式（三种收敛风格、占位英雄区等）与本节互补，共同压制"看起来能跑"的模板 UI。*
