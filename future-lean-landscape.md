---
type: survey
status: active
date: 2026-06-11
tags:
  - recursive-decomposition
  - memory
  - verified-subproblem-memory
  - lean
  - theorem-proving
  - survey
---

# Lean 方向详尽调研

> [!summary] 本页定位
> 本页是 Lean / 形式化证明方向的专项调研。它服务于 [[future-scenarios|未来研究候选场景]] 中的 `verified subproblem memory` 主张：能否让系统自动生成、验证、索引并复用新的中间 lemma / proof fragment / subproblem graph。

调查时间：2026-06-11。

## 一页版结论

Lean 是递归分解与 memory 线里最干净、也最危险的候选主战场。

它干净，是因为：

- Lean proof checker 提供强验证。
- proof state、tactic、lemma、dependency graph 天然是局部中间对象。
- proof search 本身天然具有递归子目标结构。
- 成功和失败都能产生明确反馈。
- memory 的“可复用性”可以用 heldout theorem 上的 proof success / proof search cost / lemma reuse rate 度量。

它危险，是因为：

- theorem retrieval、premise selection、proof-state interaction、whole-proof generation、RL with proof assistant feedback、test-time search、recursive subgoal decomposition 都已有强工作。
- LeanSearch / Loogle / LeanExplore / ReProver / LeanDojo / DeepSeek-Prover / AlphaProof / Seed-Prover / Hilbert 等已经吸收了许多弱版本主张。
- 如果只是“检索已有 theorem”“把过去 proof trace 塞进上下文”“让 agent 反复试 tactic”，不会形成独立研究增量。

当前最可守的 Lean 命题应收缩为：

> 系统能否从 solved / failed proof attempts 中自动形成新的、Lean-verified、带依赖与适用范围的中间 lemma / proof fragment / subproblem memory，并在 family-heldout 或 research-level tasks 上降低 proof search cost、提高 proof success 或提升局部修复成功率。

更短版本：

> 不是 retrieve existing theorem，而是 grow reusable verified lemma memory。

## 为什么 Lean 适合本线

Lean 官方定位是开源编程语言和 proof assistant，用于写可验证代码与形式化证明；其核心卖点之一是 minimal trusted kernel 提供 correctness 保证，并支持强自动化与 metaprogramming。见 [Lean 官方网站](https://lean-lang.org/)。

这对本研究线有三个直接含义。

### 1. Verification 由系统提供

在普通数学题、代码题或 Agent trace 中，判断中间步骤是否真正确很难。Lean 中：

- theorem statement 是类型。
- proof 是 inhabitant / term。
- tactic 只是构造 proof term 的高级接口。
- 最终正确性由 kernel 检查。

因此，`verified subproblem memory` 中的 `verifier` 不需要重新发明。它可以直接是：

```text
Lean kernel check
Lean command-line build
Lean environment tactic execution
```

这让 Lean 成为验证最硬的 sanity check。

### 2. 中间对象天然结构化

Lean proof search 的基本对象天然对齐本线：

| 本线对象 | Lean 实例 |
| --- | --- |
| subproblem | proof state / subgoal |
| instruction | tactic |
| verifier | Lean kernel / tactic execution |
| memory item | lemma / theorem / proof fragment / tactic pattern |
| dependency | imported theorem / local hypothesis / proof DAG |
| recursive decomposition | tactic 把 goal 分解成多个 subgoals |
| local repair | 修改局部 tactic / lemma，而不是重写整个 proof |

这比自然语言 trace 更适合做可回放、可归因、可训练的数据对象。

### 3. 现实强基线足够硬

Lean 方向不会太容易赢。它的强基线已经包括：

- mathlib 中大量人工 formalized mathematics。
- Loogle / LeanSearch / LeanExplore / Moogle 等 theorem search。
- ReProver / LeanDojo 的 retrieval-augmented proving。
- DeepSeek-Prover 系列的大规模 synthetic data、RL 和 search。
- AlphaProof / Seed-Prover 的大规模 RL 与 test-time scaling。
- Hilbert 这类 informal reasoning + formal verifier + retriever + recursive decomposition 的 agentic system。

如果在这些压力下仍能看到 `verified subproblem memory` 的可归因增量，结论会更有说服力。

## Lean 生态底座

### Lean 4

Lean 4 是当前主线。Lean 4 的特点包括：

- dependent type theory / calculus of inductive constructions。
- theorem proving + functional programming。
- tactic mode 和 term mode。
- extensible parser、elaborator、tactics、decision procedures、pretty printer、code generator。
- metaprogramming 能力适合实现 search / automation / data extraction。

来源：

- [Lean 官网](https://lean-lang.org/)
- [The Lean 4 Theorem Prover and Programming Language](https://lean-lang.org/papers/lean4.pdf)
- [Theorem Proving in Lean 4](https://leanprover.github.io/theorem_proving_in_lean4/)

### mathlib4

mathlib4 是 Lean 4 的社区数学库。它包含：

- 数学定义和 theorem。
- programming infrastructure。
- tactics。
- 自动生成文档。
- 活跃社区、Zulip、贡献流程和 CI。

来源：

- [mathlib4 GitHub](https://github.com/leanprover-community/mathlib4)
- [mathlib overview](https://leanprover-community.github.io/mathlib-overview.html)
- [mathlib docs](https://leanprover-community.github.io/mathlib4_docs/index.html)

对本项目的意义：

- mathlib 是最主要的 existing theorem memory。
- 任何 Lean memory 项目都必须证明自己不是“更复杂的 mathlib retrieval”。
- 需要记录 memory item 是否依赖 mathlib theorem、是否只是包装已有 theorem、是否生成新 lemma。

## 工具与基础设施谱系

### Theorem search

Theorem search 是 Lean 方向最直接的强对手。

| 工具 | 类型 | 对本项目的压力 |
| --- | --- | --- |
| Loogle | formal / pattern search | 已能按 constant、name、subexpression、conclusion shape 搜索 Lean / Mathlib declarations |
| LeanSearch | natural-language theorem search | 已能用自然语言找 mathlib theorem |
| Moogle | semantic search | 已能自然语言搜索 mathlib4 |
| LeanExplore | semantic / hybrid search | 面向 Lean 4 declarations，覆盖 Mathlib、Std、Batteries、PhysLean 等多个 package |
| Lean Finder | semantic search | 强调理解数学用户意图 |

来源：

- [Loogle](https://loogle.lean-lang.org/)
- [LeanSearch](https://leansearch.net/)
- [Moogle](https://www.moogle.ai/)
- [LeanExplore paper](https://arxiv.org/html/2506.11085v1)
- [Lean Finder paper](https://arxiv.org/html/2510.15940v1)
- [Searching for Theorems in Mathlib](https://leanprover-community.github.io/blog/posts/searching-for-theorems-in-mathlib/)

对本项目的结论：

> 如果 memory 只是帮助模型找到已有 theorem，它会被 theorem search / premise retrieval 吸收。

可守增量必须是：

- 生成新的 lemma。
- 从多个 solved tasks 抽象出更一般的 lemma。
- 记录 proof-state-specific usefulness，而不是只记录 theorem semantics。
- 记录 failed retrieval / failed proof 的负样本，降低 harmful retrieval。

### LeanDojo / ReProver

LeanDojo 是这条线最重要的基础设施之一。

原始 LeanDojo 提供：

- 从 Lean repos 提取 proof states、tactics、premises、AST、dependencies。
- 把 Lean 变成 programmatic interaction / gym-like environment。
- 构造 benchmark。
- 训练 ReProver，用 retrieval-augmented model 生成下一步 tactic。

LeanDojo-v2 进一步强调：

- Lean 4。
- repository tracing。
- lifelong dataset management。
- retrieval-augmented agents。
- Hugging Face fine-tuning。
- external inference APIs。
- whole-proof generation 和 proof search 两种 proof method。
- Pantograph interaction。
- LeanProgress integration。

来源：

- [LeanDojo 项目页](https://leandojo.org/leandojo.html)
- [LeanDojo paper](https://arxiv.org/abs/2306.15626)
- [LeanDojo docs](https://leandojo.readthedocs.io/en/stable/)
- [ReProver GitHub](https://github.com/lean-dojo/ReProver)

对本项目的结论：

> LeanDojo 已经覆盖 data extraction、environment interaction、retrieval augmented tactic generation 和部分 lifelong dataset management。

因此本项目不能把贡献写成：

- 首次提取 proof state。
- 首次把 Lean 接成 agent environment。
- 首次做 premise retrieval。
- 首次训练 tactic model。

剩余可守点：

- verified generated lemma memory。
- failure-pattern memory。
- proof-state case memory 的 heldout usefulness。
- dependency-aware memory item。
- continual memory growth curve。
- generated memory 的 harmful retrieval control。

### Lean Copilot / LeanAide / llmstep

这些工具更偏用户协作和 workflow integration。

| 工具 | 作用 | 对本项目的压力 |
| --- | --- | --- |
| Lean Copilot | 在 Lean 内原生调用 LLM，建议 tactic / premise / search proof | “LLM + Lean workflow integration”不新 |
| LeanAide | autoformalization、自然语言到 Lean 的辅助工具 | “自然语言辅助形式化”已有直接系统 |
| llmstep | LLM proofstep suggestions，并用 Lean 检查建议 | “多尝试 tactic 并检查”不新 |

来源：

- [Lean Copilot paper](https://arxiv.org/html/2404.12534v2)
- [Lean Copilot GitHub](https://github.com/lean-dojo/LeanCopilot)
- [LeanAide GitHub](https://github.com/siddhartha-gadgil/LeanAide)
- [LeanAide 项目介绍](https://www.renaissancephilanthropy.org/leanaid-bridgingai-and-mathematics-with-autoformalization)
- [llmstep GitHub](https://github.com/wellecks/llmstep)

对本项目的结论：

> 如果实验只是让 LLM 在 Lean 里补 tactic 或建议 theorem，它会被这些工具谱系吸收。

### Aesop / grind / classical automation

Lean 不是只有 LLM。传统自动化也很强。

Aesop 是 Lean 4 的 white-box best-first proof search tactic，可在用户定义规则集上搜索，并集成 simplifier。Lean 4 新自动化如 `grind` 也在提升 routine proof automation。

来源：

- [Aesop paper](https://people.compute.dtu.dk/ahfrom/aesop-camera-ready.pdf)
- [Aesop GitHub](https://github.com/leanprover-community/aesop)
- [Lean 官网 grind 示例](https://lean-lang.org/)

对本项目的结论：

> Lean memory 方向需要对标传统 automation。若 generated memory 只是补充 simp/aesop 已能解决的 routine lemma，价值较低。

## 模型与系统谱系

### ReProver

ReProver 是 LeanDojo 的 retrieval-augmented prover。其核心是：

- premise retriever。
- proof state + retrieved premises -> tactic generation。
- accessible premises 与 hard negative 构造。
- benchmark 来自 mathlib theorem/proof extraction。

来源：

- [LeanDojo paper](https://arxiv.org/abs/2306.15626)
- [ReProver GitHub](https://github.com/lean-dojo/ReProver)

对本项目的压力：

> Retrieval-augmented tactic generation 是已被验证的强基线。

### DeepSeek-Prover 系列

DeepSeek-Prover 展示了 Lean 方向中数据和训练路线的强吸收。

| 系统 | 核心机制 | 代表结果 / 意义 |
| --- | --- | --- |
| DeepSeek-Prover | 大规模 synthetic Lean 4 data，从自然语言题目生成 formal statements 和 proofs | 8M formal statements with proofs；miniF2F-test 46.3% with 64 samples / 52% cumulative；FIMO 5/148 |
| DeepSeek-Prover-V1.5 | SFT + proof assistant feedback RL + RMaxTS / MCTS-style diverse proof path search | miniF2F 63.5%，ProofNet 25.3% |
| DeepSeek-Prover-V2 | recursive theorem proving pipeline，subgoal decomposition，informal + formal reasoning unified，RL | MiniF2F-test 约 88.9% pass ratio；PutnamBench 47/658 或项目页口径 49/658；AIME 24-25 选题 6/15 |

来源：

- [DeepSeek-Prover](https://arxiv.org/abs/2405.14333)
- [DeepSeek-Prover-V1.5](https://arxiv.org/abs/2408.08152)
- [DeepSeek-Prover-V2](https://arxiv.org/abs/2504.21801)
- [DeepSeek-Prover-V2 GitHub](https://github.com/deepseek-ai/DeepSeek-Prover-V2)

对本项目的结论：

> “synthetic data + Lean feedback + RL + recursive subgoal decomposition”已经是强主线，不能作为本项目的新意。

剩余问题应更细：

- subgoal decomposition 产生的 solved subgoal 是否可跨任务复用？
- resolved subgoal proof 是否能升级为 named/generated lemma？
- generated lemma 的适用范围如何学习？
- 失败 subgoal 是否能变成 reusable negative memory？

### AlphaProof

AlphaProof 是 Google DeepMind 的 formal math RL 系统。它把 Lean 环境建模为 sequential decision-making：

- state 是 Lean tactic state。
- action 是 tactic text。
- reward 与 proof completion / tactic cost 相关。
- search 和 RL 在 Lean verifier 反馈下迭代。
- 2024 IMO 中与 AlphaGeometry 2 组合达到银牌水平。
- Nature 论文中进一步明确了 Lean environment、state/action/reward、goal decomposition、TTRL 等设计。

来源：

- [DeepMind blog: IMO silver](https://deepmind.google/blog/ai-solves-imo-problems-at-silver-medal-level/)
- [Nature: Olympiad-level formal mathematical reasoning with reinforcement learning](https://www.nature.com/articles/s41586-025-09833-y)

对本项目的压力：

> Lean as RL environment 已经被高强度验证。若本项目谈“可学习控制反馈”或“proof search RL”，必须承认 AlphaProof 已覆盖大框架。

本项目可保留的不同点：

- 是否显式产生 reusable verified memory。
- 是否评估 memory growth 对 heldout tasks 的边际收益。
- 是否从 proof search trace 中形成可诊断、可更新、可迁移的中间对象。

### Seed-Prover

Seed-Prover 是 ByteDance Seed 的 Lean formal proving 系列。项目页显示：

- Seed-Prover 1.0 参与 IMO 2025，记录多个 Lean verified proof。
- Seed-Prover 1.5 声称解决 88% PutnamBench、11/12 Putnam 2025，并强调 learning from experience、agentic RL 和 test-time workflow。

来源：

- [Seed-Prover GitHub](https://github.com/ByteDance-Seed/Seed-Prover)
- [Seed-Prover 1.5 arXiv](https://arxiv.org/html/2512.17260v1)
- [Seed-Prover blog](https://seed.bytedance.com/en/blog/seed-prover-1-5-advanced-mathematical-reasoning-through-a-novel-agentic-architecture)

对本项目的压力：

> “experience accumulation”“agentic prover”“TTS workflow”已经被强系统吸收。若本项目谈 memory，必须区分是 general experience / trace history，还是可验证、可索引、可复用的 subproblem memory。

### Hilbert

Hilbert 是很贴近本线的对标系统，因为它直接使用：

- informal reasoner。
- specialized Lean prover。
- formal verifier。
- semantic theorem retriever。
- recursive decomposition。
- verifier feedback refinement。

论文摘要称其在 PutnamBench 和 miniF2F 上有强结果，并强调 recursive decomposition 连接 informal reasoning 与 formal proof generation。

来源：

- [Hilbert arXiv](https://arxiv.org/abs/2509.22819)
- [Hilbert GitHub](https://github.com/apple/ml-hilbert)

对本项目的压力：

> “递归分解 + Lean verifier + retriever + agentic loop”已经是直接强对手。

本项目若做 Lean，需要明确：

- 是否只是 Hilbert-like recursive proving。
- 是否额外维护 verified memory。
- memory 是否跨任务复用，而不是只服务当前 proof search。
- 是否降低 recursive decomposition 的搜索成本。

### Kimina-Prover、APOLLO 等

Kimina-Prover、APOLLO 等也属于 Lean formal proving 前沿。

- Kimina-Prover 强调 large formal reasoning model、reasoning-driven exploration、Lean 4 proof generation。
- APOLLO 强调 LLM + Lean compiler feedback collaboration，报告 miniF2F 上高准确率和降低 sampling cost。

来源：

- [Kimina-Prover Preview](https://arxiv.org/abs/2504.11354)
- [Kimina-Prover GitHub](https://github.com/MoonshotAI/Kimina-Prover-Preview)
- [APOLLO OpenReview](https://openreview.net/forum?id=fxDCgOruk0)

对本项目的压力：

> Lean compiler feedback、test-time search、reasoning model specialization 都不是空白。

## Benchmark 与数据谱系

### miniF2F / miniF2F-v2

miniF2F 是 formal-to-formal benchmark，覆盖 olympiad、AMC、AIME、IMO、高中和本科数学题。

但 miniF2F 已被严肃 challenge。miniF2F-Lean Revisited 指出：

- 端到端 pipeline 需要自然语言理解、formalization、proof。
- 原 miniF2F 中 formal / informal statement mismatch 影响评估。
- 他们修正后提出 miniF2F-v2，并显示端到端性能与单独 autoformalization / theorem proving 指标之间存在明显错位。

来源：

- [miniF2F GitHub](https://github.com/openai/miniF2F)
- [miniF2F-Lean Revisited](https://openreview.net/forum?id=KtaHv0YUyh)

对本项目的结论：

> miniF2F 可作为历史基准，但不适合作为唯一裁决。对 memory 研究，更重要的是 family-heldout、subgoal reuse、research-level proof tasks。

### ProofNet

ProofNet 是 undergraduate-level math benchmark，包含 Lean 3 formal theorem statement、自然语言 theorem statement、自然语言 proof，覆盖实分析、复分析、线性代数、抽象代数、拓扑等。

来源：

- [ProofNet paper](https://arxiv.org/abs/2302.12433)
- [ProofNet GitHub](https://github.com/zhangir-azerbayev/ProofNet)

对本项目的结论：

> ProofNet 适合评估 autoformalization 与 formal proving，但 Lean 3 和 formalization quality / benchmark age 要考虑。

### PutnamBench

PutnamBench 面向 Putnam competition，具备多语言 formalization：

- 论文版：1692 hand-constructed formalizations of 640 theorems，Lean 4 + Isabelle，部分 Coq。
- 项目页后来显示更多 formalizations，覆盖 1962-2025，支持 Lean 4 / Isabelle / Coq。

来源：

- [PutnamBench paper](https://arxiv.org/abs/2407.11214)
- [PutnamBench GitHub](https://github.com/trishullab/PutnamBench)

对本项目的结论：

> PutnamBench 是强 benchmark，但很多系统已在上面卷 SOTA。若做 memory，不能只报告 solved count；应报告 memory hit、reuse、proof search cost、heldout family、harmful memory。

### FIMO / FormalMATH / ProverBench

DeepSeek-Prover 系列引入或使用多个 formal math benchmark：

- FIMO：formalized IMO / shortlist style tasks。
- FormalMATH：更广的 formal math tasks。
- ProverBench：DeepSeek-Prover-V2 引入的 325 formalized problems，包括 AIME 24-25 selected problems 和 textbook problems。

来源：

- [DeepSeek-Prover](https://arxiv.org/abs/2405.14333)
- [DeepSeek-Prover-V2](https://arxiv.org/abs/2504.21801)

对本项目的结论：

> 这些 benchmark 可用于证明 proof-generation 能力，但未必直接适合验证 memory。需要额外设计 memory construction / reuse split。

### RLMEval

RLMEval 聚焦 research-level neural theorem proving，从真实 Lean formalization projects / Lean Blueprint 项目中构造评估。

摘要中最关键的结果：

- 613 theorems from 6 Lean projects。
- state-of-the-art models 在更现实 setting 下仍有明显 gap。
- best model 只有约 10.3% pass rate。

来源：

- [RLMEval arXiv](https://arxiv.org/abs/2510.25427)
- [RLMEval GitHub](https://github.com/augustepoiroux/RLMEval)

对本项目的结论：

> RLMEval 更接近“真实 formalization project”难度。若本项目想证明 memory 对 research-level formalization 有价值，RLMEval 比 miniF2F 更有说服力。

### FormalML

FormalML 是 Lean 4 benchmark，面向机器学习理论中的 formal subgoal completion。

摘要中最关键点：

- 任务是 subgoal completion：给定人类 sketch 留下的短但非平凡 proof obligation。
- 数据来自 optimization 和 probability inequalities。
- 4937 extracted subgoal completion cases。
- 结合 premise retrieval 与 complex research-level contexts。

来源：

- [FormalML OpenReview](https://openreview.net/forum?id=wCRZbspSZi)
- [FormalML GitHub](https://github.com/njuyxw/FormalML)

对本项目的结论：

> FormalML 很适合验证 proof-state memory / subgoal memory，因为它直接把任务压到“局部 proof obligation completion”。

### Lean Workbook / Lean-GitHub / Herald

这些数据方向说明 Lean 生态数据正在扩张：

- Lean Workbook：大量 Lean 4 formalized math problems 和部分 searched proofs。
- LEAN-GitHub：从大量 Lean 4 repos 编译形成 theorem proving dataset。
- Herald：把 Mathlib4 corpus 转为自然语言注释数据，用于 natural-formal alignment。

来源：

- [Lean-Workbook release note](https://github.com/InternLM/InternLM-Math)
- [LEAN-GitHub](https://arxiv.org/html/2407.17227v1)
- [Herald OpenReview](https://openreview.net/forum?id=Se6MgCtRhz)

对本项目的结论：

> 数据规模不再是唯一瓶颈。更关键的是数据对象是否支持 reusable memory、negative memory、dependency-aware reuse 和 heldout transfer。

## 已被吸收的弱版本主张

| 弱版本主张 | 已有吸收 |
| --- | --- |
| Lean 可以验证 proof correctness | Lean / mathlib 基础能力 |
| 可以搜索已有 theorem | Loogle、LeanSearch、Moogle、LeanExplore、Lean Finder |
| 可以从 Lean repo 提取 proof states / tactics / premises | LeanDojo |
| 可以让模型与 Lean environment 交互 | LeanDojo、Pantograph、AlphaProof、DeepSeek-Prover、Seed-Prover |
| 可以用 retrieval 增强 theorem proving | ReProver、LeanDojo-v2、Hilbert |
| 可以训练 tactic generator / whole-proof generator | ReProver、DeepSeek-Prover、Kimina、Seed-Prover |
| 可以用 Lean feedback 做 RL | DeepSeek-Prover-V1.5、AlphaProof、Seed-Prover |
| 可以递归分解 theorem / subgoals | DeepSeek-Prover-V2、Hilbert、AlphaProof goal decomposition |
| 可以用自然语言 reasoner + formal verifier | Hilbert、DeepSeek-Prover-V2、AlphaProof formalizer pipeline |
| 可以端到端 autoformalize + prove | DeepSeek-Prover、LeanAide、Conjecturing / Lean-FIRe 等 |

因此，本项目不能把这些作为主贡献。

## 仍可能有价值的剩余切口

### 切口 A：Generated Verified Lemma Memory

核心问题：

> 系统能否从 solved / failed proof attempts 中自动提出新的 lemma，并由 Lean 验证，然后在 heldout tasks 中复用？

这与 theorem retrieval 的区别：

- theorem retrieval 找已有 theorem。
- generated lemma memory 增长新 theorem。

Memory item：

```text
generated_lemma_memory:
  statement
  proof
  source_tasks
  abstraction_origin
  dependencies
  validity_scope
  failed_applications
  successful_reuse_cases
  usefulness_score
```

关键指标：

- generated lemma pass rate。
- nontriviality / non-duplication rate。
- heldout reuse rate。
- proof search node reduction。
- proof time reduction。
- harmful retrieval rate。
- memory construction cost。

强失败条件：

- generated lemma 只是原 theorem 重命名。
- generated lemma 只是已有 mathlib theorem 的包装。
- heldout tasks 上没有复用收益。
- memory retrieval 噪声吞掉收益。

### 切口 B：Proof-State Case Memory

核心问题：

> 给定当前 proof state，过去相似 proof state 的 closing tactic / local proof fragment 是否比 theorem retrieval 更有用？

这比 generated lemma memory 更稳，更适合第一阶段。

Memory item：

```text
proof_state_case:
  normalized_goal
  local_context_signature
  closing_tactic_or_fragment
  required_premises
  proof_result
  failure_modes
  valid_scope
```

对照：

- no memory。
- theorem retrieval。
- raw proof trace retrieval。
- proof-state case memory。
- corrupted / distractor case memory。

关键指标：

- local proof completion rate。
- top-k useful case rate。
- harmful retrieval rate。
- average proof steps。
- time-to-close-subgoal。
- cross-project generalization。

强失败条件：

- proof-state case memory 不优于 theorem retrieval。
- 只在 near-duplicate theorem 上有效。
- 检索到的 tactic 过拟合 local names / imports。

### 切口 C：Failure / Negative Memory

核心问题：

> 失败 proof attempts 是否能变成可复用的 negative memory，减少未来无效 search？

Lean proof search 的成本常花在：

- tactic type error。
- impossible premise。
- apply 方向错误。
- simp set 不合适。
- search branch 爆炸。
- wrong theorem retrieval。

Memory item：

```text
failure_memory:
  proof_state_signature
  attempted_tactic
  error_message
  retrieved_premises
  failure_type
  repair_direction
  invalid_scope
  future_avoidance_count
```

关键指标：

- repeated bad tactic rate 是否下降。
- average branching factor 是否下降。
- time-to-first-valid-tactic 是否下降。
- proof search node count 是否下降。
- false avoidance 是否可控。

这个方向可能比 success memory 更实用，因为 Lean search 中失败尝试数量远大于成功 proof。

### 切口 D：Dependency-Aware Memory

核心问题：

> memory item 是否能记录它依赖哪些 theorem、imports、local hypotheses、typeclass assumptions，并据此判断何时可用？

这区别于普通 RAG：

- RAG 常只看相似性。
- dependency-aware memory 需要验证可见性、依赖、scope、imports。

关键指标：

- accessible-memory precision。
- invalid dependency retrieval rate。
- repair after missing import。
- local theorem visibility accuracy。

### 切口 E：Recursive Subproblem DAG

核心问题：

> 一个 theorem 的 proof search 是否能显式展开成 typed subproblem DAG，并在 DAG 节点级别缓存、复用、修复？

节点：

```text
proof_node:
  node_id
  theorem_or_goal
  local_context
  parent_nodes
  child_nodes
  tactic_or_lemma
  verifier_status
  dependencies
  reusable_as_lemma
  uncertainty
```

操作：

- split goal。
- prove subgoal。
- verify node。
- generalize node to lemma。
- retrieve similar node。
- repair failed node。
- merge proof。

对照：

- whole-proof generation。
- sequential tactic generation。
- tree search without memory。
- recursive DAG with cache only。
- recursive DAG with verified memory。

关键指标：

- local repair success。
- global restart rate。
- reusable node rate。
- heldout node reuse。
- proof depth / width generalization。

这个方向最贴近“递归分解 + memory”，但工程复杂，不应作为第一击。

### 切口 F：Conjecture / Subgoal Completion

Conjecturing 论文指出，一些数学 formalization 不能只当成 direct translation；需要先 conjecture explicit answer / bound / proposition。FormalML 则把问题收缩到 proof sketch 中 unresolved subgoals。

对本项目的意义：

- memory 不一定只存 lemma，也可以存 conjecture pattern。
- 对某些 theorem，正确子目标是什么本身就是核心。
- `subgoal completion` 是比 whole theorem proving 更局部、更适合 memory 的任务。

候选实验：

- 在 FormalML 上做 proof-state memory。
- 在 ConjectureBench / PutnamBench 子集上做 conjecture pattern memory。
- 比较 answer/conjecture provided vs generated 的差距。

来源：

- [Conjecturing paper](https://openreview.net/forum?id=JKILJjKKvt)
- [FormalML](https://openreview.net/forum?id=wCRZbspSZi)

## 建议的第一阶段实验

第一阶段不建议直接做 generated lemma discovery。那太难，也容易失败得不可诊断。

更稳的第一阶段：

> proof-state case memory + theorem retrieval strong baseline + heldout subgoal completion。

### 实验 1：Proof-State Case Memory Sanity Check

目标：

> 过去相似 proof state 的 closing tactic / proof fragment 是否能提供 theorem retrieval 之外的增量？

数据：

- mathlib / LeanDojo extracted proof states。
- FormalML subgoal completion。
- 可选 RLMEval 子集。

构造：

```text
train memory bank:
  proof_state -> closing_tactic / proof_fragment / required_premises

test:
  heldout proof states from same family
  template-heldout
  project-heldout
```

对照：

| 组 | 含义 |
| --- | --- |
| no retrieval | 直接 prover |
| theorem retrieval | LeanSearch / ReProver-style premise retrieval |
| raw trace retrieval | 检索过去 proof text |
| proof-state case memory | 检索 normalized proof-state cases |
| case memory + theorem retrieval | 组合 |
| distractor case memory | 加入相似但错误 cases |

主指标：

- subgoal completion rate。
- proof steps。
- proof search nodes。
- time-to-close。
- useful retrieved case rate。
- harmful retrieval rate。
- cross-project transfer。

最小胜利：

> 在同等 prover、同等 top-k、同等 token budget 下，proof-state case memory 相比 theorem retrieval 单独使用，在 heldout subgoal completion 上提高 success 或降低 search cost，并且 distractor memory 不会显著误导。

失败解释：

- 如果只在 near duplicate 上有效，它是 cache。
- 如果不优于 theorem retrieval，它是弱 memory。
- 如果 harmful retrieval 高，它需要 dependency / scope 约束。

### 实验 2：Failure Memory

目标：

> 失败 tactic / failed retrieval / Lean error 是否能减少未来 search 浪费？

数据：

- prover search logs。
- tactic error messages。
- proof-state transitions。
- failed premise retrieval。

对照：

- no failure memory。
- text-only error history。
- structured failure memory。
- structured failure memory + repair classifier。

指标：

- invalid tactic rate。
- repeated bad tactic rate。
- branch explosion rate。
- proof search node count。
- success under fixed compute。

最小胜利：

> 在固定 search budget 下，failure memory 降低无效分支并提高 pass rate 或减少 time-to-proof。

### 实验 3：Generated Lemma Memory 小规模版本

目标：

> 在限定 family 内，系统能否生成非平凡、Lean-verified、可复用的 lemma？

建议先选小领域：

- algebra identities。
- inequalities。
- list / finite set lemmas。
- simple probability / optimization sublemmas。
- FormalML 中反复出现的局部 proof obligations。

对照：

- mathlib retrieval。
- raw trace memory。
- generated lemma memory。
- generated lemma memory + usefulness reranker。

硬过滤：

- lemma 必须通过 Lean。
- lemma 不能与 source theorem α-equivalent。
- lemma 不能只是已有 theorem 的 rename。
- lemma 必须在至少一个 heldout theorem 中被成功使用。

指标：

- generated valid lemma rate。
- non-duplicate rate。
- heldout reuse rate。
- proof search cost reduction。
- harmful lemma retrieval rate。
- construction cost。

最小胜利：

> 生成 lemma 的构造成本可被后续 heldout reuse amortize，且不是 theorem retrieval 已能替代。

## 强基线清单

Lean 方向至少要对标以下基线。

### 检索基线

- Loogle。
- LeanSearch。
- LeanExplore。
- Moogle。
- ReProver-style dense premise retrieval。
- theorem name / namespace heuristic。

### Prover 基线

- no-retrieval tactic generation。
- ReProver / LeanDojo-v2 prover。
- whole-proof generation。
- theorem retrieval + tactic generation。
- Aesop / simp / grind / linarith / nlinarith 等自动化。
- DeepSeek-Prover 系列可用模型或公开 proof outputs。
- Seed-Prover / Kimina / Hilbert 若可复现或可调用，则作为高端参考。

### Memory 消融基线

- no memory。
- final theorem cache。
- raw proof trace memory。
- theorem retrieval memory。
- proof-state case memory。
- generated lemma memory。
- corrupted / stale / distractor memory。
- dependency-aware filtered memory。

### 成本账本

必须记录：

- prover calls。
- Lean tactic executions。
- verified / failed tactic count。
- proof search nodes。
- total generated tokens。
- total input tokens。
- wall-clock。
- GPU time。
- Lean build / import cost。
- memory construction cost。
- retrieval latency。
- human curation cost。

如果只报告 pass rate，不报告 proof search cost，memory 结论会很弱。

## 数据与实现建议

### 推荐基础设施

优先使用：

- Lean 4。
- mathlib4。
- LeanDojo-v2 或 Pantograph 做 proof interaction。
- Loogle / LeanSearch / LeanExplore 做 retrieval baseline。
- FormalML / RLMEval / PutnamBench / miniF2F-v2 做不同层级评估。

不建议第一阶段自建完整 Lean environment wrapper，除非现有工具无法满足：

- proof-state normalization。
- proof trace extraction。
- tactic execution logging。
- dependency graph extraction。
- memory write/read API。

### Memory bank schema

建议统一存储：

```text
memory_id
memory_type: proof_state_case | generated_lemma | failure | dependency_pattern
lean_version
mathlib_revision
imports
source_file
source_theorem
source_proof_state
normalized_goal
local_context_signature
statement
proof_or_tactic
required_premises
dependencies
verifier_status
validity_scope
failed_applications
successful_reuse_cases
embedding
symbolic_index_keys
created_at
last_verified_at
```

特别要记录：

- Lean version。
- mathlib revision。
- imports。
- required premises。
- source theorem。
- whether generated or retrieved。

否则 memory 很容易因为版本或 visibility 失效。

### Retrieval 设计

不要只做 embedding retrieval。建议三路召回：

1. semantic retrieval：goal / context embedding。
2. symbolic retrieval：constants、types、namespace、conclusion shape。
3. dependency retrieval：accessible premises / imports / local hypotheses。

然后 rerank：

```text
proof_state
candidate_memory
dependency_compatibility
historical_reuse
failure_cases
```

输出：

```text
useful_score
expected_tactic
expected_cost_reduction
harmful_risk
```

## 研究定位建议

### 不建议主张

不建议写：

- Lean 证明可以被 LLM 自动化。
- Lean verifier 让 proof 正确。
- retrieval 能帮 theorem proving。
- recursive decomposition 能帮 formal proof。
- Lean feedback 可以做 RL。

这些已被强工作覆盖。

### 建议主张

建议写：

> 现有 Lean prover 多关注当前 theorem 的搜索和已有 theorem retrieval；本方向关注 proof attempts 之后留下的可验证中间对象，能否形成可增长、可复用、可诊断、可更新的 memory，并在 heldout tasks 上产生可归因的 proof search cost 或 success 增量。

### 与递归分解 + memory 的关系

Lean 是最自然的主战场，因为：

- recursive decomposition 对应 subgoal graph。
- memory 对应 generated lemma / proof-state case / proof fragment。
- verifier 对应 Lean kernel。
- reuse 对应 heldout theorem proof search。
- local repair 对应修某个 subgoal / tactic / lemma。

但 Lean 也强迫本线面对最硬现实：

> 如果在 Lean 里都只能做 retrieval / cache，而不能产生 reusable verified subproblem memory，那么“递归分解 + memory”作为强研究主张需要大幅收缩。

## 推荐推进顺序

### Stage 0：复现与基线

- 搭 Lean 4 + mathlib4 + LeanDojo-v2 / Pantograph。
- 选 FormalML 或 LeanDojo extracted proof-state dataset。
- 跑 theorem retrieval + tactic generation baseline。
- 建成本账本。

输出：

> 一个可重复的 proof-state completion benchmark pipeline。

### Stage 1：Proof-State Case Memory

- 从训练 proofs 中提取 normalized proof_state -> closing tactic / fragment。
- 做 symbolic + semantic retrieval。
- 对比 theorem retrieval。
- 加 distractor / stale memory。

输出：

> proof-state case memory 是否有 theorem retrieval 之外的局部增量。

### Stage 2：Failure Memory

- 记录 failed tactic、Lean error、failed retrieval。
- 训练或规则化 failure classifier。
- 在 fixed search budget 下减少无效分支。

输出：

> 失败轨迹是否能成为有用 negative memory。

### Stage 3：Generated Lemma Memory

- 在小领域中生成 candidate lemma。
- Lean 验证。
- 去重和 generality 检查。
- heldout theorem reuse。

输出：

> 是否存在真正 grow memory 的信号。

### Stage 4：Recursive Subproblem DAG

- 把 proof search trace 显式组织成 subproblem DAG。
- 节点级缓存、复用、修复。
- 与 flat search / sequential tactic generation 对照。

输出：

> 是否形成递归分解 + memory 的完整机制。

## 最关键挑战

### 1. Generated lemma 的非平凡性

一个 lemma 通过 Lean 不代表有用。它可能：

- 太专用。
- 只是原题重命名。
- 已经存在于 mathlib。
- 无法被自动检索和复用。

必须设计 nontriviality / novelty / reuse 检查。

### 2. Memory construction cost

如果生成和验证 memory 的成本超过后续节省，它不是有效 flywheel。

需要报告：

- 生成多少 candidate。
- 通过多少。
- 去重后多少。
- heldout 复用多少。
- 每个有效 reuse 的成本。

### 3. Version drift

Lean 和 mathlib 变化快。Memory item 必须绑定：

- Lean version。
- mathlib commit。
- imports。
- dependencies。

否则长期 memory 会失效。

### 4. Harmful retrieval

错误相似 memory 会误导 proof search。必须测试：

- distractor memory。
- stale memory。
- near-miss theorem。
- wrong namespace / missing import。

### 5. Human curation leakage

如果 memory schema、lemma family、heldout split 由研究者过度手工设计，实验会被 challenge 为 DSL / benchmark engineering。

需要：

- 自动抽取。
- 预注册 split。
- heldout family。
- cross-project transfer。

### 6. SOTA 系统不可复现

AlphaProof、Seed-Prover、DeepSeek-Prover-V2、Hilbert 等强系统不一定完全可复现或成本过高。处理方式：

- 把它们作为 high-end reference。
- 第一阶段对标可复现开源基线，如 LeanDojo/ReProver、LeanSearch、FormalML baseline。
- 如果未来要投稿，再补高端 baseline 或公开 proof outputs 对比。

## 当前裁决

Lean 方向值得做，但不能以“LLM 自动证明 Lean theorem”作为主线。

最建议的可输命题：

> 在 Lean 4 proof-state completion / theorem proving tasks 上，proof-state case memory、failure memory、generated verified lemma memory 是否分别、以及组合后，相对 theorem retrieval、raw trace memory 和 strong prover baseline，在 heldout tasks 上形成可核算的 proof success、proof search cost 或 local repair 增量。

最建议的第一实验：

> FormalML / LeanDojo proof states 上的 proof-state case memory，对标 theorem retrieval，报告 success、search nodes、harmful retrieval 和 heldout transfer。

最有价值但更高风险的后续实验：

> 自动生成 verified lemma memory，并证明这些 lemma 在 heldout theorem proving 中被复用且节省 proof search cost。

如果第一实验失败：

- Lean memory 方向应暂时降级为 retrieval / prover engineering。
- 不应继续扩张到 generated lemma 和 recursive DAG。

如果第一实验成功：

- 可继续做 failure memory。
- 再做 generated lemma memory。
- 最后才谈 recursive subproblem DAG。

## 参考

### Lean / mathlib

- [Lean 官方网站](https://lean-lang.org/)
- [The Lean 4 Theorem Prover and Programming Language](https://lean-lang.org/papers/lean4.pdf)
- [Theorem Proving in Lean 4](https://leanprover.github.io/theorem_proving_in_lean4/)
- [mathlib4 GitHub](https://github.com/leanprover-community/mathlib4)
- [mathlib docs](https://leanprover-community.github.io/mathlib4_docs/index.html)

### Tooling / search / infrastructure

- [LeanDojo](https://leandojo.org/leandojo.html)
- [LeanDojo paper](https://arxiv.org/abs/2306.15626)
- [ReProver GitHub](https://github.com/lean-dojo/ReProver)
- [Lean Copilot](https://arxiv.org/html/2404.12534v2)
- [LeanAide](https://github.com/siddhartha-gadgil/LeanAide)
- [Loogle](https://loogle.lean-lang.org/)
- [LeanSearch](https://leansearch.net/)
- [LeanExplore](https://arxiv.org/html/2506.11085v1)
- [Aesop](https://people.compute.dtu.dk/ahfrom/aesop-camera-ready.pdf)

### Provers / systems

- [DeepSeek-Prover](https://arxiv.org/abs/2405.14333)
- [DeepSeek-Prover-V1.5](https://arxiv.org/abs/2408.08152)
- [DeepSeek-Prover-V2](https://arxiv.org/abs/2504.21801)
- [AlphaProof Nature paper](https://www.nature.com/articles/s41586-025-09833-y)
- [AlphaProof DeepMind blog](https://deepmind.google/blog/ai-solves-imo-problems-at-silver-medal-level/)
- [Seed-Prover GitHub](https://github.com/ByteDance-Seed/Seed-Prover)
- [Seed-Prover 1.5](https://arxiv.org/html/2512.17260v1)
- [Hilbert](https://arxiv.org/abs/2509.22819)
- [Kimina-Prover](https://arxiv.org/abs/2504.11354)
- [APOLLO](https://openreview.net/forum?id=fxDCgOruk0)

### Benchmarks / datasets

- [miniF2F GitHub](https://github.com/openai/miniF2F)
- [miniF2F-Lean Revisited](https://openreview.net/forum?id=KtaHv0YUyh)
- [ProofNet](https://arxiv.org/abs/2302.12433)
- [PutnamBench](https://arxiv.org/abs/2407.11214)
- [RLMEval](https://arxiv.org/abs/2510.25427)
- [FormalML](https://openreview.net/forum?id=wCRZbspSZi)
- [Conjecturing](https://openreview.net/forum?id=JKILJjKKvt)
- [LEAN-GitHub](https://arxiv.org/html/2407.17227v1)
- [Herald](https://openreview.net/forum?id=Se6MgCtRhz)
