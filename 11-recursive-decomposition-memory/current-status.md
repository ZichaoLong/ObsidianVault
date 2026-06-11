---
type: current-status
status: active
tags:
  - recursive-decomposition
  - memory
  - current-status
  - d2
  - phase1
---

# 当前状态：D² / Phase 1

> [!summary] 本页定位
> 本页只整理当前已经发生的结果、方法和可守结论。未来候选场景见 [[11-recursive-decomposition-memory/future-scenarios|未来研究候选场景]]。

当前最可守的表述：

> 递归分解与 memory 线不直接证明“模型需要像 lambda 演算一样工作”。当前先检验：结构化分解多样性能否产生稳定、低成本的难度信号；分歧熵能否驱动自适应计算分配；trace / verified subproblem memory 能否在高分歧和失败样本上提供独立纠偏收益。

## 历史动机的位置

这条线的理论动机来自与控制反馈线不同的计算观。

- 图灵机、RAM/RASP 更强调状态、寻址、读写、指令执行。
- lambda 演算更强调函数抽象、函数应用、变量绑定、替换、递归。
- 二者在可计算性上等价，但工作方式和成本直觉不同。
- 函数式编程、Lisp、ML、Haskell、闭包、continuation、graph reduction、term rewriting 等都可看作这一思想在工程或理论中的后续形态。

需要谨慎的是：lambda 演算早期主要回答可计算性与形式系统问题，并不天然给出现代 AI 里的计算复杂度、训练难度或数据飞轮优势。它更适合作为动机桥，而不是直接证据。

更稳的现实映射是：

> 复杂问题可以被表示为可组合、可调用、可替换、可递归展开的中间对象，而不是一次性线性文本。

## 当前材料的真实核心

Phase 1 报告标题是 `Memory-Augmented Recursive-Decomposition Reasoning Agents`，但从证据看，当前真正站得住的是 v6 / D²：

> 三种结构化 decomposition styles 在同一模型上并行运行；它们的答案分歧形成 semantic entropy；entropy 决定 Direct、Majority、Arbitrate 三条路径；高分歧时 arbiter 读取失败 traces 后重解。

这可以拆成三层机制。

| 层 | 机制 | 当前证据 |
| --- | --- | --- |
| 多样性 | IPEV / Algebraic / Atomic 三种分解风格 | pairwise error Jaccard 约 0.53-0.55，说明错误有一定去相关 |
| 路由 | 答案分歧熵决定是否追加计算 | H=0、H≈0.637、H=log3 与准确率单调相关 |
| 纠偏 | arbiter 读取失败 traces 后重解 | v6 相对 v5 和多数基线有收益，但还需更多消融 |

Memory 当前不是最强证据点。材料里出现了：

- v1: networkx graph memory。
- v2: context envelope 和 reflection。
- v3: file workspaces、isolation、verified knowledge memory。
- v6: trace memory feeding arbiter agents。

这些说明 memory 是工程演进的一部分，但尚未单独证明 memory 本身是收益来源。

## 六代演进

六代系统的单一设计问题是：

> 如何在没有 oracle 的情况下，对难题花更多 compute，对简单题花更少 compute？

| 版本 | 机制 | GSM8K-200 | 主要收益 | 暴露问题 |
| --- | --- | ---: | --- | --- |
| v1 | tool-calling + networkx graph memory | 55.0% | 证明工具和 memory 方向可做 | planning 和 computing 混在一个 prompt，cache poisoning |
| v2 | planner + solver + reflection | 77.5% | 角色拆分明显提升，reflection 带来修复 | 无 failure isolation，uniform reflection cost |
| v3 | master-slave + file workspaces | 81.5% | 隔离、审计、持久化，worker 可递归变 mini-master | file I/O bottleneck，recipe 固定 |
| v4 | HCE complexity routing | 85.0% | 首个 adaptive compute | complexity score 需要额外 LLM call 且可能错 |
| v5 | structural diversity voting | 87.5% | 错误去相关开始发挥作用，去掉 HCE overhead | 全同意时浪费计算，全分歧时无恢复 |
| v6 | semantic entropy routing + arbiters | 93.5% | 用分歧信号做自适应计算和纠偏 | 需要更强对照拆清楚收益来源 |

这条演进说明：项目真正逐步摸到的是 adaptive compute，而不是单纯 memory。

## D² 方法

Agent v6 / D² 的机制是：

1. 用同一 3B 模型运行三个结构不同的 reasoning agents。
2. 三个 agents 分别采用 IPEV、Algebraic、Atomic 分解风格。
3. 计算三者最终答案分布的 Shannon entropy。
4. 根据 entropy 路由：
   - unanimous: Direct。
   - 2:1 majority: Majority。
   - all disagree: Arbitrate。
5. 高分歧时，两名 arbiter 读取三条失败 traces 并重解。
6. 最终用三名原始 agents 加两名 arbiters 的五票结果。

这个系统的关键洞察是：

> 分歧本身就是难度信号。

这比 v4 的显式 HCE complexity score 更干净，因为不需要额外 LLM call。

## 当前结果

Phase 1 材料记录的主要结果如下。

| Method | Cost | GSM8K-200 | GSM8K | SynthMath-1K |
| --- | ---: | ---: | ---: | ---: |
| Standard CoT | 1x | 83.0 | 82.87 | 58.0 |
| Structured CoT (IPEV) | 1x | 88.0 | 62.70 | 55.0 |
| Algebraic agent | 1x | 83.5 | 80.82 | 61.5 |
| Plan-and-Solve+ | 1x | 88.5 | 43.37 | 57.5 |
| Least-to-Most | 2x | 71.5 | 60.12 | 56.5 |
| ReAct | 2-5x | 65.0 | 79.15 | 47.0 |
| Decomposed Prompting | 2x | 82.5 | 80.82 | 57.0 |
| Self-Verification | 2x | 84.0 | 74.37 | 56.0 |
| Progressive Hint | 2-3x | 87.0 | 83.32 | 54.0 |
| Complexity-Guided Router | 2x | 65.0 | 75.89 | 56.5 |
| 3-Agent Majority Vote | 3x | 91.0 | 71.80 | 62.0 |
| Self-Consistency (k=3) | 3x | 80.0 | 83.24 | 68.1 |
| 5-Agent Majority Vote | 5x | 90.0 | 87.79 | 69.0 |
| Agent v6 / D² | 3.16-3.55x | 93.5 | 89.39 | 71.7 |

主要读法：

- D² 在 GSM8K-200、完整 GSM8K、SynthMath-1K 三列最高。
- 完整 GSM8K 上 D² 为 89.39%，Standard CoT 为 82.87%，提升 +6.52pp。
- SynthMath-1K 上 D² 为 71.7%，Standard CoT 为 57.8% 左右，提升约 +13.9pp。
- v6 相对 v5 在 GSM8K-200 上从 87.5% 到 93.5%，主要新增 entropy routing 和 arbiter agents。
- Phase 1 材料还记录了 Phi-3.5-mini 的跨模型泛化：CoT 81.20% 到 D² 85.75%，Unified-390 从 43.85% 到 49.23%。

成本解释要谨慎。材料里说 reasoning tier 可以 batched forward，因此 wall-clock 不是简单 3x，但论文或后续实验必须同时报告 calls、tokens、FLOPs 近似、wall-clock 和 dollar cost。

## 当前证据强度

| 主张 | 证据强度 | 说明 |
| --- | --- | --- |
| D² beats CoT on math benchmarks | 强 | GSM8K、SynthMath-1K、AIME、U-MATH 都有提升，且材料记录了统计检验 |
| Disagreement is a difficulty signal | 强 | entropy 与 accuracy 单调相关，且 SynthMath 触发更多 arbitration |
| Structural diversity matters | 中强 | pairwise error-set Jaccard 说明错误不完全重合，但还需 same-prompt 多样性对照 |
| Arbiter benefits from failed traces | 中 | v6 有提升，但需要 answer-only / trace-aware / random trace 消融 |
| Recursive decomposition is the key | 中弱 | v6 更像并行多策略分解；真正递归结构在 v3 更明显但不是最终主贡献 |
| Memory is the key | 弱到中 | memory 贯穿演进，但缺少独立 ablation |
| Planning is main bottleneck | 中 | causal ladder 有启发，但 intervention 设计可能引入 gold-plan / gold-answer 信息泄漏 |

## 当前候选分支

### 分支 A：结构化分解多样性

问题：

> 固定同一基础模型时，预先设计的多种 decomposition styles 是否比随机采样、自一致性或同质 multi-agent 更能产生可利用的错误去相关？

它对标：

- self-consistency。
- same prompt repeated sampling。
- multi-agent debate。
- plan-execute。
- least-to-most。
- Tree-of-Thought。

它要证明的不是“多跑几次有用”，而是：

> 结构差异比采样差异更能产生低相关错误，从而提升 ensemble 和 routing 的价值。

### 分支 B：分歧熵路由

问题：

> 不额外调用 complexity estimator，仅利用多个分解策略的答案分布，能否得到足够好的难度信号，并据此自适应分配计算？

它当前是最强候选主线。

关键原因：

- v4 的 HCE complexity routing 需要额外 LLM call。
- v6 的 entropy routing 使用已有输出，额外成本低。
- 分歧本身包含失败模式信息，不只是一个标量。

### 分支 C：trace / subproblem memory

问题：

> 高分歧或失败样本中的 traces、verified subproblem、失败模式和修复策略，是否能作为 memory 改善当前纠偏和未来相似任务？

这是最接近“memory-augmented”的部分，但当前需要补实验。

Memory 不能只存：

- 最终答案。
- 原始全文 trace。
- 大段自然语言经验。

更应存：

- typed subproblem。
- verified intermediate result。
- failed branch。
- error type。
- correction pattern。
- dependency edge。

## 与 plan-execute 的关系

Plan-execute 是这条线不可回避的强对手，就像 Agent+Tools 是控制反馈线不可回避的强对手。

当前主张不能是：

> 我们第一次让模型分解问题。

因为这已经被 plan-execute、least-to-most、decomposed prompting、ReAct、Tree-of-Thought、multi-agent debate、Reflexion 等大量吸收。

可守主张应是：

> 不同 decomposition styles 的分歧可以作为难度估计和纠偏入口；trace-aware arbitration 和 verified subproblem memory 能否在强 agentic baseline 上形成 cost-quality 增量。

## 当前最小可输命题

主命题：

> 在同一基础模型、同等或可核算计算预算下，结构化分解多样性产生的分歧熵，能否比固定 self-consistency、plan-execute、ReAct、Tree-of-Thought 类基线更好地分配推理计算，并提升 cost-normalized accuracy。

次命题：

> 在高分歧或失败样本上，trace memory / verified subproblem memory 是否比 answer-only voting、plain re-solving、普通 context replay 更能提升局部纠偏成功率和未来任务复用率。

更长期命题：

> 将问题表示为可递归展开的 typed subproblem graph，并只在高不确定子节点继续展开，是否比固定深度 plan-execute 或 flat multi-agent voting 有更好的 cost-quality Pareto。

## 当前实验协议

当前至少拆四个变量。

| 变量 | 问题 | 强对照 |
| --- | --- | --- |
| Decomposition diversity | 多种结构化分解风格是否比同质采样更有用 | same prompt x3、self-consistency、random prompt variants |
| Entropy routing | 分歧熵是否是有效难度信号 | random routing、HCE routing、fixed voting、oracle difficulty upper bound |
| Trace-aware arbitration | arbiter 是否真的从失败 traces 中获益 | answer-only arbiter、no-trace re-solve、random trace、corrupted trace |
| Memory | verified subproblem / failure memory 是否有复用价值 | no memory、raw trace memory、final-answer memory、unverified memory |

不能只比较 `D² vs CoT`。这个对照可保留为展示，但不足以证明机制。

### Stage 0：复现和成本账本

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

### Stage 1：结构化分解多样性

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

### Stage 2：分歧熵路由

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

### Stage 3：Trace-aware arbitration

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

### Stage 4：Memory 消融

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

### Stage 5：真正递归子问题图

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

## 主要攻击面

### 攻击 1：只是 self-consistency 的结构化版本

D² 同时运行三个 agents，可能只是 self-consistency / ensemble 的变体。

防守边界：

- 比 same prompt x3。
- 比 self-consistency k=3/5。
- 比 random prompt variants。
- 报告 error decorrelation。
- 报告 majority-correct 和 all-wrong rate。

如果 structural diversity 不稳定优于这些基线，应降级为 ensemble engineering。

### 攻击 2：只是多花 compute

Agent v6 成本高于单次 CoT。收益可能只是多跑几次。

防守边界：

- 统一成本账本。
- 同等 token budget 下比较。
- 同等 model call budget 下比较。
- 报告 cost-normalized accuracy。
- 比 fixed 5-agent majority。

如果同成本 self-consistency 或 5-agent majority 追平，D² 没有独立机制优势。

### 攻击 3：entropy routing 是事后解释

分歧熵与难度相关，不等于它能做有效路由。

防守边界：

- 与 random routing 比。
- 与 HCE routing 比。
- 与 oracle routing 上界比。
- 固定 arbitration fraction。
- 预注册 hard-case recall 和 false arbitration rate。

如果 entropy routing 不优于 random routing，路由主张失败。

### 攻击 4：arbiter 只是重新解题

Arbiter 可能没有真正使用 traces，只是又做了一次或两次解题。

防守边界：

- answer-only arbiter。
- no-trace re-solve。
- random trace。
- corrupted trace。
- verified trace。
- trace utilization analysis。

如果 answer-only 与 trace-aware 相同，trace memory 主张失败。

### 攻击 5：memory 只是污染或 retrieval

如果 memory 存了相似题和答案，收益可能只是查表。

防守边界：

- family split。
- parameter split。
- template-heldout。
- distractor memory。
- stale memory。
- 只允许 verified subproblem，不允许最终答案直接命中。

如果 memory 只在近邻模板上有效，应降级为 retrieval engineering。

### 攻击 6：递归分解不真实

当前 v6 更像 flat multi-agent ensemble，不是真正 recursive decomposition。

防守边界：

- 引入 typed subproblem graph。
- 子问题节点可验证。
- 高不确定节点继续展开。
- verified nodes 可缓存和复用。
- 局部失败可修复，不必全局重启。

如果没有这些结构，不应强称 recursive decomposition 已经成立。

### 攻击 7：baseline 弱

Plan-and-Solve、ReAct、Least-to-Most 等 baseline 在小模型上表现差，可能因为实现或 prompt 不够强。

防守边界：

- 使用公开强 prompt。
- 多轮调参预算相同。
- 记录每个 baseline 的最佳 prompt。
- 引入 external implementations 交叉验证。
- 增加 stronger agentic baselines。

### 攻击 8：benchmark 偏置

SynthMath-1K 可能天然适合结构化分解。

防守边界：

- 保留 SynthMath 作为第一阶段可控 benchmark。
- 增加 sorting、algorithm tracing、program synthesis、多文件代码修复。
- 增加 surface-form perturbation。
- 增加 family-heldout。

### 攻击 9：小模型特化

D² 可能只是 3B 小模型短板补丁，在 thinking models 或大模型上收益消失。

防守边界：

- 同一 agent framework 跑 Qwen2.5、Phi、Qwen thinking、DeepSeek-R1-distill 等。
- 对每个模型比较 bare model vs agent。
- 不再强行 suppress CoT。
- 报告 delta 随模型能力变化的曲线。

如果大模型上收益消失，应收缩为：

> 小模型推理增强和成本控制工程。

## 更好的理论问题

### 问题 1：结构化多样性是否降低错误相关性

形式化直觉：

> 对同一模型 `M`，不同 decomposition operator `d_i` 诱导不同错误集合 `E_i`。若 `E_i` 的相关性低于随机采样或同质 prompt 变体，则 ensemble 和 entropy routing 有结构性优势。

这比“递归分解有用”更可测。

### 问题 2：分歧是否是可用的不确定性估计

形式化直觉：

> 多个 structured solvers 的输出分布 `q(a|x)` 的 entropy `H(q)` 是否校准任务失败概率 `P(error|x)`，并能在固定追加计算预算下最大化收益。

这把 v6 的核心压成 calibration / routing 问题。

### 问题 3：trace 是否含有可纠偏信息

形式化直觉：

> 给定同样的题目和候选答案，失败 trace `T_i` 是否提供额外信息，使 arbiter 的纠偏概率高于 answer-only setting。

这把 trace memory 从“日志”变成可检验的信息变量。

### 问题 4：verified subproblem 是否可跨任务复用

形式化直觉：

> 若一个子问题节点 `s` 具有 verified input/output 和依赖边，则在同 family 但不同参数或表面词的任务中，检索并实例化 `s` 能否降低求解成本或错误率。

这才是 memory 的强版本。

## 失败条件

这条线应承认失败的情况：

- D² 只赢 CoT，不赢强 agentic baselines。
- Structural diversity 不优于普通 self-consistency。
- Entropy routing 不优于 random routing。
- Arbiter 不依赖 trace。
- Memory 只产生污染式近邻查表。
- Recursive DAG 的成本超过 flat ensemble，且没有长度或深度泛化收益。
- 成本账本显示收益被额外 token / calls / scaffold 吞掉。

## 当前 Defense

当前 defense 不是：

> 递归分解与 memory 已经成立。

而是：

- Phase 1 已经找到一个有证据的机制核心：结构化分解多样性和分歧熵路由。
- 这个机制与递归分解 / memory 有自然连接，但连接还需要实验补齐。
- 下一步不是扩张叙事，而是把 diversity、routing、arbitration、memory 分开做可输实验。
- 如果 memory 和 recursive DAG 失败，D² 仍可能作为 adaptive multi-agent reasoning 工程方向保留。
- 如果 memory 和 recursive DAG 成功，才有资格重新提升为“可复用子问题结构”的研究线。

能说：

- D² 是一个有初步证据的自适应计算分配框架。
- 分歧熵是一个有证据的难度信号。
- trace-aware arbitration 是一个值得单独检验的纠偏机制。

不能说：

- memory 已经被证明是主要收益来源。
- 递归分解已经优于所有 plan-execute。
- lambda 演算路线已经得到实验验证。
- 当前结果已经证明了可复用子问题函数或长期 memory。
