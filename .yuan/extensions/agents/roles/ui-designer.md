# Yuan Agent Contract: UI Designer

**Extension Namespace:** `ui-designer`
**Extension Schema Version:** `yuan.agent.ui-designer/v1`

## Proposal Contract

### Base Schema

This contract extends `.yuan/core/schemas/PROPOSAL.md`. All Core Envelope fields apply.

### Extension Namespace

`ui-designer`

### Extension Schema Version

`yuan.agent.ui-designer/v1`

### Required Professional Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `design_system` | object | Visual design tokens | See example below |
| `component_specs` | array[object] | Component specifications | See example below |
| `prototype_path` | string | Path to prototype file | `"docs/YYYYMMDD-features/prototype.html"` |
| `design_rationale` | string | Design decisions justification | See example below |
| `template_avoidance` | array[string] | Template patterns explicitly avoided | See example below |

### Design System Example

```yaml
design_system:
  colors:
    primary: "#1A1A2E"
    secondary: "#16213E"
    accent: "#0F3460"
    background: "#F4F1EA"
    text: "#1A1A2E"
  typography:
    display: "Playfair Display"
    body: "Inter"
  spacing:
    base_unit: 4
    scale: [4, 8, 16, 24, 32, 48, 64]
  density: 3
  motion: 4
  variance: 6
```

### Component Specs Example

```yaml
component_specs:
  - component: "Login Card"
    states: ["default", "loading", "error", "success"]
    interactions: ["focus", "hover", "active"]
    accessibility: ["keyboard-navigable", "screen-reader-compatible"]
    prototype_ref: "prototype.html#login"
  - component: "Data Table"
    states: ["empty", "loading", "paginated", "filtered"]
    interactions: ["sort", "filter", "select"]
    accessibility: ["keyboard-navigable", "aria-live-regions"]
    prototype_ref: "prototype.html#table"
```

### Design Rationale Example

```yaml
design_rationale: "采用深蓝+奶油色搭配，呼应企业级产品的专业感与亲和力；Playfair Display 展示字体传递经典稳重，Inter 正文字体确保可读性；非对称布局（VARIANCE:6）打破 SaaS 常见的居中对称，创造记忆点。"
```

### Template Avoidance Example

```yaml
template_avoidance:
  - avoided: "奶油底+陶土色模板"
    reason: "与产品专业定位不符，选择深蓝主色调"
  - avoided: "纯黑+荧光绿模板"
    reason: "仅适合游戏/加密产品，本工具为企业管理平台"
```

### Professional Validation Rules

1. `design_system` MUST declare colors, typography (display + body), spacing, and density
2. `component_specs` MUST cover all user-facing components in the feature
3. `prototype_path` MUST point to an existing file that can be opened in a browser
4. `design_rationale` MUST justify design choices from project theme, NOT from templates
5. `template_avoidance` MUST explicitly list avoided AI template patterns with reasons

### Evidence Binding Rules

UI Designer conclusions require concrete Evidence:
- `prototype_path` MUST reference an actual file that exists and renders correctly
- `design_system` colors MUST be consistent with the project's existing design tokens
- `component_specs` MUST include all interaction states (loading/empty/error/success)

Pure assertions like "design is complete" without a working prototype are rejected.

---

## Excluded Fields (Core Only)

UI Designer extensions CANNOT modify:
- `hypothesis` fields (Designer creates visuals, doesn't define implementation hypotheses)
- `strategy_profile.action_class`
- `atomic_change_set.target_scope` (Designer produces prototypes, doesn't modify implementation code)
- `risk.level` (design changes are advisory and don't affect risk)
- `verification_plan.validators` (Designer produces design evidence, but validation is Core-managed)
