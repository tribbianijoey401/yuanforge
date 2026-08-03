---
name: custom-extension-authoring
description: 在项目内创建可发现、可校验、可更新保留的 Yuan Custom Extension。
---

# Custom Extension 编写

1. 在 `.yuan/extensions/custom/<extension-id>/` 创建 `rules/`、`agents/` 或 `skills/<id>/SKILL.md`；id 使用小写字母、数字和连字符。
2. 创建 `extension.json`，字段为 `schema_version`、`extension_id`、`description`、`rules`、`agents`、`skills`。每个 Catalog Entry 包含 `id`、类别内相对 `path`、`description` 和非空 `use_when`。
3. 运行 `<入口> capability bind-custom <扩展目录> --write`，由 Runtime 计算逐文件 Digest 并原子更新 `extension.json`。
4. 运行 `<入口> capability list`；扩展不应出现在 `custom_errors`，其 id 会变成 `<extension-id>:<item-id>`。
5. 使用 `<入口> capability resolve --skill <命名空间-id>` 验证路由与 Digest。
6. Custom Extension 只能指导 Proposal 或产生 Evidence；不得修改 Core、托管 Profile、Install Record 或六种 Result。

最小未绑定 Descriptor：

```json
{"schema_version":"yuan.custom-extension/v1","extension_id":"team","description":"团队能力","rules":[],"agents":[],"skills":[{"id":"deploy-review","path":"skills/deploy-review/SKILL.md","description":"发布审查","use_when":["发布前"]}]}
```
