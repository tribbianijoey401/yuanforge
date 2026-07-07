# 📐 规范约定 (CONVENTIONS.md)

> **本文件回答："怎么写代码才算对？"**
> 写代码前必读。全体 Agent 共同维护。

---

## 代码规范

### 命名

| 类型 | 规范 | 示例 |
|------|------|------|
| 文件 | 小写 + 连字符 | `user-auth.ts`, `user_model.py` |
| 类 | PascalCase | `UserAuth`, `UserModel` |
| 函数/方法 | camelCase（JS/TS）或 snake_case（Python） | `getUserById`, `get_user_by_id` |
| 常量 | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT` |
| 数据库表 | 复数、snake_case | `users`, `order_items` |

### 目录

```
src/
├── models/        # 数据模型
├── services/      # 业务逻辑
├── api/           # API 端点/路由
├── utils/         # 工具函数
└── config/        # 配置文件
```

---

## Git 规范

### Commit 格式

```
<type>: <简短描述>

<详细说明（可选）>
```

| Type | 用途 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `refactor` | 重构（不改变行为） |
| `test` | 添加/修改测试 |
| `docs` | 文档更新 |
| `chore` | 构建/工具/依赖 |

### 示例

```
feat: 用户注册端点

POST /api/users/register — 邮箱+密码注册，返回 JWT token
```

---

## API 规范

### RESTful 路由

| 方法 | 路径 | 用途 |
|------|------|------|
| GET | `/api/{resource}` | 列表 |
| GET | `/api/{resource}/{id}` | 详情 |
| POST | `/api/{resource}` | 创建 |
| PUT | `/api/{resource}/{id}` | 全量更新 |
| PATCH | `/api/{resource}/{id}` | 部分更新 |
| DELETE | `/api/{resource}/{id}` | 删除 |

### 响应格式

```json
{
  "data": { ... },
  "error": null,
  "meta": { "page": 1, "total": 100 }
}
```

---

## 测试规范

详见 [`.yuan/rules/iron-rules.md`](../.yuan/rules/iron-rules.md) 铁律 Ⅱ。

| 类型 | 范围 | 命名 |
|------|------|------|
| 单元测试 | 单个函数/方法 | `test_<功能>.py` |
| 集成测试 | 多个模块协作 | `test_integration_<场景>.py` |

---

## 安全

- ❌ 禁止硬编码密钥/Token/密码
- ✅ 使用环境变量或 `.env` 文件
- ✅ `.env` 加入 `.gitignore`
- ✅ 敏感配置提供 `.env.example` 模板

---

> *最后更新: 2026-07-07*
