---
type: analysis
status: draft
tags:
  - recursive-decomposition
  - memory
  - research-direction
  - lean
  - kernel-optimization
  - code
  - algorithms
---

# Lean、性能优化、代码 / 算法任务的方向比较

这份文档比较三个候选研究场景：

- Lean / 形式化证明。
- GPU / NPU kernel 性能优化。
- 普通代码 / 算法问题。

核心判断标准不是“哪个任务更容易做出 benchmark 提升”，而是：

> 哪个场景最能承载 `recursive decomposition + memory` 的独立价值：把已验证的局部中间结果变成可复用、可组合、可检索、可更新、可局部纠偏的对象。

如果一个方向只能证明“多跑几次、检索相似样例、让 Agent 调工具”有用，它会被 self-consistency、RAG、Agent+Skills、autotune 或普通工程循环吸收。

## 总体结论

| 维度 | Lean / 形式化证明 | Kernel 性能优化 | 代码 / 算法问题 |
| --- | --- | --- | --- |
| 价值叙事 | 最清晰：数学证明天然需要 lemma、分解、复用 | 工程价值强：性能、成本、硬件效率 | 范围广，但容易散 |
| 验证强度 | 最强，proof checker 严格验证 | 中强，正确性测试 + 性能 benchmark | 从中强到中弱，取决于测试 / spec |
| 中间对象 | theorem、lemma、proof state、proof fragment | tile、schedule、layout、bottleneck fix、failed config | helper、invariant、rewrite rule、patch pattern |
| 递归分解自然度 | 很高，proof DAG / lemma dependency 天然存在 | 中高，优化搜索可分解但需人为建模 | 差异很大，算法合成较好，普通代码修复较弱 |
| memory 可复用性 | 理论上强，但 retrieval 对手强 | 形状 / 算子 / 硬件迁移可测 | 容易退化成模板或例题检索 |
| 强基线压力 | LeanSearch、LeanDojo、ReProver、Lean Copilot、premise retrieval | compiler、autotune、Triton autotune、Agent+Skills、evolutionary search | RAG、SWE-style agents、unit-test repair、skills、self-debug |
| 小规模训练适配 | 适合训练 reranker、usefulness predictor、tactic policy | 很适合训练 cost model、retriever、patch proposer | 适合，但信号噪声和污染风险更高 |
| 最小实验清晰度 | 高：heldout theorem proof success / search cost | 高：correct-and-fast / trial budget / reuse | 中：必须先设计强 verifier 和 family split |
| 最大风险 | 只是在做 theorem retrieval | 只是在做 autotune / template search | 只是在做 RAG / 代码样例复用 |
| 推荐定位 | 高价值主战场 | 工程型高价值分支 / 算力利用分支 | sanity check 或数据工厂，除非有强 spec |

当前更稳的研究排序：

1. Lean 适合承担“这条研究线是否有硬核心”的主问题。
2. Kernel 优化适合承担“能否把递归分解 + memory 变成工程闭环和训练闭环”的问题。
3. 普通代码 / 算法任务适合承担 sanity check、数据构造和方法预研，但不宜作为第一主线，除非引入强 verifier、强 family split 和明确的 reusable subproblem schema。

## 统一研究对象

这三类方向如果要属于同一条研究线，必须共享一个抽象对象：

```text
verified_subproblem_memory:
  problem_family
  local_goal
  input_contract
  output_contract
  solution_or_strategy
  verifier
  dependencies
  validity_scope
  reuse_history
  failure_cases
  update_rule
```

不同场景只是这个对象的实例不同。

| 场景 | memory item 的实例 |
| --- | --- |
| Lean | verified lemma、proof-state -> tactic、proof fragment、lemma dependency subgraph |
| Kernel | tile config、schedule decision、layout transform、bottleneck diagnosis、failed config、profile-conditioned patch |
| 代码 / 算法 | helper function、invariant、rewrite rule、API usage pattern、repair pattern、property-tested component |

关键区别：

- `memory` 不是保存大段上下文。
- `memory` 不是保存最终答案。
- `memory` 不是普通 RAG。
- `memory` 必须能被验证、能说明适用范围、能被组合进新任务、能在失败时局部修复。

## 维度一：价值叙事

### Lean

Lean 的最大优势是价值叙事天然成立：

> 数学证明本来就是把复杂命题分解为 lemma，再通过组合、实例化、替换和依赖管理完成证明。

这与 `recursive decomposition + memory` 的关系最紧：

- recursive decomposition 对应 proof search、case split、lemma decomposition。
- memory 对应已有 theorem、generated lemma、proof fragment、proof-state case。
- verification 由 Lean checker 提供。
- composition 由 theorem dependency 和 tactic execution 体现。

Lean 的研究主张可以写得很硬：

> 系统能否从 solved / failed proof attempts 中自动形成新的 verified lemma memory，并在 heldout theorem tasks 上降低 proof search cost 或提高 proof success？

这不是“让模型做数学题”，而是“让系统增长一批可验证、可复用的中间数学对象”。

### Kernel 性能优化

Kernel 优化的价值叙事更工程化：

> 高性能 kernel 编写需要大量局部优化决策；这些决策有正确性和性能反馈，且可能跨相似算子、shape bucket、dtype、硬件复用。

它与 `recursive decomposition + memory` 的关系也明确，但需要主动建模：

- recursive decomposition 对应 op -> shape bucket -> bottleneck -> schedule subproblem -> tile/layout/pipeline decision。
- memory 对应可复用优化经验、成功 schedule、失败配置、profile-conditioned patch。
- verification 对应 correctness test、differential testing、benchmark、profile counter。
- composition 对应多个 schedule decisions 组合成完整 kernel。

这条线的强处是闭环非常硬：每次候选 kernel 都会产生编译结果、正确性结果、性能结果、profile 信号。它也能自然使用 GPU/NPU 算力。

但它的叙事风险也很大：

> 如果 memory 只是在记录某个 shape 的最佳 config，那它就是 cache / autotune result，不是 verified subproblem memory。

Kernel 方向必须证明跨 shape、跨算子变体、跨硬件或跨 backend 的复用收益。

### 代码 / 算法问题

普通代码 / 算法问题的范围最大，但价值叙事最容易散。

它可能很适合：

- 算法 helper function 的复用。
- invariant / rewrite rule 的复用。
- program synthesis 中已验证组件的组合。
- repair pattern 的局部纠偏。

但也最容易退化：

- LeetCode 题库检索。
- 相似题模板复用。
- 单测驱动的 trial-and-error。
- Agent+Skills 工程循环。
- 把 raw trace 塞进上下文。

代码 / 算法方向只有在引入明确的局部 verifier 和 memory schema 后，才接近本线核心。否则它更适合作为低成本 sanity check。

## 维度二：验证强度

验证强度决定 memory 的可信度，也决定是否能做局部纠偏。

| 验证类型 | 场景 | 强度 | 问题 |
| --- | --- | --- | --- |
| proof checker | Lean / Coq / Isabelle / Dafny / F* | 最强 | 工程门槛高，已有 retrieval / prover 强 |
| SMT / symbolic checker | SMT、rewrite、invariant | 强 | 表达范围有限，任务设计要求高 |
| differential testing | kernel、算法实现 | 中强 | 依赖 reference 和测试覆盖 |
| property-based testing | 算法 / 代码 | 中 | property 写不好会 false verify |
| unit tests | 代码修复 | 中弱 | 覆盖不足，容易 test hacking |
| final-answer judge | 数学题 / 编程题 | 弱 | 只能验证最终答案，不能验证中间对象 |

因此：

- Lean 最适合证明“verified memory”这个概念。
- Kernel 最适合证明“验证 + 性能反馈 + 搜索闭环”这个工程 flywheel。
- 普通代码必须尽量从 unit tests 升级到 property tests、differential tests、symbolic checks 或 formal spec。

## 维度三：递归分解是否自然

### Lean：天然递归

Lean proof search 本身就是递归结构。

```text
target theorem
  -> subgoals
  -> local lemmas
  -> proof states
  -> tactics
  -> dependencies
  -> closed proof
```

一个 proof state 可以进一步分解；一个 lemma 可以被多个 theorem 复用；失败时也可以只修一个 proof fragment。这是最接近 `recursive decomposition` 原意的场景。

### Kernel：搜索分解，需要人为结构化

Kernel 优化也能分解，但不是数学意义上的天然 proof DAG。

```text
operator
  -> shape / dtype / hardware bucket
  -> bottleneck diagnosis
  -> memory layout decision
  -> tile / block / warp mapping
  -> pipeline / vectorization
  -> correctness and benchmark
```

它的递归性来自搜索过程：

- 先定位瓶颈。
- 再展开局部 schedule 子问题。
- 再根据 profile 修局部失败。
- 已验证的优化经验进入 memory。

如果系统每次都全局重写 kernel，而不是复用和修补局部 schedule subproblem，那它就不是递归分解，只是代码生成。

### 代码 / 算法：取决于任务设计

算法题可能有递归结构：

- divide and conquer。
- dynamic programming。
- graph subroutine。
- parser / evaluator。
- algebraic simplification。

但普通代码修复未必有。

如果 memory item 是 `helper function + spec + tests + valid scope`，则较接近本线。如果只是保存“某类 bug 的修复 diff”，则更像经验检索。

## 维度四：memory 的复用与组合

### Lean 的复用

Lean 中可复用对象最清楚：

- 一个 lemma 可以被多个 theorem 引用。
- 一个 proof fragment 可以关闭相似 proof state。
- 一个 tactic pattern 可以在相似 local context 复用。
- 一个 generalized lemma 可以覆盖多个具体实例。

最关键的指标不是检索命中，而是：

- verified lemma reuse rate。
- proof search node reduction。
- proof success improvement on heldout family。
- harmful retrieval rate。
- generated lemma 是否不是原题重命名。

### Kernel 的复用

Kernel 中复用更实用，但更难判定抽象层级。

低价值复用：

- 同一个 shape 复用同一个 tile。
- 同一个 benchmark 复用最佳 kernel。
- 同一个模板参数换名字。

高价值复用：

- 同一 op family 跨 shape bucket 复用 schedule decision。
- 同一 bottleneck 跨不同 operator 复用 repair strategy。
- 同一 hardware generation 上复用 memory layout / warp mapping。
- failed config memory 降低未来无效 trial。
- profile-conditioned retriever 提高 time-to-threshold-speedup。

Kernel memory 的关键不是“记住最快实现”，而是“记住为什么这个局部优化在这个适用范围内有效”。

### 代码 / 算法的复用

代码 / 算法中复用最容易被误判。

低价值复用：

- 题目模板匹配。
- 复制相似解法。
- 记忆最终代码。
- 用 RAG 找到 StackOverflow / GitHub 片段。

高价值复用：

- helper function 有 spec、tests、valid input range。
- invariant 可被多个任务验证使用。
- rewrite rule 有 checker。
- repair pattern 能定位局部 bug，而不是全局重写。
- subproblem graph 能记录 dependency 和 reuse history。

因此代码 / 算法方向必须做 family-heldout 和 distractor memory，否则很难证明不是 retrieval。

## 维度五：强基线与吸收压力

### Lean 的强基线

Lean 方向不能低估已有系统：

- LeanSearch 等自然语言 theorem search 已经解决一部分“找 theorem”问题。
- LeanDojo 提供 proof state extraction、interaction、retrieval-augmented theorem proving 基础设施。
- ReProver / premise retrieval 已经把 retrieval 放进 theorem proving loop。
- Lean Copilot / tactic generation 也在吸收模型辅助证明能力。

所以 Lean 方向不能把贡献写成：

> 我们能检索 theorem。

更强的贡献应是：

> 我们能从解决过程里自动生成、验证、抽象、索引新的 lemma memory，并证明它们在 heldout tasks 中有复用价值。

### Kernel 的强基线

Kernel 方向面对的是更强的工程吸收压力：

- compiler search。
- TVM / Ansor / MetaSchedule。
- Triton autotune。
- TorchInductor / vendor libraries。
- KernelBench / TritonBench 等 LLM kernel generation benchmark。
- Agent+Skills + profiling tools。
- evolutionary / AlphaEvolve-like coding search。

因此 Kernel 方向不能把贡献写成：

> LLM 能写更快 kernel。

更强的贡献应是：

> verified optimization memory 是否能在强 autotune / Agent+Skills / evolutionary search 基线下，减少 trial budget、降低失败率、提升 heldout reuse。

### 代码 / 算法的强基线

普通代码 / 算法方向强基线非常宽：

- RAG / example retrieval。
- self-debug / unit-test loop。
- Agent+Tools / Agent+Skills。
- program synthesis search。
- repair agents。
- benchmark-specific templates。

如果没有强 verifier 和强 split，任何提升都可能被解释为：

> 检索到了相似样例，或者多试了几次。

## 维度六：小规模训练如何落地

这里的小规模训练指几台 8 卡服务器级别，不假设从零训练大模型。

### Lean

适合训练的模块：

- proof-state retriever。
- theorem / lemma reranker。
- lemma usefulness predictor。
- memory-conditioned tactic policy。
- lemma proposer 的 LoRA / SFT。

训练数据：

- proof states。
- theorem dependencies。
- tactic traces。
- successful / failed retrieved lemma pairs。
- generated lemma 的 reuse history。

最小训练目标：

```text
proof_state + candidate_lemma -> useful / not useful
```

更进一步：

```text
proof_state + retrieved_memory -> next tactic / proof fragment
```

Lean 训练的优势是标签相对干净；缺点是数据工程、Lean 环境、proof search loop 成本不低。

### Kernel

Kernel 是最适合消耗 GPU/NPU 资源的方向，因为训练和评测都需要实际硬件闭环。

适合训练的模块：

- cost model / latency predictor。
- schedule reranker。
- optimization memory retriever。
- profile-conditioned patch proposer。
- correctness / failure classifier。
- reward / preference model。

训练数据来自真实循环：

```text
operator + shape + dtype + hardware
-> candidate kernel / tile / schedule
-> compile result
-> correctness result
-> latency / bandwidth / occupancy
-> profile bottleneck
-> next edit
-> memory write
```

最小训练目标：

```text
current_op + shape + profile + candidate_schedule -> worth_benchmarking
```

Kernel 训练的优势是反馈自动化、指标硬、GPU 可直接用起来；缺点是 benchmark 噪声、硬件依赖、强基线极强。

### 代码 / 算法

适合训练的模块：

- subproblem retriever。
- helper usefulness reranker。
- repair pattern classifier。
- property-test generator。
- memory-conditioned code patch proposer。

训练数据：

- solved algorithm tasks。
- helper function extraction。
- unit / property test pass-fail。
- bug -> patch trajectories。
- invariant / rewrite rule 使用记录。

最小训练目标：

```text
task_spec + candidate_helper + tests -> useful / harmful
```

代码 / 算法训练的优势是数据易造；缺点是 verifier 弱、污染风险大、训练出来的模型可能只学到模板相似度。

## 维度七：最小可输实验

### Lean 最小实验

输入：

```text
一批 Lean theorem proving tasks
```

系统输出：

```text
verified lemma memory
```

对照：

- no memory。
- theorem retrieval / LeanSearch-like baseline。
- raw proof trace memory。
- final theorem cache。
- verified generated lemma memory。
- generalized lemma memory。

主指标：

- heldout proof success。
- proof search nodes / tactics / time。
- lemma reuse rate。
- proof length reduction。
- harmful retrieval rate。
- memory construction cost。

判定：

> 如果 generated verified lemma memory 不能超过 strong theorem retrieval，Lean 方向至少在当前设定下退化为 retrieval engineering。

### Kernel 最小实验

输入：

```text
operator + shape + dtype + hardware target
```

系统输出：

```text
verified optimization memory + candidate kernels / schedules
```

对照：

- Triton autotune / compiler baseline。
- plain LLM agent。
- Agent+Skills。
- evolutionary search。
- Agent + retrieved memory。
- Agent + trained reranker。
- Agent + memory + reranker。

主指标：

- correct-and-fast rate。
- time-to-first-correct。
- time-to-threshold-speedup。
- benchmark trial count。
- compile / runtime failure rate。
- heldout shape / operator reuse。
- harmful memory rate。
- memory overhead。

判定：

> 如果 memory 不能减少 trial budget 或跨 heldout shapes 复用，只能说它是 autotune cache。

### 代码 / 算法最小实验

输入：

```text
family-split algorithm / code synthesis tasks
```

系统输出：

```text
verified helper / invariant / rewrite / repair memory
```

对照：

- no memory。
- RAG examples。
- final solution memory。
- raw trace memory。
- Agent+Skills。
- verified helper memory。
- distractor memory。

主指标：

- heldout solve rate。
- test / property pass rate。
- helper reuse success。
- local repair success。
- harmful retrieval rate。
- search cost / attempts。
- cross-family transfer。

判定：

> 如果收益只来自近邻样例或最终解检索，代码 / 算法方向不能支撑本线主张。

## 维度八：数据飞轮

这条研究线若要长期推进，需要一种数据飞轮：

```text
solve attempt
-> local subproblem extraction
-> verification
-> memory write
-> retrieval / composition in future tasks
-> success / failure attribution
-> training signal
-> better extraction / retrieval / proposal
```

三个方向的数据飞轮差异很大。

| 环节 | Lean | Kernel | 代码 / 算法 |
| --- | --- | --- | --- |
| solve attempt | proof search / tactic generation | kernel generation / schedule search | coding agent / synthesis |
| verification | Lean checker | tests + benchmark + profile | tests / property / oracle |
| memory write | lemma / proof fragment | schedule / bottleneck / failed config | helper / invariant / patch |
| future reuse | proof-state retrieval | shape / op / profile retrieval | task / API / invariant retrieval |
| attribution | theorem dependency / tactic success | latency, correctness, error type | test pass, bug localization |
| training signal | clean but sparse | rich but noisy | abundant but less reliable |

Kernel 的 flywheel 工程最完整；Lean 的 verification 最干净；代码 / 算法最容易扩规模但最容易污染。

## 维度九：和 Phase 1 / D² 的关系

Phase 1 更像：

> structured ensemble + entropy routing + trace-aware arbitration。

三类候选方向是在回答：

> 如何把 Phase 1 中较弱的 `memory` 叙事，升级为真正可验证、可复用、可组合的中间对象？

映射关系：

| Phase 1 机制 | Lean 后续 | Kernel 后续 | 代码 / 算法后续 |
| --- | --- | --- | --- |
| decomposition styles | 不同 proof strategies / subgoal decompositions | 不同 schedule strategies | 不同 algorithm decomposition |
| entropy / disagreement | proof attempt failure / tactic uncertainty | candidate kernel failure / performance disagreement | multi-solver disagreement |
| trace-aware arbitration | proof trace / failed proof repair | profile / compile error repair | failed test / patch repair |
| memory | verified lemma memory | verified optimization memory | verified helper / invariant memory |

如果继续沿 D² 直接做数学 word problems，最容易被攻击为 structured ensemble。Lean / Kernel / verified code 方向则把 memory 变成更硬对象。

## 维度十：最关键攻击

### 对 Lean 的攻击

- 你是否只是做了更复杂的 theorem retrieval？
- generated lemma 是否只是原题或近邻模板重命名？
- heldout family 是否真的排除了表面相似污染？
- memory construction cost 是否超过 proof search 节省？
- proof-state reranker 是否只是学 theorem popularity？
- 生成 lemma 的抽象层级是否足够支持组合？

### 对 Kernel 的攻击

- 你是否只是重造 autotune / cost model？
- memory 是否只复用同 shape？
- Agent+Skills 加上 profiling 是否已经追平？
- benchmark variance 是否让结果不可重复？
- correctness tests 是否覆盖数值边界？
- trained reranker 是否只是学常见 shape / op popularity？
- 跨硬件迁移失败时，memory 是否还有研究价值？

### 对代码 / 算法的攻击

- verifier 是否太弱，导致 false verified memory？
- 是否只是 RAG 找相似题？
- family split 是否足够硬？
- helper / invariant 是否能组合，还是只能贴模板？
- memory 是否降低 search cost，还是增加上下文噪声？
- 局部修复是否真的发生，还是每次全局重写？

## 维度十一：适合声称什么

### Lean 可声称

强声称：

> verified lemma memory 可以从解决过程增长，并在 heldout theorem proving tasks 中复用，降低 proof search cost 或提高 proof success。

弱声称：

> proof-state memory / reranking 在形式化证明中是有效 sanity check。

不可声称：

> 已证明递归分解是通用智能的必要机制。

### Kernel 可声称

强声称：

> verified optimization memory 在强 autotune / Agent+Skills 基线下，能减少 trial budget、降低失败率、提升 heldout operator / shape 上的 correct-and-fast rate。

弱声称：

> profile-conditioned memory 对 kernel search 有工程增益。

不可声称：

> LLM 写 kernel 本身证明了 recursive decomposition + memory。

### 代码 / 算法可声称

强声称：

> verified helper / invariant / rewrite memory 能跨 family 复用，并提升局部纠偏和组合求解。

弱声称：

> 在某类算法合成任务中，memory-conditioned agent 比 no-memory baseline 更稳。

不可声称：

> 普通代码修复 benchmark 提升就是 verified subproblem memory 的证据。

## 建议推进方式

### 如果目标是高价值研究主线

优先 Lean。

理由：

- verification 最硬。
- subproblem / lemma / dependency 天然存在。
- 递归分解与 memory 的概念最贴合。
- 失败也有清晰结论：如果在 Lean 里都难以证明 memory 增量，本线强主张需要大幅收缩。

最小路线：

```text
Lean task families
-> proof-state / theorem retrieval baseline
-> generated verified lemma memory
-> heldout reuse
-> reranker / usefulness predictor training
```

### 如果目标是用起小规模 GPU/NPU 并形成工程闭环

优先 Kernel。

理由：

- 训练、搜索、评测都能消耗 GPU/NPU。
- correctness + performance 双反馈硬。
- 数据飞轮天然自动化。
- 工程价值明确。

最小路线：

```text
Triton / PTO / PyPTO operator families
-> Agent+Skills + autotune baseline
-> optimization memory schema
-> cost model / reranker
-> heldout shape / op reuse
```

### 如果目标是快速 sanity check

选择代码 / 算法，但要收窄。

不建议从普通代码修复开始。更合适的是：

- property-tested algorithm synthesis。
- SMT / rewrite rule memory。
- helper library construction。
- invariant discovery。

最小路线：

```text
生成式 algorithm task families
-> property / differential verifier
-> helper / invariant extraction
-> family-heldout reuse
-> distractor memory stress test
```

## 研究组合建议

最稳组合不是三选一，而是分层：

1. Lean 作为理论上最干净的主线：验证 `verified subproblem memory` 是否有硬增量。
2. Kernel 作为工程和训练闭环分支：验证同一思想在高价值系统工程中是否能承受强基线。
3. 代码 / 算法作为方法预研和数据工厂：快速测试 memory schema、retriever、distractor、local repair 等机制。

但不应三个方向同时深挖。更合理的是：

- 先选一个主战场。
- 另一个作为 sanity check / 迁移验证。
- 第三个只保留文档和轻量实验。

当前建议：

> Lean 主线 + Kernel 工程分支，是最清晰的组合。普通代码 / 算法暂时只做方法孵化，不承担主叙事。

## 参考

- [LeanSearch](https://leansearch.net/)
- [LeanDojo](https://leandojo.org/)
- [LeanDojo: Theorem Proving with Retrieval-Augmented Language Models](https://arxiv.org/abs/2306.15626)
- [KernelBench](https://github.com/ScalingIntelligence/KernelBench)
- [KernelBench paper](https://arxiv.org/abs/2502.10517)
- [TritonBench paper](https://arxiv.org/abs/2502.14752)
- [TritonBench GitHub](https://github.com/thunlp/tritonbench)
