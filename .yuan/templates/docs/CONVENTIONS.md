# 项目规范

> 怎么写代码才算对。全体维护此文件。

---

## 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 文件 | [约定] | `[示例]` |
| 类 | PascalCase | `UserAuth` |
| 函数 | [约定] | `getUserById` |
| 常量 | UPPER_SNAKE_CASE | `MAX_RETRY` |

---

## 目录约定

```
src/
├── models/        # 数据模型
├── services/      # 业务逻辑
├── routes/        # API 端点
└── utils/         # 工具函数
```

---

## Git 规范

- **Commit 格式:** `type: 简短描述`（feat/fix/refactor/test/docs/chore）
- **一个 Commit 一件事**

---

## 安全

- ❌ 禁止硬编码密钥
- ✅ 使用环境变量
- ✅ `.env` 加入 `.gitignore`
