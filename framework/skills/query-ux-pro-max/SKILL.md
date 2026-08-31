---
name: query-ux-pro-max
description: 查询 UI-UX-Pro-Max 行业设计知识库，获取特定行业的 UI 惯例、风格推荐和 UX 指南。不凭记忆猜测行业 UX 惯例。
trigger: UI Designer 或 UX Reviewer 遇到特定行业/产品类型的 UX 惯例不确定时调用
---

# Query UX Pro Max — 行业 UX 知识查询

## 权限与时机

仅在 Presentation Contract 已选择 View Model、且仍有未决 industry convention 时使用本 Skill（即 View Model 之后）。它只提供条件性建议，不选择 View Model、不替换 content topology，也不规定 visual recipe。

按以下固定优先级应用约束：Product Contract / Acceptance / Repository Fact → Presentation Architecture → Visual Absolutes → Project Design System → query。

不得使用 query 结果覆盖上游事实、frozen Presentation Contract、accessibility requirement 或 project-owned design constraint。

## vNext Reference Routing

- 首先根据 Industry / Product Signal 查询本 Skill 的 `skill://references/*.csv`，只读取匹配行。
- 需要 Design Token：读取 `framework://references/design-systems/token-standard.md` 的相关 Section。
- 需要 Color / Typography / Landing Pattern：分别读取 `framework://references/design-systems/color-palettes.md`、`framework://references/design-systems/typography-pairings.md`、`framework://references/design-systems/landing-patterns.md` 的匹配 Section。
- 已知 Industry：只读取 `framework://references/industries/{industry}.md` 的相关体验原则，不读取全部 Industry Reference。

> 数据内嵌于 `skill://references/`。这里的 Skill Root 是当前 `SKILL.md` 所在目录。来源：[UI-UX-Pro-Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill)

## 可用数据集

| 文件 | 行数 | 内容 |
|------|------|------|
| `skill://references/ui-reasoning.csv` | 161 | 行业 → 推荐模式 + 风格优先级 + 色彩情绪 + 字体个性 + 反模式（**核心文件**） |
| `skill://references/styles.csv` | 67 | UI 风格详情（关键词、适用场景、禁用场景、色彩、动效、实现清单） |
| `skill://references/ux-guidelines.csv` | 99 | UX 最佳实践 + 反模式（导航、表单、无障碍、性能、动效、触摸……） |
| `skill://references/landing.csv` | 24 | Landing Page 布局模式（Hero-Centric / Conversion / Feature-Rich……） |
| `skill://references/products.csv` | 161 | 产品/行业分类索引 |

## 查询方法

> 数据文件位于 `skill://references/`。执行命令前先把逻辑定位符解析成当前 Skill 的真实目录；用本地文本搜索，零网络依赖。

### 1. 按行业查设计建议（最常用）

```bash
# 在核心推理规则中搜索行业关键词
grep -i "<行业关键词>" <skill_dir>/references/ui-reasoning.csv
```

`ui-reasoning.csv` 的列结构：
```
行业名 | 推荐Landing模式 | 风格优先级 | 色彩情绪 | 字体个性 | 关键动效 | 反模式
```

示例：
```bash
grep -i "beauty\|spa\|wellness" <skill_dir>/references/ui-reasoning.csv
# → Beauty/Spa → Soft UI Evolution + Organic Biophilic
# → 色彩: soft pink + sage green + gold
# → 反模式: bright neon colors + harsh animations + dark mode + AI purple/pink gradients
```

### 2. 按风格查详情

```bash
grep -i "<风格名>" <skill_dir>/references/styles.csv
```

`styles.csv` 的列结构：
```
风格名 | 类型 | 关键词 | 主色 | 辅色 | 动效 | 最适合 | 不适合 | 无障碍 | 性能 | CSS关键词
```

示例：
```bash
grep -i "glassmorphism" <skill_dir>/references/styles.csv
# → 关键词: frosted glass, blur, transparency, layered
# → 最适合: modern SaaS, financial dashboards
# → 不适合: critical accessibility, low-contrast environments
```

### 3. 查 UX 最佳实践

```bash
grep -i "<类别>" <skill_dir>/references/ux-guidelines.csv
```

`ux-guidelines.csv` 的列结构：
```
类别 | 问题 | 平台 | 要做 | 不要做 | 代码示例（好） | 代码示例（坏） | 严重度
```

示例：
```bash
grep -i "form\|accessibility\|animation" <skill_dir>/references/ux-guidelines.csv
```

### 4. 查 Landing Page 模式

```bash
grep -i "<模式>" <skill_dir>/references/landing.csv
```

## 查询原则

- **不凭记忆猜测。** LLM 的训练数据偏向通用场景，行业特定惯例（如医疗行业的色彩安全规范、金融产品的信任符号）容易出错。
- **先查 `ui-reasoning.csv`，再按需查辅助文件。** 行业推理规则是入口，风格详情和 UX 指南是被查表用的。
- **查询结果引用到产出物。** 将行业惯例写入 UI Designer 的视觉规范或 UX Reviewer 的审计报告，注明来源。
- **不加载全文件。** `grep` 按行匹配，只读取匹配的行，避免将 300KB+ 的数据注入上下文。
