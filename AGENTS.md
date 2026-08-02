# Yuan Adapter 启动入口

当 `.yuan/config.json` 存在时，在处理项目工作前运行 `yuan status`。以输出的 Work Scope 和 Grant 作为动作边界，通过 Yuan CLI 记录 Attempt 并运行 Verifier。只有 `yuan reduce` 返回 `COMPLETE` 时才能报告完成。

本文件只负责告诉 Agent 平台如何进入 Yuan。它不定义 Core 语义，也不能覆盖已经固定的 Protocol 或 Kernel。
