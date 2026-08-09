---
work: workflow-pause-and-update-reporting
work_state: active
workflow: new-feature
stage: implement
agent:
  id: backend-dev
  state: active
quality:
  test: pending
  review: pending
---

# Current Situation

正在把用户主动 Pause 落为所有 Workflow 的统一行为，并让 Update 显式报告未升级路径及原因。

## Last Completed

- 完整保留用户提供的 1016 行 `deep-requirement-discovery` 内容，只追加“不加载外部 References、全文整体加载”的 Framework 接口声明。
- Product Analyst 在模糊、高影响、高不确定或 Solution 先于 Outcome 时先执行 Discovery，再由 Grilling 继承结果形成具体 Spec。
- Routing 与四个 Primary Workflow 只声明 Agent，不再声明或指定 Skill；Product Analyst 根据自己的 Contract 判断两段式 Skill Chain。
- Insight 的 Expected Skill 改由已观察 Agent 的 Contract 推导，不再从 Workflow 推导。
- Update 只替换官方受管资产并原样保留 Project-owned 文件；写入前仅允许 `idle` / `paused` Work 状态。
- 未完成 Work 可保存 Checkpoint 后 Pause，下次 Session 从 Next Action 恢复；Pause 不归档、不清空 `WORK.md`。
- Framework Version 为 `4.0.0-alpha.3`；69 项 Test、Framework Check、Dangling Reference Check、Dashboard JavaScript Syntax Check 与 diff check 全部通过。

## Next

先建立行为回归，再实现 Installer reporting 与统一 Pause Contract。

## Blocker

无
