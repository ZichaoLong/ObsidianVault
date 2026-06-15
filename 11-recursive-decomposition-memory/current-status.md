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
> 本页面向项目验收与方向同步，整理 Phase 1 已完成内容、主要结果、真实结论边界、风险和后续方向。未来候选场景见 [[future-scenarios|未来研究候选场景]]。
> 收到的代码仓库审视见 [[code-review-recursive-reasoning-agents|recursive-reasoning-agents 代码审视]]；该页专门区分代码仓库内可复核证据与 Phase 1 报告 / 汇报材料结论。

## 摘要

Phase 1 在小模型约束下完成了 6 轮 Agent 系统迭代，最终形成 Agent v6 / D²。

当前最可守的结论是：

> D² 是一个在小模型数学推理场景中有效的 adaptive compute / structured ensemble 方案：通过三种结构化分解风格制造答案分歧，用分歧熵判断难度，并在高分歧样本上追加 arbiter 纠偏。

当前不应过度声称：

- 不能说已经证明 `memory-augmented recursive decomposition` 是主要收益来源。
- 不能说已经证明真正的递归子问题图优于现有 Agent / plan-execute。
- 不能说这套机制已经能对标最强 LLM + 最强 Agent。
- 不能说当前结果已经证明长期 memory 或可复用子问题函数。

更准确的验收结论：

> Phase 1 证明了在固定小模型条件下，经过系统化 Agent 工程迭代，可以显著提升数学推理 benchmark；同时也暴露出原始“递归分解 + memory”叙事需要收缩。最终最强信号来自 ensemble-style structural diversity、semantic entropy routing 和 trace-aware arbitration，而不是 memory 本身。

## 项目约束与目标

本阶段的主要约束：

- 以小模型为基础，不直接使用最强闭源 LLM。
- 重点探索 test-time compute 如何组织，而不是训练一个新基础模型。
- 任务主要集中在数学推理 benchmark，包括 GSM8K、SynthMath-1K 等。
- 系统允许多轮 Agent 调用、分解、反思、路由、仲裁和 trace 记录。

这意味着本阶段结果的合理比较对象不是“所有前沿 LLM+Agent”，而是：

- 同一小模型上的 CoT。
- 同一小模型上的 plan-execute / ReAct / self-consistency / voting 等 Agent 方法。
- 同等或可核算计算成本下的多策略推理方案。

如果要拼最终效果，必须面对：

- 最强 LLM + 最强 Agent。
- 经过充分蒸馏、后训练和工程打磨的小模型。
- 更完整的工具、检索、verifier 和系统 scaffold。

因此，本阶段更适合被理解为：

> 小模型约束下的 Agent 推理组织方式探索，而不是通用最强能力竞赛。

## 历史动机的位置

这条线的历史动机来自 lambda 演算、函数组合和递归展开。

- lambda 演算强调函数抽象、函数应用、变量绑定、替换、递归。
- 函数式程序把复杂对象组织成可组合、可调用、可替换的中间结构。
- 函数式编程、Lisp、ML、Haskell、闭包、continuation、graph reduction、term rewriting 等都可看作这一思想在工程或理论中的后续形态。

需要谨慎的是：lambda 演算早期主要回答可计算性与形式系统问题，并不天然给出现代 AI 里的计算复杂度、训练难度或数据飞轮优势。它适合作为本研究线的历史动机牵引，而不是直接证据。

更稳的现实映射是：

> 复杂问题可以被表示为可组合、可调用、可替换、可递归展开的中间对象，而不是一次性线性文本。

但从 Phase 1 结果看，当前真正被实验证据支持的不是完整递归分解理论，而是 adaptive compute / structured ensemble。

## Phase 1 的真实核心

Phase 1 报告标题是 `Memory-Augmented Recursive-Decomposition Reasoning Agents`，但从证据看，当前真正站得住的是 v6 / D²：

> 三种结构化 decomposition styles 在同一模型上并行运行；它们的答案分歧形成 semantic entropy；entropy 决定 Direct、Majority、Arbitrate 三条路径；高分歧时 arbiter 读取失败 traces 后重解。

这可以拆成三层机制，可类比于机器学习中的 ensemble 技术。

| 层 | 机制 | 当前证据 |
| --- | --- | --- |
| 多样性 | IPEV / Algebraic / Atomic 三种分解风格 | pairwise error Jaccard 约 0.53-0.55，说明错误有一定去相关 |
| 路由 | 答案分歧熵决定是否追加计算 | H=0、H≈0.637、H=log3 与准确率单调相关 |
| 纠偏 | arbiter 读取失败 traces 后重解 | v6 相对 v5 和多数基线有收益，但仍需更多消融 |

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

成本解释要谨慎。材料里说 reasoning tier 可以 batched forward，因此 wall-clock 不是简单 3x，但后续如果用于论文或外部汇报，需要同时报告 calls、tokens、FLOPs 近似、wall-clock 和 dollar cost。

## 能证明什么，不能证明什么

| 主张 | 证据强度 | 说明 |
| --- | --- | --- |
| D² beats CoT on math benchmarks | 强 | GSM8K、SynthMath-1K、AIME、U-MATH 都有提升，且材料记录了统计检验 |
| Disagreement is a difficulty signal | 强 | entropy 与 accuracy 单调相关，且 SynthMath 触发更多 arbitration |
| Structural diversity matters | 中强 | pairwise error-set Jaccard 说明错误不完全重合，但还需 same-prompt 多样性对照 |
| Arbiter benefits from failed traces | 中 | v6 有提升，但需要 answer-only / trace-aware / random trace 消融 |
| Recursive decomposition is the key | 中弱 | v6 更像并行多策略分解；真正递归结构在 v3 更明显但不是最终主贡献 |
| Memory is the key | 弱到中 | memory 贯穿演进，但缺少独立 ablation |
| Planning is main bottleneck | 中 | causal ladder 有启发，但 intervention 设计可能引入 gold-plan / gold-answer 信息泄漏 |

当前能说：

- D² 是一个有初步证据的自适应计算分配框架。
- 分歧熵是一个有证据的难度信号。
- 结构化多样性在小模型上能够产生一定错误去相关。
- trace-aware arbitration 是一个值得单独检验的纠偏机制。
- Phase 1 给出了有效的小模型 Agent 工程迭代结果。

当前不能说：

- memory 已经被证明是主要收益来源。
- 递归分解已经优于所有 plan-execute。
- lambda 演算路线已经得到实验验证。
- 当前结果已经证明了可复用子问题函数或长期 memory。
- 当前系统已经优于最强 LLM + 最强 Agent。

## 主要风险与未证明项

### 1. D² 可能主要是 structured ensemble

D² 同时运行三个 agents，可能本质上是 self-consistency / ensemble 的结构化版本。当前结果有工程价值，但科学新意需要谨慎表述。

后续若继续沿 D² 做论文，应补：

- same prompt x3。
- self-consistency k=3/5。
- random prompt variants。
- fixed 5-agent majority。
- 同成本 token / call 预算比较。

### 2. 分歧熵可能只是经验有效的难度信号

分歧熵与难度相关，这是有价值的观察；但它是否比其他 routing 信号更优，需要更强对照。

需要补：

- random routing。
- HCE routing。
- oracle routing 上界。
- 固定 arbitration fraction 下的 hard-case recall 和 false arbitration rate。

### 3. Arbiter 是否真的利用 trace 尚未完全证明

当前 v6 给 arbiter 提供失败 traces，但还不能排除 arbiter 只是“又解了一遍题”。

需要补：

- answer-only arbiter。
- no-trace re-solve。
- random / corrupted trace。
- truncated / compressed trace。
- trace utilization analysis。

### 4. Memory 贡献尚未独立拆出

Memory 在 v1-v6 中多次出现，但没有独立 ablation。当前不能把项目主贡献写成 memory。

需要补：

- no memory。
- raw trace memory。
- final-answer memory。
- verified subproblem memory。
- distractor / stale memory。

### 5. 递归分解尚未真正成立

当前 v6 更像 flat multi-agent ensemble，不是真正 recursive subproblem DAG。

若未来要重新主张递归分解，需要至少具备：

- 子问题节点。
- 父子依赖。
- 节点 verifier。
- 节点缓存和复用。
- 高不确定节点继续展开。
- 局部失败可修复，而不是全局重启。

### 6. 小模型特化风险

D² 可能只是 3B 小模型短板补丁，在 thinking models 或更强模型上收益变小。

因此后续如果继续评估 D²，需要报告：

- 同一 Agent framework 在不同模型规模下的 delta。
- bare model vs agent 的对比。
- token / latency / dollar cost。
- 是否能在更强 reasoning model 上仍有 Pareto 优势。

### 7. Benchmark 与成本口径风险

SynthMath-1K 适合控制变量，但也可能天然偏向结构化分解。成本表中的 `3.16-3.55x` 也需要和实际 wall-clock、token、batching 口径分开解释。

后续外部汇报或论文需要避免只报 accuracy。

## 后续方向判断

Phase 1 给出的结论不应是“原始大叙事已经成立”，而应是：

> 小模型 Agent 迭代有效，但最终最强方法更接近 adaptive ensemble。若继续追求更高研究价值，需要转向更硬、更可验证、或更接近工程闭环的场景。

当前更值得推进的后续方向有三类。

### 方向一：Lean / 形式化证明

目的：

> 用 Lean proof checker 把 `verified subproblem memory` 做硬。

价值：

- verifier 严格。
- lemma / proof state / proof fragment 天然是可复用中间对象。
- 可以更清楚地区分 retrieval、trace memory、generated lemma memory。

核心问题：

> 系统能否自动生成、验证、索引并复用新的中间 lemma，并在 heldout theorem proving tasks 上降低 proof search cost 或提高 proof success？

详见 [[future-lean-landscape|Lean 方向详尽调研]]。

### 方向二：Kernel 性能优化

目的：

> 在 correctness + performance 双重可验证场景中，检验 verified optimization memory 是否能减少搜索成本、降低失败率或跨 shape / operator 复用。

价值：

- 工程反馈硬。
- 训练和评测闭环清楚。
- 可直接对接 GPU / NPU 资源。

风险：

- autotune、compiler search、Agent+Skills、evolutionary coding agents 都是强对手。
- 如果 memory 只复用同 shape，就是 cache，不是研究增量。

详见 [[future-kernel-landscape|Kernel 性能优化工作谱系]]。

### 方向三：小模型系统化与数据价值

目的：

> 不把小模型当成最终万能 solver，而是研究小模型能否承担 cheap worker、retriever、reranker、verifier helper、repair proposer、router 等局部角色。

价值：

- 小模型适合多次调用和局部控制。
- 小模型更依赖结构化输入、verifier 和高质量轨迹。
- 如果 verified traces 比 raw agent logs 更适合训练小模型，递归分解 + memory 可转化为数据飞轮价值。

核心问题：

> verified subproblem traces / local repair traces 是否比普通 CoT 或 raw agent trace 更适合蒸馏小模型？

详见 [[future-small-model-landscape|小模型研究谱系调研]]。

## 验收口径建议

对验收小组，建议这样表述 Phase 1：

> 项目在小模型约束下完成 6 轮 Agent 迭代，最终 D² 在数学推理 benchmark 上显著优于 CoT 和若干 Agent baseline。该结果证明了结构化多样性、分歧熵路由和仲裁纠偏在当前设置下有效，但尚未证明 memory 或真正递归分解是主要收益来源。基于这一结论，后续方向应从泛化叙事收缩到更硬的场景：Lean 形式化证明、Kernel 性能优化、小模型 worker / 数据蒸馏。

这既保留项目成果，也明确边界和下一阶段牵引。
