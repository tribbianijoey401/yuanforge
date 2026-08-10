---
name: seam-agreement
description: >
  Seam 预约定：代码合并边界规范
spec_type: rule
version: "3.0.0"
---

---
name: seam-agreement
description: 前后端接口契约约定 — 前后端 Dev 共享的唯一真相源。首次使用时由前后端 Dev 协商填写。
version: 1.0.0
---

# Seam Agreement — 前后端接口契约约定

> **vNext Scope：** 只在 Work 改变 Cross-module Interface、Frontend / Backend Contract 或 Test Seam 时加载，不是所有 Implementation 的前置 Gate。

> **这是前后端之间的共享约定，不是某一方的约束。**
> 修改此文件需要前后端 Dev 双方确认。
> **首次使用时由 Architect 引导前后端 Dev 共同填写。**

## 约定内容

### 1. 命名规范

- 端点命名：
- 参数命名：
- 错误码格式：

### 2. 数据格式

- JSON schema 规范：
- 分页格式：
- 时间格式：

### 3. 错误处理

- HTTP 状态码映射：
- 错误响应格式：

### 4. 认证方式

- JWT 传递方式：
- Token 有效期：

### 5. 边界情况

- 空值处理：
- 并发场景：
- 超时策略：

### 6. @ptg 字段注解

每个数据字段定义后可附加 `@ptg` 注解，供 CAL 脚本解析生成运行时断言。

**格式**：`@ptg: type=<python_type>, nullable=<bool>, required=<bool>, enum=[...], pattern=/regex/`

**示例**：

    name: string — 用户姓名
    @ptg: type=str, nullable=false, required=true

    status: integer — 状态码
    @ptg: type=int, nullable=false, required=true, enum=[0,1,2], pattern=/^[0-9]+$/

**注解列表**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | str | Python 类型名（str/int/float/bool） |
| `nullable` | bool | 是否允许 null |
| `required` | bool | 是否必填 |
| `enum` | list | 枚举值列表（可选） |
| `pattern` | regex | 正则匹配模式，斜杠包裹（可选） |

若当前 Work 选择 CAL，Tester 根据 `project://docs/WORK.md` 中已确认的 Interface Contract 与 Verification Seam 编写 Project-native contract assertions；Framework 不依赖不存在的固定生成器脚本。

## 变更记录

| 日期 | 变更 | 发起人 | 确认人 |
|------|------|--------|--------|
| — | 初始版本（待填写） | — | — |
