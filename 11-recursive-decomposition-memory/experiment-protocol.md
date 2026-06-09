---
type: experiment-protocol
status: active
tags:
  - recursive-decomposition
  - memory
  - experiment
---

# 递归分解与 Memory：实验协议

这份文档只回答怎么实验，不承担历史叙事。

当前实验目标：

> 检验结构化分解多样性、分歧熵路由、trace-aware arbitration、verified subproblem memory 分别以及组合后，是否在强 agentic baseline 和成本账本下形成稳定收益。

## 总体设计

当前至少拆四个变量。

| 变量 | 问题 | 强对照 |
| --- | --- | --- |
| Decomposition diversity | 多种结构化分解风格是否比同质采样更有用 | same prompt x3、self-consistency、random prompt variants |
| Entropy routing | 分歧熵是否是有效难度信号 | random routing、HCE routing、fixed voting、oracle difficulty upper bound |
| Trace-aware arbitration | arbiter 是否真的从失败 traces 中获益 | answer-only arbiter、no-trace re-solve、random trace、corrupted trace |
| Memory | verified subproblem / failure memory 是否有复用价值 | no memory、raw trace memory、final-answer memory、unverified memory |

不能只比较 `D² vs CoT`。这个对照可保留为展示，但不足以证明机制。

## Stage 0：复现和成本账本

先复现 Phase 1 的关键数字。

必须记录：

- model。
- decoding policy。
- prompt version。
- benchmark version。
- sample split。
- total generated tokens。
- total input tokens。
- model calls。
- batch size。
- wall-clock。
- GPU type。
- arbitration fraction。

成本至少报告四种口径：

| 口径 | 含义 |
| --- | --- |
| calls | 几次模型调用 |
| tokens | 总输入和输出 token |
| wall-clock | 实际延迟，允许 batching 优势 |
| compute-normalized | 用 token / FLOPs 近似的成本归一化准确率 |

如果只在 wall-clock 口径赢，而 token / compute 口径不赢，结论应收缩为：

> batching 工程下的 latency Pareto 优势。

## Stage 1：结构化分解多样性

目的：

> 证明收益不是简单多采样，而是结构化 decomposition styles 的错误去相关。

实验组：

| 组 | 描述 |
| --- | --- |
| CoT x1 | 普通单次 CoT |
| SamePrompt x3 | 同一 prompt 运行三次，temperature 可控 |
| SelfConsistency k=3 | 标准 self-consistency |
| PromptVariants x3 | 三个轻微 prompt 变体 |
| StructuralDiversity x3 | IPEV / Algebraic / Atomic |
| StructuralDiversity shuffled | 保留三 prompt 长度和格式，但打乱 decomposition semantics |

主指标：

- accuracy。
- cost-normalized accuracy。
- pairwise error Jaccard。
- all-wrong rate。
- at-least-one-correct rate。
- majority-correct rate。

关键裁决：

> 如果 StructuralDiversity x3 的 error decorrelation 和 majority-correct rate 不稳定优于 SamePrompt / SelfConsistency，D² 的第一层机制不成立。

## Stage 2：分歧熵路由

目的：

> 证明 entropy 不只是事后解释，而是能做自适应计算分配。

实验组：

| 组 | 描述 |
| --- | --- |
| Fixed majority | 始终三票多数 |
| Fixed arbitrate | 所有问题都追加 arbiter |
| Random routing | 按相同 arbitration fraction 随机选题仲裁 |
| HCE routing | 额外 LLM call 做 complexity score |
| Entropy routing | v6 方案 |
| Oracle routing | 用是否错误或 gold difficulty 做上界，不用于主比较 |

主指标：

- cost-normalized accuracy。
- arbitration precision。
- arbitration recall for would-fail cases。
- false arbitration rate。
- missed hard case rate。
- entropy bucket calibration。

关键裁决：

> Entropy routing 至少要在相同 arbitration budget 下优于 random routing，并接近或超过 HCE routing 的 cost-quality Pareto。

## Stage 3：Trace-aware arbitration

目的：

> 证明 arbiter 不是单纯多一次重解，而是利用了失败 traces。

实验组：

| 组 | 描述 |
| --- | --- |
| No arbiter | 分歧时只返回随机或多数规则 |
| Answer-only arbiter | 只给题目和三个答案，不给推理 trace |
| Trace-aware arbiter | 给题目、答案、三条 trace |
| Truncated trace | 每条 trace 固定 token 上限 |
| Compressed trace | 先摘要再给 arbiter |
| Verified trace | 只给通过局部 verifier 标注过的 trace |
| Corrupted trace | 给错配 trace，检测是否被误导 |

主指标：

- arbitration success。
- trace utilization rate。
- correction localization accuracy。
- wrong-trace robustness。
- token cost。

关键裁决：

> 如果 answer-only arbiter 与 trace-aware arbiter 相同，trace memory 不是关键机制。如果 corrupted trace 明显误导，必须引入 trace verification 或压缩策略。

## Stage 4：Memory 消融

目的：

> 证明 memory 不是口号，而是可复用状态。

Memory 类型：

| 类型 | 内容 | 风险 |
| --- | --- | --- |
| final-answer memory | 题目到答案 | 容易变成污染或查表 |
| raw trace memory | 完整自然语言 trace | 噪声大，难复用 |
| failure-pattern memory | 错误类型和修复策略 | 需要归因标签 |
| verified subproblem memory | 子问题、输入、输出、verifier、依赖 | 最接近可复用机制 |
| typed subproblem graph | DAG 节点和边 | 工程复杂，但最能支撑递归分解 |

实验设计：

- family-split benchmark：训练/记忆库与测试题同 family 但不同参数。
- template-heldout benchmark：测试使用未见模板。
- distractor memory：加入相似但错误的 memory。
- stale memory：加入过期或不适用 memory。

主指标：

- memory hit usefulness。
- harmful retrieval rate。
- repair success with memory。
- future-task transfer。
- memory compression ratio。
- verifier pass rate。

关键裁决：

> 如果 memory 只在同模板近邻上有用，应写成 retrieval engineering。如果 verified subproblem memory 能跨参数、跨表面词、跨局部结构复用，才接近本线主张。

## Stage 5：真正递归子问题图

目的：

> 从 flat multi-agent ensemble 走向 recursive decomposition。

子问题节点至少包含：

```text
node_id
parent_ids
input_state
goal
solution
confidence
verifier
status
dependencies
```

操作至少包含：

- split。
- solve。
- verify。
- merge。
- expand_uncertain_node。
- cache_verified_node。
- retrieve_similar_node。

对照：

| 组 | 描述 |
| --- | --- |
| flat D² | 当前 v6 |
| fixed-depth plan-execute | 固定分解深度 |
| recursive DAG no memory | 有子问题图，无复用 |
| recursive DAG with verified memory | 有子问题图，有 verified memory |
| ToT baseline | 树搜索式推理 |

主指标：

- cost-quality Pareto。
- solved subproblem reuse。
- expansion depth。
- merge error rate。
- local repair vs global restart。
- length / depth generalization。

## Benchmark 建议

短期：

- SynthMath-1K。
- Sorting benchmark。
- GSM8K apples-to-bananas。
- AIME / MATH500 作为参考。

中期：

- 可生成 family 的代数题。
- 可生成 family 的组合题。
- 可生成 program synthesis / algorithm tracing。
- 多文件小型代码修复。

Benchmark 必须支持：

- 自动判分。
- 变体生成。
- family split。
- 干扰项注入。
- 子问题 ground truth 或近似 verifier。

## 失败条件

这条线应承认失败的情况：

- D² 只赢 CoT，不赢强 agentic baselines。
- Structural diversity 不优于普通 self-consistency。
- Entropy routing 不优于 random routing。
- Arbiter 不依赖 trace。
- Memory 只产生污染式近邻查表。
- Recursive DAG 的成本超过 flat ensemble，且没有长度或深度泛化收益。
- 成本账本显示收益被额外 token / calls / scaffold 吞掉。

