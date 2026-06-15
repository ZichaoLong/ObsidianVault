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

其中控制反馈与递归分解先分开推进；Hybrid 只作为后续合流形态：把控制反馈线里的部分确定性 tools 替换为 intelligent subagents，并检验显式状态语义是否仍改善数据质量、归因、纠偏、复用或成本。

| 方向 | 关注对象 | 当前定位 |
| --- | --- | --- |
| 控制反馈 | 运行时控制过程：看哪里、改哪里、如何验证、何时提交或回滚 | 先用确定性 tools / resolver / verifier 验证显式状态语义与局部状态访问 |
| 递归分解与 Memory | 任务 / 问题结构：如何拆分、求解、验证、复用子问题 | 研究 verified subproblem memory、D²、Lean / Kernel / 小模型等候选场景 |
| Hybrid | 过程与问题结构的接口：`load -> subagent -> verify -> commit` | 作为控制反馈线后续压力测试，不作为当前第一阶段主命题 |

直接进入：

- 控制反馈：[[10-control-feedback-token-instruction/current-mainline|当前主线]]
- 递归分解与 Memory：[[11-recursive-decomposition-memory/current-status|当前状态]]
- TIDE：[[20-tide-decentralized-neural-network/README#TIDE / 去中心化神经网络：概览|概览]]

其他入口：

- [[30-technical-notes/README|技术笔记]]
- [[40-index/README|索引]]
