# Presentation Architecture

本 Reference 用于让展示方式匹配 Content Topology。选择能让任务、关系与变化清晰可见的最小模型；只有每个模型负责独立任务时才组合使用。

## View Models

| View Model | 适用场景 | 必须保留 |
|---|---|---|
| Queue | 人需要按序处理工作并执行下一步动作。 | priority、ownership、order reason |
| Timeline | 工作由 sequence、causality 或 elapsed change 解释。 | time scale、event source、current position |
| Map | location、proximity 或 route change 会改变决策。 | geographic scale、selected place |
| Tree | parent-child structure 是主要关系。 | ancestry、expansion state、current branch |
| Table | 用户比较大量稳定字段或扫描记录。 | sort、filters、column meaning、row identity |
| Board | 工作在离散且有意义的状态间移动。 | state definition、limits、transition ownership |
| Calendar | scheduling、availability 或 date conflicts 驱动行动。 | time zone、range、selected interval |
| Feed | 新事件需要扫描，但不应暗示这是完整历史。 | source、recency、unread/read state |
| Comparison | 决策依赖有限候选集的 trade-offs。 | comparison criteria、selected candidates |
| Detail workspace | 单个对象有足够深度，需要就地检查或修改。 | object identity、unsaved state、return path |
| Form flow | 任务包含有序输入、校验与 commit boundary。 | completion state、validation、resumability |
| Canvas | 空间排列本身需要被编辑或探索。 | zoom、position、selection、collaboration state |

## Selection Contract

- 根据 dominant task 与 relationship topology 选择一个 Primary View Model，并引用决定它的 Content Model 字段。
- 只有独立 subordinate task 无法由主模型清晰表达时，才增加 Secondary View Model，并说明边界与 rationale。
- 至少记录一个 rejected candidate，并说明具体 volume、relationship、priority、transition、action、device 或 continuity fact 为何使它更弱。
- 不得按视觉新奇感选择。只有其保留的 context 与 canonical facts、intended outcome 相匹配时，模型才有效。

## Detail Strategy

根据 task cost，而不是视觉潮流，选择 detail depth：

- 对不打断扫描、短且可逆的澄清，使用 inline detail。
- 集合必须保持可见、且用户需要比较或分流时，使用 side detail。
- 编辑、历史、权限或相关实体需要持续专注时，使用 dedicated detail workspace。
- 对次要证据使用 progressive disclosure；不得隐藏 primary action、current state 或 recovery path。
- 在每一层都保持 object identity、status 与 action consequence 可见。

## Context Continuity

信息仍然有效时，返回集合应恢复用户的工作上下文：

- 为实体、控件与语义区域保持稳定 identity。
- 用户返回或刷新时，保留 selected object、filters、sort、expansion、draft、focus 与有意义的 scroll position。
- 只播报真实变化，不重置无关上下文；区分 record change 与 re-render。
- 无法恢复时，解释变化、保留可恢复输入，并提供清晰返回路径。

## Anti-convergence

不要从预设 color mode、page archetype、density 或知名产品的 visual recipe 开始，也不要因为流行或其他内容使用过就选择某种展示方式。

应改用 System Story 与 Content Model 检验选择：

- 如果关系、任务或变化频率改变，同一结构是否仍然合适？
- 每个区域是否暴露了必要事实或动作？
- 最独特的处理是否由有意义的关系或事件支撑？
- 使用 reduced motion 的人是否仍能感知状态、结果与 recovery path？
