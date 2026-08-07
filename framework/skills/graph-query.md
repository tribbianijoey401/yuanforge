---
name: graph-query
description: Extended Profile 的大型 Project 关系检索候选能力；不属于 vNext MVP，也不在默认 Workflow 中激活。
version: 4.0.0
---

# Graph Query Skill

## vNext Reference Routing

本 Skill 不加载 Framework References。它只在七类 Project Document 已无法以可接受成本回答跨 Module 关系问题、且 Project 明确启用 Extended Graph Profile 时使用。

## Boundary

- 默认不创建 Graph、Index、Event 或独立 Truth Source。
- Graph 只能由当前 Product、Architecture、Decision、Work 和 Memory 派生，不能反向覆盖它们。
- Graph Build Artifact 可删除并重建；不得成为 Session Recovery 的前置条件。
- vNext MVP 的 Conductor、Memory 和 Complex Bug Workflow 不依赖本 Skill。
