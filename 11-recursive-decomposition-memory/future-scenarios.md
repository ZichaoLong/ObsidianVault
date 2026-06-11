---
type: future-scenarios
status: active
tags:
  - recursive-decomposition
  - memory
  - verified-subproblem-memory
  - research-direction
  - lean
  - kernel-optimization
  - code
  - algorithms
---

# 未来研究候选场景

> [!summary] 本页定位
> 本页整理未来候选场景。当前 D² / Phase 1 的现状、结果、方法和攻击面见 [[11-recursive-decomposition-memory/current-status|当前状态：D² / Phase 1]]。

未来主线不应直接声称“memory 已经有效”，而应收缩为一个更硬的问题：

> 给定一批任务和求解轨迹，系统能否自动形成、验证、索引、复用局部中间对象，并在 heldout 任务中降低搜索成本、提高成功率或提升局部纠偏能力？

这个对象暂称为 `verified subproblem memory`。

## 统一研究对象

三类主要候选方向如果要属于同一条研究线，必须共享一个抽象对象：

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
| Lean / 形式化证明 | verified lemma、proof-state -> tactic、proof fragment、lemma dependency subgraph |
| Kernel 优化 | tile config、schedule decision、layout transform、bottleneck diagnosis、failed config、profile-conditioned patch |
| 代码 / 算法 | helper function、invariant、rewrite rule、API usage pattern、repair pattern、property-tested component |
| SMT / symbolic | rewrite rule、constraint、invariant、proof obligation、solver tactic |

关键区别：

- `memory` 不是保存大段上下文。
- `memory` 不是保存最终答案。
- `memory` 不是普通 RAG。
- `memory` 必须能被验证、能说明适用范围、能被组合进新任务、能在失败时局部修复。

## 选择标准

一个方向是否适合作为未来候选，取决于五点：

1. 中间对象是否可验证。
2. 中间对象是否可跨任务复用。
3. 中间对象是否能组合成更大解。
4. 失败时是否支持局部纠偏，而不是全局重启。
5. 强基线下是否仍有可归因增量。

普通最终答案评测不够。单元测试、oracle、symbolic checker、property tests 能提供验证，但验证强度和 Lean proof checker 不同。

## 总体方向比较

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

小模型不是同一层级的任务场景，而是横向载体：它可以用于 Lean、Kernel、代码 / 算法、D² 数学推理中的 cheap worker、retriever、reranker、verifier helper、repair proposer 和 router。专项调研见 [[11-recursive-decomposition-memory/future-small-model-landscape|小模型研究谱系调研]]。

## 验证强度

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

## 场景一：Lean Verified Lemma Memory

专项调研见 [[11-recursive-decomposition-memory/future-lean-landscape|Lean 方向详尽调研]]。本节保留方向摘要。

Lean 方向把 `verified subproblem memory` 收缩到一个更硬的问题：

> 给定一批已形式化任务，系统能否从解决过程里提取出可复用的 verified lemma / subproblem，并在 heldout 任务中通过检索、实例化、组合这些 lemma，降低证明搜索成本或提高证明成功率？

如果以 Lean 为基础设施，verification 已经由 proof checker 解决；retrieval 也已有 LeanSearch / LeanDojo / ReProver / Lean Copilot / Pantograph 等强对手。因此贡献不能写成“可验证”或“能检索 theorem”，而应落在：

> 自动形成、证明、抽象、索引、复用新的中间引理。

### Memory item

一个 Lean memory item 至少应包含：

```text
subproblem:
  statement
  proof
  assumptions
  dependencies
  verifier
  validity_scope
  source_tasks
  reuse_history
```

自然实例包括：

- verified lemma。
- proof-state -> useful lemma / tactic。
- proof fragment。
- lemma dependency subgraph。
- generalized lemma 从多个具体实例抽象而来。

### 与普通 theorem retrieval 的区别

| 机制 | 存在对象 | 关键问题 |
| --- | --- | --- |
| theorem retrieval / LeanSearch | mathlib 已有 theorem | 能否找到已有定理 |
| raw trace memory | 过去 proof trace | 能否提示当前证明 |
| verified lemma memory | 新生成并已证明的 lemma / proof fragment | 能否抽象、复用、组合 |
| recursive subproblem graph | lemma 之间形成依赖图 | 能否局部展开、局部修复、跨任务积累 |

最危险的退化是：

> 只是把 LeanSearch / RAG 接上，然后说 memory 有用。

Lean 方向真正要检验的是：系统能否增长一批新 memory，并让这些 memory 在 heldout task 上产生增量。

### 候选方向

方向 A：Verified Lemma Discovery

> 系统能否从多个 solved tasks 或 failed proof attempts 中，自动提出一个更一般的 lemma，并用 Lean 证明它？

最小裁决：

- 生成的 lemma 必须通过 Lean。
- lemma 不能只是原题重命名。
- lemma 必须在 heldout tasks 中被复用。
- 复用后要降低 proof search cost 或提高 proof success。

方向 B：Proof-State Memory / Case-Based Proving

> 给定当前 proof state，检索过去相似 proof state 及其 closing tactic / local proof fragment，是否比普通 theorem retrieval 更有用？

它回答：

- memory 是否比 raw theorem retrieval 多带来信息。
- 过去证明状态是否有可迁移结构。
- harmful retrieval 是否可控。

方向 C：Lemma Usefulness Prediction

> 给定 proof state 和 candidate lemma，能否预测这个 lemma 是否真的有用？

输入：

```text
proof_state
candidate_lemma
local_context
```

输出：

```text
useful / not useful
expected tactic
expected cost reduction
```

方向 D：Continual Verified Memory

> 任务按时间流进入，系统解决一批任务后把 verified subproblem 写入 memory，后续 heldout tasks 是否越来越容易？

关键指标：

- memory 增长后 proof success 是否上升。
- proof search cost 是否下降。
- harmful retrieval 是否随 memory 增大而失控。

方向 E：Recursive Subproblem DAG

> 不只存单个 lemma，而是存一组有依赖关系的 verified nodes；失败时只展开某个节点，成功节点缓存复用。

这最接近“递归分解”，但工程复杂，不应作为第一击。

### Lean 最小实验

输入：

```text
一批 Lean theorem proving tasks
```

输出：

```text
系统自动生成的 verified lemma memory
```

目标：

```text
在 heldout tasks 上提升 proof success 或降低 proof search cost
```

基本对照：

| 组 | 含义 |
| --- | --- |
| no memory | 直接证明 |
| mathlib retrieval | LeanSearch / Loogle / premise retrieval |
| raw trace memory | 检索过去 proof traces |
| final theorem memory | 近邻 theorem / answer，作为污染风险对照 |
| verified lemma memory | 只存已由 Lean 验证的中间 lemma |
| generalized lemma memory | 从多个实例抽象出更一般 lemma，再验证并复用 |

主指标：

- proof success rate。
- proof search nodes / tactics / time。
- retrieved lemma usefulness。
- harmful retrieval rate。
- verified lemma reuse rate。
- heldout family transfer。
- proof length reduction。
- memory construction cost。

关键裁决：

> 如果 verified lemma memory 只在同模板近邻上有效，那就是 retrieval / cache；如果它能从训练任务中生成更抽象的 lemma，并在表面不同、参数不同、组合结构不同的 heldout theorem 中复用，才接近高价值 memory。

### Lean 小规模训练路线

几台 8 卡服务器不适合从零训练大模型。更现实的训练目标是 retrieval / reranking / proof policy / lemma proposal。

Stage 0：不训练，先做审计。

- 建立 Lean task families。
- 划分 family-heldout / template-heldout。
- 定义 memory schema。
- 跑 no-memory / theorem retrieval / raw trace memory / verified lemma memory baseline。

Stage 1：训练 reranker。

任务：

> `proof state + candidate lemma -> useful / not useful`

数据：

- 从 mathlib / LeanDojo-style traces 提取 proof states。
- 使用实际 proof dependencies 构造正样本。
- 使用相似但未被使用的 theorem 构造 hard negatives。

Stage 2：训练 tactic / proof-step policy。

任务：

> condition on retrieved verified memory，预测下一步 tactic 或 proof fragment。

目标：

- memory-conditioned prover 优于普通 retrieval prover。
- proof search nodes / time 下降。
- heldout family 上仍有效。

Stage 3：训练 lemma proposer。

闭环：

```text
propose lemma -> Lean verifies -> add to memory -> heldout tasks reuse -> successful reuse becomes training signal
```

这是高风险高价值阶段，不应在 Stage 0/1 失败时继续扩张。

### Lean 失败条件

- verified lemma memory 不优于 mathlib retrieval / LeanSearch-like baseline。
- 生成 lemma 只是原题或近邻模板的重命名。
- family-heldout / template-heldout 上没有复用收益。
- harmful retrieval rate 随 memory 增长快速上升。
- reranker 只能学习 theorem popularity，不能学习 proof-state usefulness。
- lemma proposal 成功率过低，memory construction cost 吞掉收益。
- proof checker 通过但 lemma 太专用，不能降低后续 proof search cost。

## 场景二：非 Lean Verified Subproblem Memory

若考虑非 Lean 方向，不能只找“能判分”的任务，而要找：

> 是否存在可局部验证、可复用、可组合的中间对象。

候选方向：

| 方向 | 可验证性 | 是否适合 memory / recursive decomposition |
| --- | --- | --- |
| 程序验证 / Dafny / F* / Coq / Isabelle | 很强 | 很适合，本质接近 Lean |
| SMT / SAT / symbolic algebra | 强 | 适合存 rewrite rule、lemma、invariant |
| 算法合成 + property tests | 中强 | 适合，但 verifier 弱于 proof checker |
| GPU / NPU kernel 优化 | 中强 | 正确性和性能可验证，适合工程型 memory，但强对手很多 |
| 代码生成 / 修复 + 单测 | 中 | 可做 sanity check，但容易退化成 retrieval |
| 多文件工程修复 | 中弱 | 需要 memory，但验证不完整，噪声大 |

### 程序合成 / 算法库构造

问题：

> 系统能否从已解决任务中提取 verified helper functions，并在 heldout algorithm tasks 中复用？

验证方式：

- 单元测试。
- property-based tests。
- differential testing。
- symbolic checks。
- optional formal spec。

风险：

- 只在近邻模板上有用。
- helper function 过专用。
- 测试覆盖不足，false verified。

一个 memory item 可以是：

```text
verified_code_subproblem:
  helper_function
  spec
  property_tests
  passing_evidence
  dependencies
  valid_input_range
  reuse_examples
  failure_cases
```

测试目标不是“最终代码过了单测”，而是：

- 是否减少重复实现。
- 是否降低搜索成本。
- 是否减少错误传播。
- 是否支持局部修复。
- 是否在 heldout family 上复用。

### SMT / Rewrite Rule Memory

问题：

> 系统能否自动发现、验证、复用 rewrite rules、invariants 或 constraints，从而减少后续求解成本？

适合对象：

- 代数化简。
- 约束求解。
- 程序不变量。
- proof obligations。
- symbolic execution。

优势：

- verifier 比普通单测强。
- 中间对象更像 lemma。
- 可复用性比自然语言 trace 更清楚。

### 代码修复 / 多文件工程任务

问题：

> 系统能否从历史 patch 中提取 verified repair pattern / API usage pattern，并在后续代码任务中复用？

这适合工程 sanity check，但高价值叙事弱于 Lean / SMT。

原因：

- 验证常依赖不完整单测。
- 任务边界噪声大。
- patch pattern 容易退化成 retrieval。
- memory 是否真正可组合较难证明。

## 场景三：GPU / NPU Kernel 优化

Kernel 优化可以作为 `verified subproblem memory` 的工程型候选分支，但前提是研究对象不是“写出一个更快 kernel”，而是：

> 系统能否从已优化 kernels 中提取 verified optimization subproblems，并在 heldout operators / shapes / hardware settings 上复用这些 memory，从而减少搜索成本、降低错误率或提升性能？

详细强基线与已有吸收见 [[11-recursive-decomposition-memory/future-kernel-landscape|Kernel 性能优化工作谱系]]。

### 为什么符合候选范畴

Kernel 优化天然具有局部子问题：

- tiling。
- memory coalescing。
- shared memory / local memory。
- vectorization。
- pipeline / prefetch。
- occupancy。
- register pressure。
- layout transform。
- fusion。
- thread / warp / block mapping。

这些子问题同时具备：

- 可验证：reference implementation、numerical tolerance、randomized tests、differential testing、shape sweep。
- 可度量：latency、bandwidth、occupancy、register spill、compile failure、runtime failure。
- 可复用：相似 op family、shape bucket、dtype、hardware target 上可能复用。
- 可组合：多个 schedule / tile / layout decisions 组合成完整 kernel。

因此它比普通代码修复更适合做工程型 sanity check。

### Optimization memory item

一个 optimization memory item 至少应包含：

```text
optimization_subproblem:
  op_family
  operator
  shape
  shape_bucket
  dtype
  target_hardware
  backend_or_dsl
  bottleneck
  tile_config
  memory_layout
  schedule_decision
  code_patch
  correctness_evidence
  benchmark_result
  profile_counters
  failed_configs
  reuse_scope
```

关键不是存完整 kernel，而是存可复用的 optimization subproblem：

- 某类 shape 的 tile pattern。
- 某种 layout transform。
- 某个 bottleneck 的修复策略。
- 某类 failed config 的避坑经验。
- 某类 op fusion 的 schedule decision。

### Kernel 强对手

必须对标：

- TVM / AutoTVM。
- TVM Ansor / auto-scheduler。
- MetaSchedule。
- Triton autotune。
- TorchInductor / compiler-generated kernels。
- Vendor libraries / vendor compiler / hand-tuned kernels。
- PTO / PyPTO / Tile-like schedule systems。
- KernelBench / TritonBench / MultiKernelBench。
- LLM coding agent + skill library + profiling tool use。
- AlphaEvolve-like evolutionary program search。

如果 verified optimization memory 不能赢 `Agent + Skills`，它不是独立机制。

### Kernel 小规模训练方向

几台 8 卡服务器不适合从零训练大模型。更合适的是训练小模块，嵌入 agent / autotune / search loop。

| 模块 | 输入 | 输出 | 价值 |
| --- | --- | --- | --- |
| cost model / reranker | op、shape、hardware、schedule、profile | worth_benchmarking / predicted latency | 减少真实 benchmark trial |
| memory retriever | op family、shape bucket、bottleneck、error | similar optimization memory | 提升有用 memory 命中，降低 harmful retrieval |
| failure classifier | compile error、runtime error、wrong output diff、profile anomaly | error type / repair direction | 把失败转成可复用 memory |
| patch proposer | current kernel、profile、failed attempts、retrieved memory | code patch / schedule decision | 减少盲目 trial |
| reward / preference model | candidate A/B + result | preference / expected utility | 支撑 offline rerank 或 RL |

最小数据闭环：

```text
operator + shape + dtype + hardware
-> generated kernel / tile config
-> correctness result
-> latency / bandwidth / occupancy / error
-> bottleneck label
-> next edit
-> final winning config
-> memory write
-> heldout reuse
```

这条闭环的关键是把每次失败和成功都变成可训练、可检索、可复用的数据，而不是只保存最终 kernel。

### Kernel 最小实验

短期任务族：

- matmul variants。
- layernorm / rmsnorm。
- softmax。
- attention block。
- elementwise fusion。
- reduction。
- transpose / layout transform。

对照组：

| 组 | 含义 |
| --- | --- |
| compiler / autotune baseline | Triton autotune、TVM/Ansor、PTO/PyPTO search 等 |
| plain LLM agent | 无专门 skill / memory |
| Agent + Skills | 有 Triton/PTO/CUDA 优化手册、模板、profiling 工具 |
| Agent + retrieved memory | 加 optimization memory 检索 |
| Agent + trained reranker | 加 cost model / reranker |
| Agent + memory + reranker | 完整候选系统 |
| evolutionary agent | generate/evaluate/mutate/select |

主指标：

- correct-and-faster rate。
- best speedup。
- time-to-first-correct。
- time-to-threshold-speedup。
- benchmark trials。
- compile/runtime failure rate。
- harmful memory rate。
- reuse success on heldout shapes / operators。
- memory construction cost。

关键裁决：

> 如果 memory 只能复用同 shape，那只是 cache；如果能跨 shape bucket、operator variant、hardware generation 复用，才有研究价值。

### 与递归分解的关系

Kernel optimization 里的递归分解不是自然语言任务分解，而是 optimization search decomposition：

```text
op family
  -> shape / dtype / hardware bucket
  -> bottleneck diagnosis
  -> schedule subproblem
  -> tile/layout/pipeline decisions
  -> correctness/performance verification
  -> local repair
```

如果系统能在失败时只修某个 optimization subproblem，而不是全局重写 kernel，就更接近 `recursive decomposition + memory`。

### Kernel 失败条件

- Agent + Skills 已经追平 memory 系统。
- Autotune / compiler search 在同等 trial budget 下更强。
- memory 只复用同 shape 或同模板。
- correctness verifier 过弱，导致 false verified kernel。
- performance variance 太大，benchmark result 不稳定。
- trained reranker 只学习 shape popularity，不能学习真实 schedule usefulness。
- memory / reranker overhead 吞掉搜索收益。
- 不能跨 hardware 或 backend 迁移。

## 场景四：普通代码 / 算法任务

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

## 横向场景：小模型作为实验载体和系统 worker

专项调研见 [[11-recursive-decomposition-memory/future-small-model-landscape|小模型研究谱系调研]]。

小模型研究本身已经非常强，主要路线包括：

- data-centric pretraining / overtraining。
- synthetic data 和高质量过滤。
- teacher distillation。
- SFT / DPO / RLVR / rejection sampling / test-time scaling。
- code、math、tool calling 等领域专精。
- 架构效率、量化、端侧部署。
- SLM-default / LLM-fallback 的 agentic system。

因此，本线不能把“小模型变强”写成递归分解 + memory 的直接证据。更合理的定位是：

> 小模型是检验递归分解 + memory 是否具有数据效率、局部控制和系统成本优势的高性价比实验场。

### 为什么小模型与本线相关

小模型适合本线的原因：

- 递归分解、D²、多 agent、local repair 往往需要多次调用，小模型能降低实验成本。
- 小模型上下文理解和鲁棒性弱，更依赖 schema、verifier、typed memory 和明确局部任务边界。
- 小模型容量有限，对训练数据质量更敏感；verified subproblem traces 可能比 raw agent logs 更适合训练。
- 小模型适合承担系统里的局部角色，而不必直接做最终 solver。

可承担角色：

| 角色 | 小模型任务 |
| --- | --- |
| selector | 判断下一步展开哪个子问题 |
| retriever | 根据 proof state / profile / code context 找 memory |
| reranker | 判断 memory 是否有用 |
| verifier helper | 做快速格式、schema、局部一致性检查 |
| repair proposer | 基于 failure memory 提出局部修复 |
| compressor | 把 trace 压缩成 memory item |
| router | 决定是否升级到大模型 |

### 小模型相关候选实验

实验 A：小模型 D² 曲线。

> structural diversity + entropy routing 的收益是否随模型规模变化？

比较 1.5B / 3B / 7B / 14B / 32B 等模型上的 CoT、self-consistency、structural diversity、entropy routing、fixed arbitration。指标包括 accuracy、cost-normalized accuracy、all-wrong rate、at-least-one-correct rate、entropy calibration、token / latency cost。

实验 B：small worker + large fallback。

> 在 recursive subproblem system 中，哪些角色可以由小模型稳定承担？

比较 all large model、all small model、small worker + verifier、small worker + large fallback、small worker + verified memory。指标包括 task success、fallback rate、local repair success、harmful memory rate、latency 和 cost。

实验 C：verified traces 蒸馏小模型。

> verified subproblem memory / local repair traces 是否比 raw agent traces 更适合训练小模型？

比较 raw CoT、raw agent trace、verified subproblem trace、failure + repair trace、generated lemma / helper / schedule memory。指标包括 imitation loss、exact action accuracy、verifier pass rate、local repair success 和 heldout family transfer。

实验 D：SLM-default / LLM-fallback memory agent。

```text
small model proposes next subproblem / memory / repair
-> verifier checks
-> if fail or uncertain, escalate to large model
-> verified outcome writes memory
```

关键裁决：

> 如果大部分局部步骤可由小模型完成，递归分解 + memory 线可自然对接小模型系统化部署；如果小模型频繁 fallback，或多次调用后成本不低，则应收缩为大模型 agent 的辅助模块。

### 小模型方向的失败条件

应承认失败的情况：

- 小模型收益只来自 teacher distillation，无法证明机制增量。
- 任务太窄，只能说明 domain specialization。
- 成本账本显示小模型多次调用后并不便宜。
- 小模型无法稳定使用 memory，harmful retrieval 上升。
- 小模型 local repair 不如大模型 global retry。
- verified trace 训练不优于普通 trace 或 teacher CoT。
- 小模型 worker 需要频繁 fallback，系统复杂度吞掉收益。

## 跨场景数据飞轮

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

## 和 Phase 1 / D² 的关系

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

## 关键攻击

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

## 适合声称什么

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

如果目标是高价值研究主线，优先 Lean。

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

如果目标是用起小规模 GPU/NPU 并形成工程闭环，优先 Kernel。

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

如果目标是快速 sanity check，选择代码 / 算法，但要收窄。

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
