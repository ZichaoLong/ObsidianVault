---
type: review
status: active
tags:
  - recursive-decomposition
  - memory
  - phase1-review
---

# Phase 1 材料审视

审视对象：

- `Phase1FinalReport-v1.pdf`
- `Phase1.pptx`

材料标题是 `Memory-Augmented Recursive-Decomposition Reasoning Agents`。从报告和汇报材料看，Phase 1 的工程演进很清楚，结果也有价值；但研究命题需要从标题中拆出来，否则容易把多个机制混在一起。

## 核心系统

最终系统是 Agent v6 / D²。

它的机制是：

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

## 六代演进的实际含义

| 版本 | 机制 | 主要收益 | 暴露问题 |
| --- | --- | --- | --- |
| v1 | tool-calling + graph memory | 证明工具和 memory 方向可做 | planning 和 computing 混在一个 prompt，cache poisoning |
| v2 | planner + solver + reflection | 角色拆分明显提升 | 无 failure isolation，reflection 成本均匀 |
| v3 | master-slave + file workspaces | 隔离、审计、持久化 | recipe 固定，I/O 和复杂度路由问题 |
| v4 | HCE complexity routing | 首个 adaptive compute | complexity score 需要额外 LLM call 且可能错 |
| v5 | structural diversity voting | 错误去相关开始发挥作用 | 全同意时浪费计算，全分歧时无恢复 |
| v6 | semantic entropy routing + arbiters | 用分歧信号做自适应计算和纠偏 | 需要更强对照拆清楚收益来源 |

这条演进说明：项目真正逐步摸到的是 adaptive compute，而不是单纯 memory。

## 当前证据强度

| 主张 | 证据强度 | 说明 |
| --- | --- | --- |
| D² beats CoT on math benchmarks | 强 | GSM8K、SynthMath-1K、AIME、U-MATH 都有提升，且有统计检验 |
| Disagreement is a difficulty signal | 强 | entropy 与 accuracy 单调相关，且 SynthMath 触发更多 arbitration |
| Structural diversity matters | 中强 | pairwise error-set Jaccard 说明错误不完全重合，但还需 same-prompt 多样性对照 |
| Arbiter benefits from failed traces | 中 | v6 有提升，但需要 answer-only / trace-aware / random trace 消融 |
| Recursive decomposition is the key | 中弱 | v6 更像并行多策略分解；真正递归结构在 v3 更明显但不是最终主贡献 |
| Memory is the key | 弱到中 | memory 贯穿演进，但缺少独立 ablation |
| Planning is main bottleneck | 中 | causal ladder 有启发，但 intervention 设计可能引入 gold-plan / gold-answer 信息泄漏 |

## 主要亮点

### 1. 自建 SynthMath-1K 是正确方向

公共 math benchmarks 已经高度污染。材料里给出 GSM8K 变体和 Gemma 引用 GSM8K 编号的证据。自建算法生成、答案可验证、SHA-256 唯一的 benchmark 对后续研究很重要。

这与本线研究直接相关：

> 如果要证明 decomposition 或 memory 的真实收益，必须优先使用可生成、可控、可分 family 的 benchmark。

### 2. Entropy routing 比 HCE routing 更自然

v4 需要额外复杂度估计调用。v6 直接利用 agents 的答案分歧。

这有两个优点：

- 难度信号来自实际求解过程，而不是另一个可能出错的 estimator。
- 分歧不仅是标量，还携带失败 traces，可给 arbiter 使用。

### 3. 小模型场景很合适

3B / 4B 小模型能力不足，正好暴露 planning、strategy、tool-calling、context 的问题。

但后续必须对接 thinking model / larger model，否则会被质疑只是在补小模型短板。

## 主要弱点

### 1. Memory 贡献没有被拆开

材料多处提 memory：

- graph memory。
- context envelope。
- file workspace。
- verified knowledge memory。
- trace memory。

但没有清楚回答：

> 如果移除 memory，只保留 decomposition diversity 和 entropy routing，性能会掉多少？

也没有区分：

- memory 存最终答案。
- memory 存自然语言 trace。
- memory 存 verified subproblem。
- memory 存失败类型。
- memory 存可复用修复策略。

因此当前不能把 memory 写成已证明主贡献。

### 2. Recursive decomposition 与 multi-agent ensemble 有混淆

v6 的三 agent 并行更像：

- heterogeneous prompting。
- structured ensemble。
- self-consistency 的结构化版本。
- multi-agent debate / arbitration 的变体。

它不等同于真正的递归分解。

真正递归分解应至少有：

- 子问题树或 DAG。
- 节点输入输出。
- 父子依赖。
- 子节点 verifier。
- 子节点可缓存。
- 高不确定节点继续展开。

v3 有 file workspace 和 mini-master 的递归痕迹，但 v6 的最终结果更偏 ensemble routing。

### 3. Baseline 需要更强

材料已经有 14-baseline comparison，但后续若投稿或扩展，强对手应包括：

- same prompt x3。
- self-consistency k=3/5/更多。
- structural prompts but no entropy routing。
- random routing。
- HCE routing。
- answer-only arbiter。
- trace-aware arbiter。
- multi-agent debate。
- Tree-of-Thought。
- Reflexion。
- plan-execute with verifier。

否则最强攻击会是：

> D² 赢的是弱 baseline 或额外 compute，而不是特定机制。

### 4. 成本口径需要更硬

材料提到 reasoning tier 是 one batched forward pass，所以 wall-clock 接近 `1 + f` 而不是 `3x`。这个说法工程上合理，但论文里必须同时报告：

- model calls。
- generated tokens。
- total decoded tokens。
- prefill tokens。
- GPU batch latency。
- GPU FLOPs 近似。
- dollar cost。
- wall-clock。

否则 reviewer 会认为成本账本选择性有利。

### 5. Planning bottleneck 的 causal ladder 需要重做

材料中 intervention ladder 显示 knowledge-only fix rate 低，full strategy fix rate 高，因此推断 planning / strategy 是主瓶颈。这个方向合理，但需要防止干预泄漏。

下一版应区分：

- formula hint。
- problem decomposition skeleton。
- operator sequence。
- final answer visible。
- explanation conditioned on gold answer。

如果某些 intervention 看到 gold answer，就不能用于证明“只差 planning”。

## 应该怎样改写研究主张

不建议：

> Memory-augmented recursive decomposition agents 已经被证明有效。

建议：

> D² 表明：结构化分解多样性可产生低成本难度信号；基于分歧熵的自适应计算分配和 trace-aware arbitration，在小模型数学推理上形成显著收益。下一步需要分别检验 memory、递归子问题图和强 agentic baselines 下的可迁移性。

这更诚实，也更能防御。

## 最值得保留的术语

- `D² / Decomposing Decomposition`：好，能概括“分解策略本身也被分解”。
- `semantic entropy routing`：好，是当前最有辨识度的机制。
- `trace-aware arbitration`：建议显式命名，因为它是 v6 中 arbiter 的真实增量。
- `verified subproblem memory`：建议作为下一阶段 memory 的强版本。

## 最该避免的术语风险

- `memory-augmented`：当前证据不足，容易被攻击。
- `recursive decomposition`：如果没有 subproblem tree/DAG 和递归展开证据，容易被 plan-execute 吸收。
- `planning bottleneck`：需要更严格 causal intervention 后再强写。

