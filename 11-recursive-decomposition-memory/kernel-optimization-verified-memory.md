---
type: plan
status: draft
tags:
  - recursive-decomposition
  - memory
  - verified-subproblem-memory
  - kernel-optimization
  - triton
  - npu
  - performance
---

# Kernel Optimization Verified Memory

GPU / NPU kernel 性能优化可以作为 `verified subproblem memory` 的工程型候选分支，但前提是研究对象不是“写出一个更快 kernel”，而是：

> 系统能否从已优化 kernels 中提取 verified optimization subproblems，并在 heldout operators / shapes / hardware settings 上复用这些 memory，从而减少搜索成本、降低错误率或提升性能？

这条线的优势是 correctness 和 performance 都可被验证；风险是它容易退化为 autotuning、template search 或 Agent+Skills。

已有工作与强基线谱系见 [[11-recursive-decomposition-memory/kernel-performance-optimization-landscape-2026-06|Kernel 性能优化工作谱系调研]]。该调研的核心结论是：typed spec、correctness harness、compile-test-profile loop、autotune、multi-agent、RL / SFT、skills / memory 叙事都已有强吸收；本方向的可守切口应收缩为 verified optimization memory 在强基线上的可归因增量。

## 为什么符合候选范畴

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

## Memory Item

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

## 对标谱系

### 1. Compiler / Autotune 系统

这些是最基础强对手：

- TVM / AutoTVM。
- TVM Ansor / auto-scheduler。
- MetaSchedule。
- Triton autotune。
- TorchInductor / compiler-generated kernels。
- Vendor libraries / vendor compiler / hand-tuned kernels。
- PTO / PyPTO / Tile-like schedule systems。

它们回答：

> 不用 LLM memory，仅靠 search space、cost model、measurement-based tuning，能否找到同等或更优 kernel？

### 2. Benchmark-Driven Kernel Generation

这些对手已经把“LLM 生成高性能 kernel”变成标准化问题：

- KernelBench：LLM 写 CUDA / DSL kernels，评估 correct-and-fast。
- TritonBench：面向 Triton generation 的 performance-aware benchmark。
- MultiKernelBench：多平台 kernel generation，覆盖 GPU / NPU / TPU。

它们回答：

> 直接让 LLM / agent 生成 kernel，在 correctness + speedup 指标下能做到什么程度？

### 3. Agent + Skills

这是最直接对手：

- LLM coding agent。
- kernel optimization skill library。
- Triton / CUDA / PTO prompt recipes。
- profiling tool use。
- compiler error repair。
- benchmark feedback loop。

它回答：

> 给 Agent 足够好的 skill、模板、profiling 工具和调试循环，是否已经足够？

如果 verified optimization memory 不能赢 `Agent + Skills`，它不是独立机制。

### 4. Evolutionary / Search Agent

代表形态：

- AlphaEvolve-like coding agent。
- evolutionary program search。
- generate -> evaluate -> mutate -> select。
- reward-guided code optimization。

它回答：

> 不显式维护 reusable subproblem memory，仅用 evaluator 驱动代码演化，能否更快找到高性能解？

### 5. Human / Template Baseline

必须保留：

- 人工 Triton template。
- 手写 CUDA / NPU kernel。
- 常见 op family 的 expert schedule。
- vendor tutorial / best practice template。

否则系统可能只是复现已有模板。

## 小规模训练方向

几台 8 卡服务器不适合从零训练大模型。更合适的是训练小模块，嵌入 agent / autotune / search loop。

### 方向 A：Cost Model / Reranker

输入：

```text
operator
shape
dtype
hardware
tile_config
schedule_decision
profile_counters
```

输出：

```text
predicted_latency
speedup_bucket
worth_benchmarking
```

目标：

- 减少真实 benchmark 次数。
- 在同样 trial budget 下更快找到 correct-and-fast kernel。
- 区分“看起来合理但性能差”的 schedule。

### 方向 B：Optimization Memory Retriever

输入：

```text
current_kernel
op_family
shape_bucket
profile_bottleneck
compiler_error_or_runtime_error
```

输出：

```text
similar_optimization_cases
tile_patterns
layout_patterns
failed_configs_to_avoid
```

目标：

- 让 memory 从经验文本变成可检索 optimization subproblem。
- 降低 harmful memory rate。
- 提升 heldout shape / op 的 reuse success。

### 方向 C：Patch / Schedule Proposal Model

输入：

```text
current_kernel
profiling_result
failed_attempts
retrieved_memory
```

输出：

```text
next_tile_config
next_schedule_decision
code_patch
```

训练方式：

- SFT / LoRA。
- pairwise preference。
- offline trajectories from autotune / agent search。

目标：

- 减少无效候选。
- 缩短 time-to-first-correct。
- 缩短 time-to-threshold-speedup。

### 方向 D：Correctness / Failure Classifier

输入：

```text
compiler_error
runtime_error
wrong_output_diff
numeric_error_pattern
profile_anomaly
```

输出：

```text
error_type
likely_root_cause
repair_direction
```

目标：

- 减少 agent 盲目 debug。
- 将失败转为可复用 failed-config memory。
- 提高局部纠偏成功率。

### 方向 E：Reward / Preference Model

数据：

```text
(kernel_config_a, result_a) vs (kernel_config_b, result_b)
```

目标：

- rerank LLM / agent 生成的候选。
- 在 correctness 和 performance 之间做稳定裁决。
- 结合 benchmark result 形成训练信号。

## 最小数据闭环

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

## 最小实验

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

## 与递归分解的关系

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

## 失败条件

这条线应承认失败的情况：

- Agent + Skills 已经追平 memory 系统。
- Autotune / compiler search 在同等 trial budget 下更强。
- memory 只复用同 shape 或同模板。
- correctness verifier 过弱，导致 false verified kernel。
- performance variance 太大，benchmark result 不稳定。
- trained reranker 只学习 shape popularity，不能学习真实 schedule usefulness。
- memory / reranker overhead 吞掉搜索收益。
- 不能跨 hardware 或 backend 迁移。

## 当前定位

这条线适合作为非 Lean 方向里的工程型高价值应用分支：

> verified optimization memory for kernel search。

它比普通代码修复更可验证，也比 Lean 更工程化。但它必须正面对标 Agent+Skills、autotuning、compiler search 和 evolutionary coding agents。

## 参考对标

- [KernelBench: Can LLMs Write Efficient GPU Kernels?](https://arxiv.org/abs/2502.10517)
- [KernelBench GitHub](https://github.com/ScalingIntelligence/KernelBench)
- [TritonBench: Benchmarking Large Language Model Capabilities for Generating Triton Operators](https://arxiv.org/abs/2502.14752)
- [TritonBench GitHub](https://github.com/thunlp/tritonbench)
- [MultiKernelBench: A Multi-Platform Benchmark for Kernel Generation](https://arxiv.org/html/2507.17773v2)
- [GEAK: Introducing Triton Kernel AI Agent & Evaluation Benchmarks](https://arxiv.org/abs/2507.23194)
- [TVM Ansor / AutoScheduler](https://tvm.apache.org/2021/03/03/intro-auto-scheduler)
- [AlphaEvolve: A coding agent for scientific and algorithmic discovery](https://arxiv.org/abs/2506.13131)
