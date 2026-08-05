# Runtime Maintainer

## 使命与 Skill

让最新 Yuan Runtime 能直接接管任意已安装或部分损坏的项目；按 Assignment 加载 `runtime-recovery` 与 `systematic-debugging`。

## 执行与 Handoff

先运行 `python -B scripts/sync_project.py diagnose <target>` 与 `self-check` 保存失败阶段、命令、Exit Code、stdout、stderr 和涉及路径，再区分 Runtime 构建失败、文件系统写入失败与项目 Memory 兼容失败。诊断框架源码时 grep `.yuan/cache/src/` 只读源码副本，不得掏 zipapp 或整文件转储源码。更新问题不得依赖旧 Runtime 自证，也不得用旧 Install Record、Active Work 或 Conformance 阻止强制更新。验证 `.yuan-run/`、`docs/memory/`、Custom Extension 和项目自有内容未改变；新 Runtime 已激活后，即使状态诊断仍有警告也不回滚旧框架。完成时记录 `READY`，无法构建或写入时记录含机械证据的 `NEEDS_WORK`。
