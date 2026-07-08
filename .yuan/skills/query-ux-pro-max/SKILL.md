---
name: query-ux-pro-max
description: 查询 UI-UX-Pro-Max 行业设计知识库，获取特定行业的 UI 惯例、风格推荐、调色板和字体配对。不凭记忆猜测行业 UX 惯例。
trigger: UI Designer 或 UX Reviewer 遇到特定行业/产品类型的 UX 惯例不确定时调用
---

# Query UX Pro Max — 行业 UX 知识查询

> 数据源：[UI-UX-Pro-Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill)
> 仓库中的 CSV 数据文件包含 161 个行业的推理规则、67 种设计风格、调色板、字体配对和 UX 指南。

## 可用数据

| 数据文件 | 内容 |
|---------|------|
| `products.csv` | 161 个产品/行业类型（SaaS、金融、医疗、电商、游戏、美业……） |
| `styles.csv` | 67 种 UI 风格（Glassmorphism / Brutalism / Neumorphism / Bento Grid……） |
| `colors.csv` | 与行业对齐的调色板 |
| `typography.csv` | 57 组字体配对 + Google Fonts import |
| `ui-reasoning.csv` | 161 条行业推理规则（推荐模式 + 风格优先级 + 色彩情绪 + 字体个性 + 反模式） |
| `ux-guidelines.csv` | 99 条 UX 指南（最佳实践 + 反模式 + 无障碍规则） |
| `landing.csv` | 24 种 Landing Page 布局模式 |
| `motion.csv` | 动效推荐 |
| `charts.csv` | 25 种图表类型推荐 |
| `design.csv` | 设计系统生成规则 |

数据文件原始 URL：
```
https://raw.githubusercontent.com/nextlevelbuilder/ui-ux-pro-max-skill/main/src/ui-ux-pro-max/data/<文件名>.csv
```

## 查询方法

### 1. 按行业查询
当 UI Designer 需要做某个行业的视觉规范时：

```bash
# 获取行业推理规则（含推荐风格、色彩情绪、反模式）
curl -sL "https://raw.githubusercontent.com/nextlevelbuilder/ui-ux-pro-max-skill/main/src/ui-ux-pro-max/data/ui-reasoning.csv" | grep -i "<行业关键词>"
```

### 2. 按风格查询
当需要了解某种风格的细节时：

```bash
curl -sL "https://raw.githubusercontent.com/nextlevelbuilder/ui-ux-pro-max-skill/main/src/ui-ux-pro-max/data/styles.csv" | grep -i "<风格名>"
```

### 3. 按产品类型查调色板/字体
```bash
curl -sL "https://raw.githubusercontent.com/nextlevelbuilder/ui-ux-pro-max-skill/main/src/ui-ux-pro-max/data/products.csv" | grep -i "<产品类型>"
```

## 使用原则

- **不凭记忆猜测。** LLM 的训练数据偏向通用场景，行业特定惯例（如医疗行业的色彩规范、金融行业的安全图标惯例）容易出错。不确定时查询数据。
- **按需拉取，不全量加载。** 只 grep 当前项目相关的行业，不下载整个 CSV。
- **查询结果写入产出物。** 将行业惯例引用到 UI Designer 的视觉规范或 UX Reviewer 的审计报告中，注明来源。
