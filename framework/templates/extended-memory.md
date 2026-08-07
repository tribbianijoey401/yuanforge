# Extended Memory Entry

当单条 Pitfall、Regression 或 Convention 需要比 `templates/project/MEMORY.md` 更完整的 Evidence 时使用；内容仍合并进 `docs/MEMORY.md`，不创建第二个 Memory System。

```markdown
### M-NNN：Title

- **Type**：Pitfall / Verified Finding / Preference / Convention
- **Scope**：Module、Platform 或 Workflow
- **Signal**：何时应该召回
- **Observed**：可观察现象
- **Cause**：已验证根因
- **Failed Attempt**：实质不同且有价值的失败尝试
- **Rule**：下次应如何处理
- **Regression**：Test、Check 或 Manual Verification
- **Evidence**：Path、Command、Commit、Issue 或用户确认
- **Supersedes**：可选，替代的旧 Memory ID
```

没有 Verified Cause 的内容只能作为 Work Hypothesis，不能写入长期 Memory。
