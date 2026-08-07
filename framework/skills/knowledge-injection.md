---
name: knowledge-injection
description: 根据 Work Signal 为其他 Skill 提供 Just-in-time Reference Retrieval，不进行全量知识注入。
version: 4.0.0
---

# Knowledge Injection Skill

## vNext Reference Routing

本 Skill 是通用 Reference Router。先根据 Work、Agent Assignment、Code Path 和 Risk 形成 Retrieval Signal，再读取 `references/README.md` 的 Skill Mapping，最后只加载命中的 Reference Section。

Context 设计必须遵守 `references/01-standards/context-engineering.md` 的 JIT 原则；禁止把全部 Project Memory、全部 Reference 或全文 Index 注入当前 Context。

## Retrieval Procedure

1. 定义当前角色要回答的一个具体问题。
2. 从 Work、Artifact、Technology、Industry、Platform、Failure Mode 和 Risk 中提取 Signal。
3. 先查 Agent Contract 的 Skill Assignment，再查 Skill 自己的 Reference Routing。
4. 只打开一个或少量候选 Reference，并定位具体 Section。
5. 将 Reference Rule 与当前 Repository Fact 对照；冲突时以已验证 Project Fact 为准。
6. 输出 Focused Knowledge Packet，不复制无关章节。

## Project Memory Retrieval

Project Memory 不是 Framework References。检索顺序为：

1. `docs/STATUS.md` 与当前 `docs/WORK.md`
2. 相关 Product / Architecture / Decision Section
3. `docs/MEMORY.md` 中命中 Module、Signal 或 Failure Mode 的条目

不要扫描全部历史 Work，也不要把未验证 Hypothesis 当作 Pitfall 注入。

## Focused Knowledge Packet

```text
Question: 当前需要解决的一个问题
Project Fact: 与问题直接相关的已验证事实
Reference: 文件 + Section
Applicable Rule: 本次真正适用的规则
Conflict / Limit: 与 Project Fact 的差异或时效限制
Suggested Verification: 如何验证该知识适用
```

## Stop Condition

一旦已有足够信息支持下一步 Verification 或 Decision，就停止加载更多 Reference。最新 Version、Price、Law 或 Platform Rule 需要外部可信来源验证，不能只依赖静态 Reference。
