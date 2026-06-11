---
type: plan
status: draft
tags:
  - recursive-decomposition
  - memory
  - verified-subproblem-memory
  - non-lean
  - code
  - algorithms
---

# 非 Lean Verified Subproblem Memory

Lean 的最大好处是把问题框定在数学定理证明这个高价值领域，并提供严格 proof checker。若考虑非 Lean 方向，不能只找“能判分”的任务，而要找：

> 是否存在可局部验证、可复用、可组合的中间对象。

这才对应 `verified subproblem memory` 的核心价值。

## 选择标准

一个非 Lean 方向是否合适，取决于三点：

- 中间对象是否可验证。
- 中间对象是否可跨任务复用。
- 中间对象是否能组合成更大解，并支持局部纠偏。

普通最终答案评测不够。单元测试、oracle、symbolic checker、property tests 能提供验证，但验证强度和 Lean proof checker 不同。

## 候选方向

| 方向 | 可验证性 | 是否适合 memory / recursive decomposition |
| --- | --- | --- |
| 程序验证 / Dafny / F* / Coq / Isabelle | 很强 | 很适合，本质接近 Lean |
| SMT / SAT / symbolic algebra | 强 | 适合存 rewrite rule、lemma、invariant |
| 算法合成 + property tests | 中强 | 适合，但 verifier 弱于 proof checker |
| GPU / NPU kernel 优化 | 中强 | 正确性和性能可验证，适合工程型 memory，但强对手很多 |
| 代码生成 / 修复 + 单测 | 中 | 可做 sanity check，但容易退化成 retrieval |
| 多文件工程修复 | 中弱 | 需要 memory，但验证不完整，噪声大 |

## 代码任务何时真的需要它

如果只是 LeetCode 风格单题，通常不需要高级 memory。RAG、例题检索、self-debug、单测循环可能已经足够。

更合适的代码任务是：

> 系统从已解决任务中提取 verified helper function / invariant / patch pattern / API usage pattern，并在 heldout 任务中复用。

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

## 推荐非 Lean 方向

### 方向 A：程序合成 / 算法库构造

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

### 方向 B：SMT / Rewrite Rule Memory

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

### 方向 C：代码修复 / 多文件工程任务

问题：

> 系统能否从历史 patch 中提取 verified repair pattern / API usage pattern，并在后续代码任务中复用？

这适合工程 sanity check，但高价值叙事弱于 Lean / SMT。

原因：

- 验证常依赖不完整单测。
- 任务边界噪声大。
- patch pattern 容易退化成 retrieval。
- memory 是否真正可组合较难证明。

### 方向 D：GPU / NPU Kernel 优化

问题：

> 系统能否从已优化 kernels 中提取 verified optimization subproblems，并在 heldout operators / shapes / hardware settings 上复用？

这是一个更工程化的候选分支。正确性可用 reference implementation / randomized tests / differential testing 验证，性能可用 benchmark / profile counters 验证。

但它的强对手很多：

- autotune。
- compiler search。
- Agent + Skills。
- evolutionary coding agents。

详细计划见 [[11-recursive-decomposition-memory/kernel-optimization-verified-memory|Kernel Optimization Verified Memory]]。

## 与 Lean 的差异

| 维度 | Lean | 非 Lean 代码 / 算法 |
| --- | --- | --- |
| 验证 | proof checker 严格验证 | 单测 / property tests / oracle / SMT，强度不一 |
| 中间对象 | theorem / lemma / proof fragment | helper function / invariant / rewrite rule / patch pattern |
| 复用性 | 数学结构天然支持抽象复用 | 取决于任务 family 和接口设计 |
| 组合性 | proof DAG 天然存在 | 需要额外定义依赖和接口 |
| 风险 | theorem retrieval 已有强对手 | 容易退化成 RAG / template reuse / test hacking |

## 失败条件

非 Lean 方向应承认失败的情况：

- memory 只在同模板近邻上有效。
- verifier 太弱，导致 false verified memory。
- 复用收益来自 retrieval，而不是 verified subproblem。
- helper / invariant / rewrite rule 不能跨 family 复用。
- memory construction cost 吞掉后续收益。
- 局部修复失败，仍需全局重做。

## 当前建议

如果追求高价值和说服力，Lean / formal proof 仍是更自然的主场。

如果追求工程 sanity check，优先级可以是：

1. 程序合成 / 算法库构造。
2. SMT / rewrite rule memory。
3. GPU / NPU kernel 优化。
4. 代码修复 / 多文件工程任务。

普通代码 benchmark 不应作为第一主线，除非它能明确产生 verified helper / invariant / repair pattern，并在 heldout tasks 上证明复用收益。
