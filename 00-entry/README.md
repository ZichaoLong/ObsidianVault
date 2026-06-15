---
type: index
status: active
tags:
  - vault-entry
  - research-notes
---

# 研究笔记入口

当前重点有三条研究线：

- [[10-control-feedback-token-instruction/README|控制反馈 / Token = Instruction]]
- [[11-recursive-decomposition-memory/README|递归分解与 Memory]]
- [[20-tide-decentralized-neural-network/README|TIDE / 去中心化神经网络]]

其中控制反馈与递归分解先分开推进；Hybrid 作为后续合流形态：把控制反馈线里的部分确定性 tools 替换为 intelligent subagents，并检验显式状态语义是否仍改善数据质量、归因、纠偏、复用或成本。

| 方向 | 一等公民 | 核心问题 |
| --- | --- | --- |
| 控制反馈 | 控制器状态 + 可行操作集 | 在某个决策状态下，系统能看什么、改什么、验证什么、提交什么、回滚什么 |
| 递归分解与 Memory | 任务对象 / 子问题对象 | 如何把任务拆成带目标、假设、依赖、输出、验证器和复用边界的中间 artifact |
| Hybrid | 任务对象 -> 状态操作接口 | subagent 产出的子问题 artifact 如何安全写回 workspace，并进入后续控制循环 |

直接进入：

- 控制反馈：[[10-control-feedback-token-instruction/current-mainline|当前主线]]
- 递归分解与 Memory：[[11-recursive-decomposition-memory/current-status|当前状态]]
- TIDE：[[20-tide-decentralized-neural-network/README#TIDE / 去中心化神经网络：概览|概览]]

其他入口：

- [[30-technical-notes/README|技术笔记]]
- [[40-index/README|索引]]
