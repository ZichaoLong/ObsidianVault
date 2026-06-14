---
type: survey
status: active
date: 2026-06-14
tags:
  - recursive-decomposition
  - memory
  - benchmark-landscape
  - mechanism-landscape
  - hrm
  - trm
  - rlm
---

# 对标机制谱系：递归分解与 Memory

> [!summary] 本页定位
> 本页整理递归分解与 memory 线需要面对的完整对标谱系。它回答三个问题：第一，当前 D² / Phase 1 到底落在什么机制谱系里；第二，未来 `verified subproblem memory` 要对标哪些强路线；第三，HRM / TRM / RLM 这类递归模型应如何解读，是否应进入本线和控制反馈线。

调查时间：2026-06-14。

## 一页版结论

递归分解与 memory 线不能只对标 `plan-execute`。更完整的对手不是单个系统，而是一整组已经在不同层级吸收“分解、递归、搜索、反思、记忆、adaptive compute”的机制族。

当前最稳判断：

- Phase 1 / D² 最接近 `structured ensemble + adaptive compute + trace-aware arbitration`，而不是严格意义上的长期 memory 或递归子问题图。
- `verified subproblem memory` 仍是未来最值得押的高价值命题，但必须在 Lean、Kernel、SMT 等有强 verifier 的场景里证明，而不是只保存 agent traces。
- HRM / TRM 应放入谱系，但它们属于 `model-internal latent recursion`，不是普通 Agent，也不是 verified memory。
- RLM 比 HRM 更直接相关，因为 RLM 把长上下文外部化为环境，并允许模型 inspect / decompose / recursively call itself；它同时连接递归分解线与控制反馈 B 分支。
- HRM / TRM 可以引入控制反馈线，但只能作为“内部隐状态控制循环”的相邻对手，不能作为 `Load/Store`、显式 workspace 或外部 memory 的证据。

更短的定位：

> 本线研究外显的、可验证的、可复用的子问题对象；HRM / TRM 研究内隐的 recurrent refinement；RLM 研究外部环境化上下文上的递归 self-call。三者都属于递归计算谱系，但机制对象不同。

## 统一分类轴

对标谱系不应只按论文名排列，而应按机制发生的位置来分类。

### 轴一：递归发生在哪里

| 位置 | 典型形态 | 例子 |
| --- | --- | --- |
| 输出文本里 | 线性 CoT、自问自答 | CoT、Self-Consistency |
| prompt 结构里 | 先分解，再求解 | Least-to-Most、Plan-and-Solve、Decomposed Prompting |
| 搜索树里 | 分支、回溯、打分 | Tree-of-Thought、Graph-of-Thought、MCTS |
| Agent runtime 里 | planner / executor / tool loop | ReAct、planner-executor、coding agents |
| 外部环境里 | 上下文作为可 inspect 的对象 | RLM、lambda-RLM、long-context recursive agents |
| 显式 memory 里 | 可检索、可复用中间对象 | Voyager skills、case memory、verified lemma memory |
| 模型隐状态里 | recurrent latent refinement | HRM、TRM、Universal Transformer-like recurrence |
| 模型参数里 | 训练 / 蒸馏后内化 | DeepSeek-R1-Distill、s1、LIMO、TinyZero |

### 轴二：memory 是否显式

| 类型 | 说明 | 对本线的意义 |
| --- | --- | --- |
| 无 memory | 每次独立求解 | 基础 baseline |
| answer memory | 只存最终答案 | 容易退化成 cache |
| raw trace memory | 存完整历史轨迹 | 易污染、难归因 |
| summary memory | 存压缩经验 | 有用但验证弱 |
| skill memory | 存可调用技能 / 程序 | 接近 Voyager / agent skills |
| verified subproblem memory | 存已验证的中间对象、依赖、适用范围 | 本线未来最硬目标 |
| latent memory | 存在于隐状态或参数 | HRM / TRM / distillation 方向 |

### 轴三：验证强度

| 验证强度 | 场景 | 对本线含义 |
| --- | --- | --- |
| final answer judge | 数学题、问答 | 只能验证终点，不能证明中间对象有用 |
| unit tests | 代码修复 | 中间对象可能仍不可靠 |
| property / differential tests | 算法、Kernel | 可以支持局部对象验证 |
| profile + correctness harness | Kernel 优化 | 能同时验证正确性与性能 |
| SMT / symbolic checker | rewrite、invariant | 很适合 verified memory |
| proof checker | Lean / Coq / Isabelle | 最适合证明 verified subproblem memory |

## 完整对标谱系

### 1. 线性推理与 CoT 家族

代表：

- Chain-of-Thought。
- Self-Consistency。
- STaR。
- process supervision / verifier-guided reasoning。

它们回答的问题：

> 让模型显式生成中间 reasoning tokens，是否能提升推理？

对本线的压力：

- 如果 D² 只是在 CoT 上做多采样，它应被归类为 self-consistency / ensemble。
- 如果 memory 只存 CoT，它很难形成独立机制。

本线剩余空间：

- 证明中间对象不是普通 reasoning text，而是可验证、可复用、可组合的子问题对象。

参考：

- [Chain-of-Thought Prompting Elicits Reasoning in Large Language Models](https://arxiv.org/abs/2201.11903)
- [Self-Consistency Improves Chain of Thought Reasoning in Language Models](https://arxiv.org/abs/2203.11171)
- [STaR: Bootstrapping Reasoning With Reasoning](https://arxiv.org/abs/2203.14465)

### 2. Prompt 级分解

代表：

- Least-to-Most。
- Plan-and-Solve。
- Decomposed Prompting。
- Program-of-Thoughts。

它们回答的问题：

> 把复杂问题拆成子问题，再逐步求解，是否比一次性 CoT 更好？

对本线的压力：

- 递归分解不是新概念。
- 如果本线只是“先分解再执行”，会被这些方法吸收。

本线剩余空间：

- 子问题是否被验证。
- 子问题是否被缓存和复用。
- 子问题图是否支持局部失败修复。
- 子问题 memory 是否跨任务迁移。

参考：

- [Least-to-Most Prompting Enables Complex Reasoning in Large Language Models](https://arxiv.org/abs/2205.10625)
- [Plan-and-Solve Prompting](https://arxiv.org/abs/2305.04091)
- [Decomposed Prompting](https://arxiv.org/abs/2210.02406)
- [Program of Thoughts Prompting](https://arxiv.org/abs/2211.12588)

### 3. 搜索式推理

代表：

- Tree-of-Thought。
- Graph-of-Thought。
- MCTS / beam search / best-first search with LLM。
- verifier-guided search。

它们回答的问题：

> 多分支探索、打分、回溯是否能提高推理成功率？

对本线的压力：

- “递归展开”可以只是搜索树。
- “多条 trace”可以只是 search candidates。
- “memory”可能只是 search cache。

本线剩余空间：

- 搜索节点是否变成可复用 memory item。
- 成功子树是否可组合进新任务。
- 失败节点是否生成局部修复数据。
- 是否能降低 heldout search cost，而不是只提升 pass@k。

参考：

- [Tree of Thoughts](https://arxiv.org/abs/2305.10601)
- [Graph of Thoughts](https://arxiv.org/abs/2308.09687)

### 4. 反思与自纠偏

代表：

- Reflexion。
- Self-Refine。
- critique-revise loops。
- verifier-based repair。

它们回答的问题：

> 失败后的自然语言反思或 verifier feedback 是否能帮助下一轮修复？

对本线的压力：

- trace-aware arbitration 可能只是反思纠偏。
- failure memory 可能只是“把错误解释放进上下文”。

本线剩余空间：

- 反思是否被结构化成可训练 repair trace。
- 同类错误复发率是否下降。
- 局部修复是否替代全局重解。
- failure memory 是否跨任务复用。

参考：

- [Reflexion](https://arxiv.org/abs/2303.11366)
- [Self-Refine](https://arxiv.org/abs/2303.17651)

### 5. Agent + Tools / Plan-Execute

代表：

- ReAct。
- AutoGPT-style agents。
- planner-executor。
- coding agents。
- theorem prover interaction。

它们回答的问题：

> 模型能否通过工具调用、环境反馈、计划执行完成长程任务？

对本线的压力：

- 现实 Agent 已经吸收了大量递归分解、反思、工具调用、文件 memory、checkpoint 和 replay。
- 若本线只是“让 Agent 多跑几轮并存 traces”，价值不足。

本线剩余空间：

- 子问题对象是否比普通 tool trace 更可学习。
- 子问题 memory 是否有 verifier 和适用范围。
- memory 是否减少未来搜索成本，而不是增加 scaffold。

参考：

- [ReAct](https://arxiv.org/abs/2210.03629)
- [Toolformer](https://arxiv.org/abs/2302.04761)

### 6. Ensemble / Adaptive Compute

代表：

- Self-consistency。
- multi-agent debate。
- majority vote。
- D² / structured diversity + entropy routing。
- adaptive compute routing。

它们回答的问题：

> 多个解法产生的分歧能否作为难度信号，并据此分配更多 compute？

当前 Phase 1 的位置：

> D² 当前最像这一类：三种结构化 decomposition styles 产生答案分歧，分歧熵决定 Direct / Majority / Arbitrate。

对本线的压力：

- D² 可以有工程价值，但科学上更接近 structured ensemble。
- 它不能直接证明长期 memory 或递归子问题图。

本线剩余空间：

- trace-aware arbitration 是否确实利用失败 trace，而不是重新求解。
- 分歧 trace 是否能转化为训练数据。
- 高分歧样本是否适合生成 verified subproblem memory。

### 7. Memory / Skill Accumulation

代表：

- MemGPT。
- Generative Agents。
- Voyager skill library。
- agentic memory。
- case-based reasoning。

它们回答的问题：

> Agent 能否把过去经验压缩、检索、复用到未来任务？

对本线的压力：

- 长期 memory、reflection memory、skill memory 都已有大量工作。
- 如果 memory item 没有验证和适用范围，本线很容易退化为普通 agent memory。

本线剩余空间：

- memory item 必须是可验证中间对象。
- memory 必须支持局部组合和局部修复。
- heldout family transfer 必须优于 raw trace / summary / RAG。

参考：

- [MemGPT](https://arxiv.org/abs/2310.08560)
- [Generative Agents](https://arxiv.org/abs/2304.03442)
- [Voyager](https://arxiv.org/abs/2305.16291)

### 8. Verified Subproblem Memory

代表候选：

- Lean verified lemma memory。
- proof-state case memory。
- Kernel verified optimization memory。
- SMT / rewrite rule memory。
- invariant / proof-obligation memory。

它回答的问题：

> 系统能否自动形成、验证、索引、复用局部中间对象，并在 heldout 任务上减少搜索成本或提高成功率？

这是本线未来最硬的候选主战场。

核心要求：

- memory item 不是最终答案。
- memory item 不是 raw trace。
- memory item 必须有 verifier。
- memory item 必须有 input / output contract。
- memory item 必须有 validity scope。
- memory item 必须能被复用或组合。
- memory item 失败时应能局部修复。

最小裁决：

> 如果 verified memory 只在同模板近邻上有效，它是 cache；如果它能在 family-heldout 或结构不同的任务中降低 proof/search/optimization cost，它才接近研究增量。

对应文档：

- [[future-scenarios|未来研究候选场景]]
- [[future-lean-landscape|Lean 方向详尽调研]]
- [[future-kernel-landscape|Kernel 性能优化工作谱系]]

### 9. Recursive Language Models / 外部环境递归

代表：

- Recursive Language Models (RLM)。
- lambda-RLM。
- long-context recursive agents。
- lossless context / recursive context management。

它们回答的问题：

> 不把长上下文直接塞进模型，而是把 prompt 当作外部环境，让模型 inspect、decompose、recursively call itself，能否提高长上下文处理效率？

RLM 的关键位置：

- 它不是普通 CoT。
- 它不是普通 plan-execute。
- 它把上下文外部化为可操作环境。
- 它允许模型递归调用自身处理局部片段。
- 它很接近“递归分解 + 控制反馈 B 分支”的交叉点。

对本线的压力：

- 如果本线只提出“递归调用 LLM 处理子问题”，RLM 已经是强对手。
- 如果本线只处理长上下文，必须对标 RLM / lambda-RLM / retrieval / compaction。

本线剩余空间：

- RLM 通常关注长上下文问答和 prompt-as-environment；本线可关注 verified subproblem memory。
- lambda-RLM 强调 typed functional runtime 与 termination / cost guarantees，这对本线是重要启发：递归分解需要可控运行时，而不是完全自由的代码生成。
- 本线可以把 RLM 视为外部递归接口强基线，再问 verified memory 是否提供额外复用价值。

参考：

- [Recursive Language Models](https://arxiv.org/abs/2512.24601)
- [RLM project page](https://alexzhang13.github.io/blog/2025/rlm/)
- [The Y-Combinator for LLMs / lambda-RLM](https://arxiv.org/abs/2603.20105)

### 10. Model-Internal Recursion：HRM / TRM

代表：

- HRM: Hierarchical Reasoning Model。
- TRM: Tiny Recursive Model。
- Universal Transformer-like recurrent refinement。
- recurrent latent reasoning。

它们回答的问题：

> 递归推理是否可以不外化成文本、工具、memory 或 agent loop，而是内化为模型隐状态中的 iterative refinement？

#### HRM 的基本定位

HRM 是 Sapient 2025 年提出的 recurrent reasoning architecture。论文声称：

- 模型约 27M 参数。
- 不依赖预训练或 CoT 数据。
- 通过两个 interdependent recurrent modules 工作。
- high-level module 做慢速抽象规划。
- low-level module 做快速细节计算。
- 在 Sudoku、Maze、ARC 等任务上取得强结果。

更重要的是它的机制位置：

> HRM 是 latent recurrent computation，不是显式递归分解，也不是显式 memory。

它对本线的价值：

- 说明“递归计算”可以被内化到模型 dynamics。
- 说明小模型 + recurrent refinement 是一个不能忽视的对手。
- 说明如果未来允许新架构，本线不应只盯着 LLM+Agent 外部 scaffold。

它不能支持的结论：

- 不能证明 `verified subproblem memory` 有用。
- 不能证明外部 workspace 有用。
- 不能证明 `Load/Store` 是低层控制原语。
- 不能证明显式子问题图优于隐式 recurrent computation。

#### HRM 的 adversarial 解读

ARC Prize 对 HRM 的后续分析很重要。其主要发现包括：

- 能大致复现 HRM 在 ARC-AGI-1 上的小模型强表现。
- HRM 在 ARC-AGI-2 上信号很弱。
- hierarchical architecture 相比同规模 transformer 的贡献可能较小。
- outer refinement loop 是更关键驱动。
- training-time refinement 和 data augmentation 非常重要。
- cross-task transfer 可能有限，部分性能接近 task-specific adaptation / memorization。

这意味着对 HRM 的合理解读应收缩为：

> HRM 提供了“内部 recurrent refinement 可能高效”的证据，但不能简单读成“层级规划模块是主要原因”，也不能读成“通用推理已经被 27M 小模型解决”。

#### TRM 的基本定位

TRM 对 HRM 提出更强挑战。TRM 论文声称：

- 不需要双模块 hierarchy。
- 用一个更小的 recursive network。
- 约 7M 参数。
- 通过递归更新 latent state 和 answer。
- 在 Sudoku-Extreme、Maze-Hard、ARC-AGI-1/2 上超过或接近 HRM。

TRM 对本线的含义：

- “hierarchy”本身可能不是核心。
- “recursive refinement + deep supervision / answer refinement”可能比复杂结构更关键。
- 小模型递归 reasoning 的研究应重点关注 refinement dynamics、训练信号和任务分布，而不是过早押注某种生物启发叙事。

参考：

- [Hierarchical Reasoning Model](https://arxiv.org/abs/2506.21734)
- [Sapient HRM GitHub](https://github.com/sapientinc/HRM)
- [ARC Prize: The Hidden Drivers of HRM's Performance](https://arcprize.org/blog/hrm-analysis)
- [Less is More: Recursive Reasoning with Tiny Networks](https://arxiv.org/abs/2510.04871)
- [TinyRecursiveModels GitHub](https://github.com/SamsungSAILMontreal/TinyRecursiveModels)

### 11. Post-Training / Distillation：把递归轨迹内化到模型

代表：

- DeepSeek-R1-Distill。
- s1。
- LIMO。
- TinyZero。
- reasoning trace distillation。
- RLVR。

它们回答的问题：

> 与其在 test time 显式递归，不如把高质量 reasoning traces、verifier feedback 或 search behavior 训练进模型。

对本线的压力：

- 如果 verified subproblem traces 有价值，强对手会直接拿去蒸馏小模型。
- 如果 distillation 后模型不再需要外部 memory，本线的 runtime 价值会下降。

本线剩余空间：

- 生成更干净的 verified traces。
- 生成局部 repair traces。
- 生成 proof-state / memory-use / failure-type 数据。
- 证明这些数据比 raw CoT / raw agent trace 更适合训练小模型。

对应文档：

- [[future-small-model-landscape|小模型研究谱系调研]]

## HRM / TRM 是否属于递归分解与 memory 线

属于，但只能作为相邻谱系，不能作为直接主线。

更精确地说：

| 问题 | 结论 |
| --- | --- |
| 是否递归 | 是，发生在模型内部 recurrent loop |
| 是否分解 | 弱，可能有 latent decomposition，但没有显式子问题对象 |
| 是否 memory | 弱，memory 是隐状态 / 参数，不是可检索外部 memory |
| 是否 verified memory | 否 |
| 是否对 D² 构成对手 | 部分，都是 adaptive compute，但发生层级不同 |
| 是否对未来小模型方向重要 | 是，非常重要 |
| 是否证明本线主张 | 否，只能作为对照与挑战 |

因此文档中应这样写：

> HRM / TRM 是递归计算谱系中的内部化路线。它们挑战“递归分解必须外显为 Agent trace 或 memory item”的假设，但并不击穿 verified subproblem memory，因为后者研究的是可验证、可复用、可审计的外部中间对象。

## 是否应引入控制反馈线

应该引入，但定位要窄。

控制反馈线当前关注：

- A：显式状态语义。
- B：局部状态访问。
- A+B：统一状态访问接口是否形成训练、纠偏、成本优势。

HRM / TRM 与此不同：

- 没有显式 external workspace。
- 没有 address / read / write / commit 事件。
- 没有可回放 semantic transition。
- 没有外部局部状态访问接口。

它们对控制反馈线的意义是：

> test-time 期间的状态更新不一定要外显为 workspace；也可以内化为 recurrent hidden state。显式控制事件路线必须证明自己相对这种内部递归路线仍有可诊断性、可训练数据、可复用 memory 或工程可控性优势。

建议控制反馈线只加入一小节：

```text
Internal recurrent / latent control loop:
  HRM / TRM 是显式 workspace 路线的相邻挑战。
  它们说明局部闭环可以发生在模型隐状态中，而非外部状态事件中。
  因此不能用 HRM 支撑 Load/Store，只能用它界定竞争边界。
```

RLM 则应同时进入控制反馈 B 分支的对标谱系：

- 它把长 prompt 当外部环境。
- 模型主动 inspect / decompose / recurse。
- 这和“主动控制局部反馈信源”高度相关。
- 如果 B 只做长上下文局部访问，RLM 是强基线。

## 对当前 D² 的重新定位

D² 不应被放在 HRM/TRM 或 RLM 同一层级。

更准确的定位：

```text
D² = structured ensemble
   + semantic entropy routing
   + trace-aware arbitration
```

它的直接强基线：

- CoT。
- Self-Consistency k=3/k=5。
- same-prompt multi-sample。
- random prompt variants。
- multi-agent debate。
- fixed majority vote。
- fixed arbitration fraction。
- Plan-and-Solve / Least-to-Most / ReAct / Decomposed Prompting。

它要补的关键消融：

- answer-only arbiter。
- no-trace re-solve。
- random / corrupted trace。
- same-prompt x3。
- structural diversity x3。
- fixed 5-agent majority。
- entropy routing vs random routing。
- arbitration cost-quality curve。

D² 的可守命题：

> structured diversity 产生错误去相关；分歧熵是低成本难度信号；trace-aware arbitration 在高分歧样本上有 cost-normalized 增益。

D² 不能直接证明：

- memory 是主贡献。
- 递归子问题图成立。
- verified subproblem memory 已经有效。
- lambda 演算式工作方式优于类图灵机工作方式。

## 对未来主线的影响

### 如果继续 D²

应按 adaptive compute / structured ensemble 方向推进。

主问题：

> 分歧熵能否稳定预测难度，并比固定 self-consistency 或固定 arbitration 更好地分配 compute？

这条线偏工程与小模型系统化，不必强行称为 memory。

### 如果推进 verified memory

应优先选 Lean / Kernel / SMT。

主问题：

> 解决过程中的中间对象能否被验证、索引、复用，并在 heldout 任务上降低搜索成本？

这条线最接近递归分解与 memory 的科学主张。

### 如果推进小模型

应把 HRM / TRM 纳入参考。

主问题：

> 小模型是否可以通过递归计算、结构化 trace 蒸馏、verified memory conditioning 或 worker specialization 获得更好的 cost-quality Pareto？

这里要区分三类路线：

| 路线 | 机制 | 训练对象 |
| --- | --- | --- |
| D² | 外部 ensemble + arbitration | answer / trace / routing data |
| verified memory | 外部可验证 memory item | proof / repair / reuse traces |
| HRM/TRM | 内部 recurrent refinement | task input-output / latent recursion |

### 如果推进长上下文 / memory 系统

RLM 是必须对标的强路线。

主问题：

> 外部环境化上下文 + recursive self-call 是否已经足够？verified subproblem memory 是否还能提供额外的可复用、可验证、可训练优势？

## 最小更新建议

后续文档结构建议：

- README 中把本文作为“对标谱系入口”。
- current-status 继续把 D² 定位为 adaptive ensemble。
- future-scenarios 继续把 Lean / Kernel / 小模型作为候选场景。
- 本文承接所有横向对标：CoT、分解、搜索、反思、Agent、memory、RLM、HRM/TRM、post-training。
- 控制反馈线只补 HRM/TRM/RLM 的相邻位置，不把它们纳入 `Load/Store` 证据链。

## 参考链接

- [Chain-of-Thought Prompting](https://arxiv.org/abs/2201.11903)
- [Self-Consistency](https://arxiv.org/abs/2203.11171)
- [Least-to-Most Prompting](https://arxiv.org/abs/2205.10625)
- [Plan-and-Solve Prompting](https://arxiv.org/abs/2305.04091)
- [Decomposed Prompting](https://arxiv.org/abs/2210.02406)
- [Tree of Thoughts](https://arxiv.org/abs/2305.10601)
- [Graph of Thoughts](https://arxiv.org/abs/2308.09687)
- [ReAct](https://arxiv.org/abs/2210.03629)
- [Reflexion](https://arxiv.org/abs/2303.11366)
- [Self-Refine](https://arxiv.org/abs/2303.17651)
- [MemGPT](https://arxiv.org/abs/2310.08560)
- [Voyager](https://arxiv.org/abs/2305.16291)
- [Recursive Language Models](https://arxiv.org/abs/2512.24601)
- [lambda-RLM](https://arxiv.org/abs/2603.20105)
- [Hierarchical Reasoning Model](https://arxiv.org/abs/2506.21734)
- [ARC Prize HRM analysis](https://arcprize.org/blog/hrm-analysis)
- [Tiny Recursive Model](https://arxiv.org/abs/2510.04871)
