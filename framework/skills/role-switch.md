---
name: role-switch
description: Platform 不支持 Independent Agent 时，由同一 LLM 顺序切换专业角色的降级协作方法。
version: 4.0.0
---

# Role Switch Skill

## vNext Reference Routing

本 Skill 不直接加载 References。每次切换后，由目标 Agent 根据自己的 Skill Assignment 决定 Reference Routing。

## Procedure

1. Conductor 在 `project://docs/WORK.md` 写明目标、Scope、Acceptance、当前 Artifact 和目标角色，并在 `project://docs/STATUS.md` 提交当前 Stage 与目标角色。
2. 保存 Focused Handoff，清除与目标职责无关的临时 Context。
3. 加载目标 Agent Contract 与当前动作需要的 Skill。
4. 目标角色只执行自己的职责，并输出 Conclusion、Evidence、Risk、Verification 和 Next Action。
5. 切回 Conductor，更新 `project://docs/WORK.md` / `project://docs/STATUS.md`，再决定下一角色。

## Limitations

- Persona Switch 不等于 Independent Context，不得把它描述为独立 Reviewer。
- 同一 LLM 已知 Writer 推理时，应优先依赖可执行 Test 和外部 Evidence。
- 不通过用户 Prompt 手工驱动每次切换；Conductor 根据 Routing 自动执行。
- 不创建后台 Runtime、Lock 或 Session Process 维持切换状态。
