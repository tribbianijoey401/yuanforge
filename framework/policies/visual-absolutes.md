---
name: visual-absolutes
description: P0 视觉绝对禁令 — 防止 AI 模板味 UI 的 5 条硬规则，绑定 G2/G3 门禁
spec_type: rule
version: "1.0.0"
---

# P0 视觉绝对禁令 Visual Absolutes

> **vNext Scope：** 只在 UI Designer 或 UX Reviewer 被 Routing 选中时加载，不进入 Backend、CLI、Document-only 或无 UI Work 的 Context。

> **来源**：参考 MVP 开发专家团的 P0 绝对规则（P0-1 / P0-2 / P0-3）。
> **定位**：本规则是 YuanForge 的 UI 质量门禁 — 任何违反以下任一条的 UI 产出，在 G2（Task Gate）/ G3（Integration Gate）必须打回，零容忍。
> **触发角色**：UI Designer 原型产出、Frontend Dev 实现、UX Reviewer 审查，均须对照本规则自检。
> **目的**：防止"看起来能跑"但充满 emoji 图标、紫粉渐变、占位文案的 AI 模板味 UI 流入主干。

---

## VA-1 禁止 emoji 作功能图标

- 任何 UI 中的**功能图标**都必须使用统一描边、可矢量缩放、语义明确的 **SVG 图标方案**（由 Architect 在 Plan 的 Spec 段锁定一套，全项目不混用）。
- 图标尺寸规范：行内 16px / 按钮内 20px / 独立图标 24px。
- ? 用 emoji 字符当功能图标 → 改用锁定图标库的对应语义图标。
- ? emoji 仅允许出现在用户生成内容（UGC）和即时通讯消息中，绝不作为 UI 功能图标。
- **Emoji 检测正则**（门禁时扫描所有产出）：
```
[\x{1F300}-\x{1F9FF}\x{2600}-\x{26FF}\x{2700}-\x{27BF}\x{FE00}-\x{FE0F}\x{1F000}-\x{1F02F}\x{1F0A0}-\x{1F0FF}\x{1F100}-\x{1F64F}\x{1F680}-\x{1F6FF}\x{1F900}-\x{1F9FF}\x{1FA00}-\x{1FA6F}\x{1FA70}-\x{1FAFF}\x{200D}\x{20E3}\x{E0020}-\x{E007F}]
```
- **例外**：emoji 仅允许出现在 UGC / 即时通讯消息中，不作为 UI 功能图标。

## VA-2 禁止紫粉渐变主视觉

- 禁止 `linear-gradient(135deg, #7C3AED→#A855F7→#EC4899)` 及 Indigo→Pink 任意渐变组合。
- Indigo `#6366F1` 和 Slate Blue `#4F46E5` 作为纯色使用允许。
- 红线禁止的是"Indigo→Pink 渐变 + 发光边框 + 毛玻璃"的三位一体 AI 模板套路。

## VA-3 禁止 AI 模板味占位 / 文案

- 禁止 "Lorem ipsum" / "Welcome to Our App" / "Sign up today" 等空洞占位。
- 文案由 `docs/WORK.md` 中已确认的 Product Contract 驱动，体现真实业务语义。

## VA-4 禁止硬编码颜色

- 除 `#fff` `#000` 外，所有颜色通过 Design Token 引用。
- Token 体系由 Architect 在 Plan 的 Spec 段锁定。

## VA-5 禁止弹跳 / 弹性缓动

- 禁止 `cubic-bezier(0.68, -0.55, 0.265, 1.55)` 等弹跳缓动。
- 动效深度匹配 UI Designer 的 MOTION 旋钮值。

---

## 门禁绑定（触发点）

| 阶段 | 触发角色 | 动作 |
|------|----------|------|
| Phase 2 设计 | UI Designer 原型 + Conductor 抽查 | emoji 正则扫描 |
| Phase 3 实现 | Frontend Dev 实现 + Conductor 联调 | 替换 emoji / 去渐变 / 去硬编码 |
| Phase 4 审查 | UX Reviewer 审查 | 打回 Frontend Dev |

> *注：`ui-designer.md` 的 AI 模板味反模式（三种收敛风格、占位英雄区等）与本节互补，共同压制"看起来能跑"的模板 UI。*
