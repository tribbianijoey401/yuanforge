# Yuan Insight

只读、自包含、旁路运行的 Yuan Framework 自省与调优模块。观察 Yuan 正常工作时已经产生的 Framework Assets 与 Project State，重建一次 Work 的语义执行路径。

**定位：** Yuan 官方能力，但工程上可选、隔离。Insight 失败/删除不影响 Yuan。

## 设计铁律

- 只读：不修改 WORK/STATUS/MEMORY，不参与 Routing，不阻塞 Agent
- 可选：删除 `.yuan/insight` 不影响 Yuan 任何流程
- Fact First：没有事实来源的字段必须 Unknown，禁止假精度
- Expected 来自现有 Framework Definition，不复制规则
- 不做 Event Ledger、不依赖平台 telemetry、不做 exact token、不常驻 LLM
- Trace 与 Signal 分离：Trace 只保存 What Changed，Signal 动态计算 What It Means

## 用法

```bash
pip install -e insight/
yuan-observe <project-root>
```

## 目录

```text
yuan_insight/
├── cli.py          # yuan-observe 入口
├── watcher.py      # file watcher + debounce
├── loader.py       # 读取 Project State 文件
├── parsers/        # status/work/framework 语义解析
├── snapshot.py     # 可观察语义状态快照
├── diff.py         # snapshot diff → transition → facts
├── coverage.py     # observation session / coverage / gap
└── trace.py        # JSONL trace 落盘
```
