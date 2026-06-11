---
type: survey
status: draft
date: 2026-06-11
tags:
  - recursive-decomposition
  - memory
  - kernel-optimization
  - performance
  - triton
  - autotuning
  - agent
---

# Kernel 性能优化工作谱系调研

调查时间：2026-06-11。

这里的“性能优化”主要指 GPU / NPU kernel、Triton / CUDA / Tile / PTO / PyPTO 类 DSL、LLM / Agent 自动 kernel 生成与优化、compiler / autotune / search 等方向。

核心结论：

> “让 LLM 写更快 kernel”已经不是空白方向。现有工作已经覆盖 typed spec、correctness harness、compile-test-profile loop、autotune、Agent+Skills、multi-agent、RL / SFT、跨平台 benchmark、best-version history。若本项目进入这个方向，必须把主张收缩为：显式 verified optimization memory 是否能在强基线之上减少搜索成本、降低失败率，并在 heldout op / shape / hardware 上产生可归因复用收益。

## 总体谱系

| 谱系 | 代表 | 已经解决 / 吸收的部分 | 对本项目的压力 |
| --- | --- | --- | --- |
| 专家库 / vendor primitives | cuDNN、TensorRT-LLM、CUTLASS / CuTe DSL、FlashAttention、FlashInfer、AMD Composable Kernel | 常见高价值算子已有强手写或模板化实现 | 不能只证明“写出某个更快 kernel” |
| 编译器 / autotune | TVM AutoTVM、Ansor、MetaSchedule、Triton autotune、TorchInductor、XLA / OpenXLA、IREE / MLIR | schedule search、cost model、measurement-based tuning 已成熟 | 必须对标 trial budget 和 cost-quality |
| Kernel DSL / tile abstraction | Triton、TileLang、CuTe DSL、JAX Pallas、ThunderKittens、PTO / PyPTO / Tile-like systems | 把低层 CUDA 细节提升为 tile / block / memory / schedule 控制 | memory 若只复用 template，研究增量弱 |
| LLM kernel benchmark | KernelBench、TritonBench、MultiKernelBench、NPUKernelBench / AscendKernelGen | 标准化 correct-and-fast 评估、跨 GPU/NPU/TPU 平台 | 需要使用强公开 benchmark 或自建同等强度 benchmark |
| LLM / Agent 优化系统 | GEAK、PRAGMA、Astra、AutoKernel、KernelSkill、AutoTriton / TritonRL | compile-test-profile loop、multi-agent、history、skills、RL/SFT 已出现 | 不能把 agent loop 或 feedback loop 当新贡献 |
| Evolutionary coding agents | AlphaEvolve、OpenEvolve、CodeEvolve | evaluator-driven code mutation / selection 已是强通用范式 | 必须对标 evolutionary search，而不是只对标 single-shot LLM |
| LLM serving kernels | FlashAttention、PagedAttention、FlashInfer、ThunderKittens 等 | LLM serving 中 attention、KV-cache、GEMM、MoE 等已高度优化 | 如果选服务内核，需要面对最强工程实现 |

## 1. 专家库与手写高性能 kernel

这类工作是最强现实基线，不一定是研究论文基线。

代表：

- NVIDIA cuDNN / TensorRT-LLM。
- NVIDIA CUTLASS / CuTe DSL。
- FlashAttention / FlashAttention-2 / FlashAttention-3。
- FlashInfer。
- AMD Composable Kernel。
- vendor compiler / vendor libraries。
- 手写 CUDA / HIP / NPU kernels。

它们的特点：

- 由专家长期调优。
- 对具体硬件架构、tensor core、memory hierarchy、cache、warp / block mapping 有深度适配。
- 常见算子已经极难击败。
- 对 benchmark 论文而言，常常是不可绕开的 “ceiling baseline”。

对本项目的含义：

- 如果目标是常见 LLM serving 算子，必须承认专家库极强。
- 若只在小算子或 toy benchmark 上赢 PyTorch eager，研究价值不足。
- 更合理的切口不是“超过专家库”，而是“在长尾算子、shape variant、new hardware、custom fusion 上减少专家工作量”。

## 2. 编译器、自动调优与搜索

代表：

- TVM AutoTVM。
- TVM Ansor / auto-scheduler。
- TVM MetaSchedule。
- Triton autotune。
- TorchInductor / torch.compile。
- XLA / OpenXLA。
- IREE / MLIR。
- Halide autoscheduler。
- Tiramisu / tensor compiler 系列。

这条线已经长期回答：

> 给定计算定义和 search space，系统能否自动搜索 tiling、thread binding、vectorization、unrolling、fusion、layout、memory placement 等 schedule，并在真实硬件上测量，找到高性能实现？

典型能力：

- 自动生成 schedule candidates。
- 在真实硬件上 benchmark。
- 用 cost model / evolutionary search / Bayesian search / rule-based sketch 缩小搜索空间。
- 保存测量结果和历史最优 schedule。

对本项目的压力：

- `tile_config -> performance` 的学习已经是 cost model / auto-scheduler 的传统问题。
- `trial budget` 是必须报告的核心指标。
- 如果 memory 只是保存某个 shape 的最佳 config，它就是 autotune cache。
- 如果 trained reranker 只是传统 cost model，研究新意应降级为工程实现。

本项目可争取的剩余点：

- 将 LLM/Agent 的 reasoning trace、compile error、profile bottleneck、failed config 也纳入可训练 memory，而不只是 schedule-performance pair。
- 让 memory 有显式适用范围和失败边界。
- 证明 memory 能跨 shape bucket / op variant / backend 迁移，而不是同 shape 复用。

## 3. Kernel DSL 与 tile abstraction

代表：

- Triton。
- TileLang。
- CuTe DSL。
- JAX Pallas。
- ThunderKittens。
- PTO / PyPTO / Tile-like schedule systems。

这类系统的共同点：

- 避免直接写完整 CUDA 细节。
- 保留 tile、block、warp、memory、layout、pipeline 的关键控制。
- 更适合 LLM / Agent 修改，因为语义层级高于 CUDA C++。
- 也更适合生成 memory item，因为可把优化决策抽象成 tile / schedule / layout / pipeline 子问题。

对本项目的含义：

> 若做 verified optimization memory，最好不要直接从裸 CUDA 起步，而应优先选择 Triton / Tile / PTO / PyPTO 这类中层抽象。

原因：

- memory item 更容易结构化。
- 编译与测试闭环更快。
- 失败类型更容易归因。
- 训练数据更容易标准化。

风险：

- 抽象层太高，可能错过关键低层优化。
- 抽象层太低，LLM/Agent 容易浪费在语法和微细节上。
- 这正是一些 2026 agent kernel 优化工作开始研究的点：agent 操作的抽象层会显著影响 trial efficiency。

## 4. Benchmark-driven kernel generation

### KernelBench

KernelBench 是当前最重要的公开基线之一。它把任务定义为：

> 给定 PyTorch 程序，让模型生成 correct and efficient CUDA / DSL kernels，在目标 GPU 上评估正确性与性能。

关键设计：

- 任务覆盖 single-kernel operators、simple fusion patterns、full model architectures、HuggingFace 模型等层级。
- 正确性通过 randomized inputs 与 PyTorch reference 对比。
- 性能通过与 PyTorch reference 的 wall-clock speedup 比较。
- 指标 `fast_p` 同时要求 correct 和 speedup 超过阈值。
- 已支持 CUDA、Triton、CuTe、TileLang、ThunderKittens、HIP 等 backend。
- 近期路线还包括 multi-turn / test-time scaling、RLVR、evolutionary search、roofline sanity check。

对本项目的含义：

- KernelBench 已经把 typed spec、correctness harness、speedup metric、multi-backend evaluation 做成公共基础设施。
- 任何新工作若只做 “PyTorch -> kernel -> correct-and-fast”，容易被吸收。
- 如果使用 KernelBench，应把研究问题落在 memory 是否降低 trial / 提升 heldout reuse，而不是 pass@k。

### TritonBench

TritonBench 更聚焦 Triton operator generation。

它的重要性在于：

- Triton 是 LLM 生成 kernel 的自然 DSL。
- benchmark 明确评估 execution accuracy 和 performance。
- 任务来自 PyTorch semantics 与真实 Triton kernel 场景。

对本项目的含义：

- 若选择 Triton 作为主后端，TritonBench 是直接 benchmark。
- 但 TritonBench 也意味着“LLM 生成 Triton”本身不新，必须加上 memory / reranker / profile-conditioned repair 的机制消融。

### MultiKernelBench

MultiKernelBench 把平台扩展到 GPU / NPU / TPU。

它的重要性：

- 证明 kernel generation 已经从 NVIDIA-only 走向 multi-platform。
- 对 NPU / TPU 场景，DSL、编译器、profile 约束都不同。
- 跨平台泛化本身成为新问题。

对本项目的含义：

- 如果项目想利用 NPU 资源，不能只看 CUDA/Triton。
- 但 multi-platform 会显著增加工程复杂度。
- 更现实的路线是先在单平台做 memory，后续再测试跨硬件迁移。

## 5. LLM / Agent kernel optimization

### GEAK

GEAK 是 AMD ROCm 生态中的 Triton kernel AI agent 与 benchmark 工作。

它说明：

- Agent + evaluator + optimizer 的结构已经进入 vendor 生态。
- Triton-on-ROCm / AMD GPU 是重要平台。
- “LLM 自动生成/优化 Triton kernel”已经是工程实践方向。

### PRAGMA

PRAGMA 的关键点是 profile-guided multi-agent kernel generation。

它已经吸收：

- execution feedback。
- fine-grained hardware profiling。
- historical best versions。
- iterative refinement。

对本项目的压力：

> 不能只说“我们把 profile 反馈给 agent”。这已经是已有工作。

剩余切口应是：

- profile bottleneck 是否写成可复用 memory item。
- 相似 bottleneck 是否能跨任务检索复用。
- failed profile / failed config 是否能减少未来无效 trial。

### Astra

Astra 是 multi-agent GPU kernel performance optimization。

它与许多 PyTorch-to-kernel benchmark 不同：

- 从已有 CUDA implementations 出发，而不是从 PyTorch specification 起步。
- 使用 specialized agents 做 generation、testing、profiling、planning。
- 对真实 serving framework 中的 kernels 做优化。

对本项目的压力：

- multi-agent decomposition 已经被用于 kernel 优化。
- compile-test-profile-plan loop 已经是强 baseline。
- 如果本项目做 Agent+Memory，必须和 Astra 类系统比较。

### AutoKernel

AutoKernel 是 2026 年的 autonomous GPU kernel optimization preprint。

它的关键机制：

- 给定 PyTorch model。
- profiling 找 bottleneck。
- 用 Amdahl's law 排序优化优先级。
- 在 Triton / CUDA C++ 后端中反复生成和 refinement。
- 用多阶段 correctness harness 验证 smoke test、shape sweep、numerical stability、determinism、edge cases。
- 做大量 experiments。

对本项目的压力：

- “自动找 bottleneck + 迭代优化 + correctness harness”已被吸收。
- 未来强 baseline 不应只是 single-shot LLM，而应包括这种 agent-driven search。

### KernelSkill

KernelSkill 是 2026 年的 multi-agent kernel optimization preprint，尤其需要注意，因为它已经显式使用 memory / skill 叙事。

它的关键点：

- 用 expert optimization skills 替代 LLM 隐式 heuristic。
- 有 long-term reusable expert skills。
- 有 short-term memory 防止重复 backtracking。
- 在 KernelBench Level 1-3 上报告较强结果。

对本项目的直接压力：

> “skills + memory for kernel optimization”已经被提出。若本项目走这一方向，必须更清楚地区分 `verified optimization memory` 与 skill library / short-term memory。

可能的差异化：

- memory item 必须有 correctness evidence、benchmark evidence、profile evidence、validity scope、failure cases。
- 必须做 harmful memory / distractor memory / stale memory stress test。
- 必须证明跨 heldout shape / op / hardware 的可归因复用，而不是仅提升同 benchmark。

## 6. 训练型方向：SFT / RL / reranking

已有训练型方向包括：

- KernelLLM：PyTorch -> Triton 的 specialized model / SFT 方向。
- AutoTriton / TritonRL：用 correctness / performance reward 训练 Triton generation。
- DRTriton / synthetic data RL 类工作：大规模合成数据 + RL。
- Cost model / schedule reranker：传统 compiler 和新 agent 系统都会使用。
- KernelBench RLVR pipeline：KernelBench repo 已提到把生成 kernel、云端 GPU evaluation、reward 转换串成 RL playground。

这些方向说明：

> 小规模训练可以做，但主问题不是“能否训练一个 kernel model”，而是训练哪个模块最值得。

对本项目更合适的小规模训练目标：

| 模块 | 输入 | 输出 | 价值 |
| --- | --- | --- | --- |
| cost model / reranker | op、shape、hardware、schedule、profile | worth_benchmarking / predicted latency | 减少真实 benchmark trial |
| memory retriever | op family、shape bucket、bottleneck、error | similar optimization memory | 提升有用 memory 命中，降低 harmful retrieval |
| failure classifier | compile error、runtime error、wrong output diff、profile anomaly | error type / repair direction | 把失败转成可复用 memory |
| patch proposer | current kernel、profile、failed attempts、retrieved memory | code patch / schedule decision | 减少盲目 trial |
| reward / preference model | candidate A/B + result | preference / expected utility | 支撑 offline rerank 或 RL |

最不建议的训练目标：

- 从零训练大模型。
- 直接训练通用 “Triton 代码生成器” 但没有强 benchmark 和强 baseline。
- 只学习 shape popularity 或 template popularity 的 reranker。

## 7. Evolutionary coding agents

AlphaEvolve / OpenEvolve / CodeEvolve 类系统把问题抽象为：

```text
candidate program
-> evaluator
-> score
-> mutation / selection
-> next candidate
```

这对 kernel optimization 是天然强对手。

原因：

- kernel 性能优化有自动 evaluator。
- 正确性和速度能作为选择压力。
- 不需要显式 memory，也可能通过 population 保留经验。
- 可以发现非直觉的优化。

对本项目的压力：

- 不能只对标 greedy agent。
- 至少需要一个 generate/evaluate/mutate/select baseline。
- 如果 explicit memory 不能减少 trial 或提升 extrapolation，它可能不如 evolutionary population search。

本项目可争取的差异：

- evolutionary search 保留的是 candidate population，不一定形成可解释、可检索、可迁移的 optimization memory。
- verified memory 可以把失败和成功都变成结构化对象，服务后续任务，而不是只服务当前搜索。

## 8. NPU / 多平台方向

NPU / TPU / AMD GPU 等非 NVIDIA 平台正在进入 kernel generation benchmark。

相关方向：

- MultiKernelBench。
- AscendKernelGen / NPUKernelBench。
- Triton-on-ROCm / GEAK。
- JAX Pallas / TPU kernels。
- vendor-specific DSL / compiler。

机会：

- 数据少，生态较新，LLM 训练数据不如 CUDA/Triton 丰富。
- 平台差异使 memory 的 validity_scope 更重要。
- 多平台迁移能更强地检验 memory 是否只是在背模板。

风险：

- 工程门槛高。
- profiling 工具链和编译器细节复杂。
- 同一 memory item 跨平台可能失效。
- benchmark reproducibility 更难。

建议：

> 先不要从多平台作为第一击。先在一个平台上定义 verified optimization memory 与强消融，再把跨平台作为后续 stress test。

## 9. 已被吃掉的“弱版本收益”

以下点不应再包装成主贡献：

| 弱收益 | 已有吸收 |
| --- | --- |
| typed kernel spec | KernelBench / TritonBench / MultiKernelBench |
| correctness harness | KernelBench、AutoKernel、各种 benchmark |
| compile-test loop | 几乎所有 agent kernel 系统 |
| profile feedback | PRAGMA、Astra、AutoKernel、GEAK |
| best-version history | PRAGMA / agent loops / evolutionary search |
| autotune / trial search | TVM、Triton autotune、TorchInductor、compiler stack |
| skill library | KernelSkill、Agent+Skills |
| SFT / RL for kernel generation | KernelLLM、AutoTriton、TritonRL、KernelBench RLVR |
| multi-platform benchmark | MultiKernelBench、AscendKernelGen |

因此，本项目不应声称：

- 第一次让 LLM 写 kernel。
- 第一次让 agent profile / debug / optimize。
- 第一次把 kernel 优化做成闭环。
- 第一次使用 memory / skill。

## 10. 可能仍有价值的剩余切口

### 切口 A：Verified Optimization Memory Schema

把每次优化尝试写成结构化 memory item：

```text
optimization_memory:
  op_family
  operator
  shape_bucket
  dtype
  hardware
  backend
  bottleneck
  schedule_decision
  tile_config
  memory_layout
  code_patch
  correctness_evidence
  benchmark_result
  profile_counters
  failed_configs
  validity_scope
  reuse_history
  harmful_cases
```

核心不是“存经验”，而是让 memory 能被验证、检索、复用、更新、诊断。

### 切口 B：失败记忆

失败 memory 可能比成功 memory 更有研究价值。

原因：

- kernel search 大量成本花在 compile fail、runtime fail、wrong output、性能差。
- failed config 可避免重复探索。
- error pattern 可训练 repair classifier。
- profile anomaly 可指向局部 bottleneck。

指标：

- compile failure rate 是否下降。
- wrong output rate 是否下降。
- repeated bad trial 是否下降。
- time-to-first-correct 是否下降。

### 切口 C：跨 heldout 复用

必须从同 shape cache 走向 heldout：

- heldout shape。
- heldout shape bucket。
- heldout op variant。
- heldout fusion pattern。
- heldout hardware generation。
- heldout backend。

如果只能同 shape 复用，应降级为 cache / autotune database。

### 切口 D：Memory 的可归因消融

需要设计消融，证明收益来自 memory，而不是更多 token、更多 trial 或更强 agent。

必要对照：

- Agent+Skills。
- Agent+Skills + random memory。
- Agent+Skills + stale memory。
- Agent+Skills + distractor memory。
- Agent+Skills + raw trace memory。
- Agent+Skills + verified optimization memory。
- Agent+Skills + verified memory + reranker。

关键指标：

- useful retrieval rate。
- harmful retrieval rate。
- memory-hit trial savings。
- memory-conditioned patch success。
- local repair success。

### 切口 E：抽象层选择

Agent 操作对象可以是：

- raw CUDA code。
- Triton code。
- Tile / PTO / PyPTO schedule。
- schedule IR。
- profile bottleneck + decision space。

本项目可以把“抽象层选择”作为一个实证问题：

> 哪种中间表示最适合 memory 复用与训练？

这比单纯比较模型更接近递归分解与 memory。

## 11. 建议实验位置

如果本项目做性能优化，推荐实验主张：

> 在强 Agent+Skills、autotune、profile-guided search、evolutionary search 基线下，verified optimization memory 是否能减少 trial budget、降低失败率，并在 heldout op / shape / hardware 上提升 correct-and-fast rate？

最小实验结构：

| 组 | 含义 |
| --- | --- |
| Compiler / autotune | Triton autotune、TorchInductor、TVM/Ansor/MetaSchedule 或 PTO/PyPTO search |
| Plain LLM agent | 无 skill / memory |
| Agent+Skills | Triton/PTO/CUDA 优化手册、模板、profiling 工具 |
| Agent+Skills+RawTrace | 检索原始历史 trace |
| Agent+Skills+VerifiedMemory | 检索结构化 optimization memory |
| Agent+Skills+VerifiedMemory+Reranker | 加 trained usefulness / cost reranker |
| Evolutionary Search | generate/evaluate/mutate/select |

主指标：

- correct-and-fast rate。
- best speedup。
- time-to-first-correct。
- time-to-threshold-speedup。
- benchmark trials。
- compile/runtime failure rate。
- wrong-output rate。
- useful memory hit rate。
- harmful memory rate。
- heldout shape / op / hardware reuse。
- memory construction overhead。

关键失败条件：

- Agent+Skills 追平 memory 系统。
- Triton autotune / compiler search 在同等 trial budget 下更强。
- memory 只复用同 shape。
- distractor memory 明显误导系统。
- benchmark variance 大到无法复现。
- reranker 只学习常见 shape / op popularity。
- memory overhead 吞掉搜索收益。

## 12. 对本项目的定位建议

性能优化可以作为递归分解与 memory 线的工程型高价值分支，但不是最干净的理论主线。

它的优势：

- correctness 和 performance 都可自动验证。
- 数据闭环硬。
- 小规模 GPU/NPU 可真实产生训练数据。
- 能把失败、profile、repair、schedule decision 都变成可训练对象。

它的劣势：

- 强基线极强。
- 很容易被 autotune / Agent+Skills / evolutionary search 吸收。
- 工程投入大，benchmark reproducibility 难。
- 如果没有 heldout 复用，很容易退化成 cache。

更合适的项目命题：

> Verified Optimization Memory for Kernel Search：系统能否从 kernel 优化过程里提取可验证、可复用、可更新的 optimization subproblem memory，并在未来 heldout 任务中降低搜索成本或错误率？

不要写成：

> LLM 自动写高性能 kernel。

## 参考

### Benchmark / LLM kernel generation

- [KernelBench GitHub](https://github.com/ScalingIntelligence/KernelBench)
- [KernelBench paper](https://arxiv.org/abs/2502.10517)
- [KernelBench OpenReview](https://openreview.net/forum?id=yeoN1iQT1x)
- [TritonBench paper](https://arxiv.org/abs/2502.14752)
- [TritonBench GitHub](https://github.com/thunlp/tritonbench)
- [MultiKernelBench](https://arxiv.org/html/2507.17773v2)
- [AscendKernelGen / NPUKernelBench](https://arxiv.org/abs/2601.07160)

### Agent / RL / training systems

- [GEAK: Triton Kernel AI Agent & Evaluation Benchmarks](https://rocm.blogs.amd.com/software-tools-optimization/triton-kernel-ai/README.html)
- [PRAGMA](https://arxiv.org/html/2511.06345)
- [Astra](https://arxiv.org/abs/2509.07506)
- [Astra GitHub](https://github.com/Anjiang-Wei/Astra)
- [AutoKernel](https://arxiv.org/abs/2603.21331)
- [KernelSkill](https://arxiv.org/abs/2603.10085)
- [AutoTriton / Automatic Triton Programming with RL](https://arxiv.org/html/2507.05687v1)
- [TritonRL](https://arxiv.org/html/2510.17891v1)
- [KernelLLM](https://huggingface.co/facebook/KernelLLM)

### Compiler / DSL / expert libraries

- [TVM Ansor / AutoScheduler](https://tvm.apache.org/2021/03/03/intro-auto-scheduler)
- [TVM MetaSchedule](https://tvm.apache.org/docs/deep_dive/tensor_ir/tutorials/meta_schedule.html)
- [Triton autotune](https://triton-lang.org/main/python-api/generated/triton.autotune.html)
- [NVIDIA CUTLASS / CuTe DSL](https://docs.nvidia.com/cutlass/latest/overview.html)
- [JAX Pallas](https://docs.jax.dev/en/latest/pallas/index.html)
- [ThunderKittens](https://github.com/HazyResearch/ThunderKittens)
- [FlashAttention](https://arxiv.org/abs/2205.14135)
- [FlashInfer](https://github.com/flashinfer-ai/flashinfer)

### Evolutionary coding agents

- [AlphaEvolve](https://arxiv.org/abs/2506.13131)
- [DeepMind AlphaEvolve blog](https://deepmind.google/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/)
- [OpenEvolve](https://github.com/algorithmicsuperintelligence/openevolve)
