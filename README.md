---
type: index
status: active
tags:
  - recursive-decomposition
  - memory
  - agent
---

# 递归分解与 Memory

> [!summary] 本页定位
> 这条研究线与 `控制反馈 / Token = Instruction` 并列。控制反馈线从 RAM/RASP、指令集、Load/Store 出发；本线从递归分解、lambda 演算、函数组合、计划执行和 memory 出发，关注模型生成的中间对象能否成为可复用、可验证、可组合、可递归调用的子问题结构。

## 文档结构

这条线现在按当前状态、审视、横向对标和未来候选四类维护：

- **当前**：[[current-status|当前状态：D² / Phase 1]]。现状、结果、方法、证据强弱、实验协议、当前攻击面。
- **当前审视**：[[code-review-recursive-reasoning-agents|recursive-reasoning-agents 代码审视]]。对收到的代码仓库进行逐项审视，区分代码内可复核证据与报告材料结论。
- **横向对标**：[[mechanism-landscape|对标机制谱系：递归分解与 Memory]]。CoT、分解、搜索、反思、Agent、memory、RLM、HRM/TRM、post-training 等机制谱系。
- **未来**：[[future-scenarios|未来研究候选场景]]。Lean、Kernel、代码 / 算法、SMT 等候选场景与推进计划。
- **未来参考**：[[future-lean-landscape|Lean 方向详尽调研]]。Lean 生态、强基线、benchmark、剩余切口和实验建议。
- **未来参考**：[[future-kernel-landscape|Kernel 性能优化工作谱系]]。Kernel 方向的强基线、已有吸收、剩余切口和参考链接。
- **未来参考**：[[future-small-model-landscape|小模型研究谱系调研]]。小模型的数据、蒸馏、后训练、领域专精、部署和系统角色。

## 一页版结论

Phase 1 材料里最强的成果不是笼统的 `memory-augmented recursive decomposition`，而是：

> 结构化分解多样性产生低成本难度信号；用分歧熵做自适应计算分配，能在小模型上提升推理表现。

也就是说，当前 v6 / D² 最可守的核心是：

- `diverse decomposition`：三种结构化分解风格产生错误去相关。
- `semantic entropy routing`：答案分歧本身成为零额外 LLM call 的难度信号。
- `trace-aware arbitration`：高分歧样本把失败 traces 交给 arbiter 纠偏。

递归分解和 memory 都是自然方向，但当前证据强度较弱，需要单独做消融。

未来主线不应直接从 D² 跳到“memory 已证明有效”，而应把问题收缩为：

> 系统能否把解决过程中的局部中间对象变成可验证、可复用、可组合、可检索、可更新、可局部纠偏的 `verified subproblem memory`。

当前最清楚的候选场景是 Lean / 形式化证明；Kernel 优化是工程价值更强但强基线压力也更大的场景；普通代码 / 算法任务适合作为 sanity check 或数据工厂，除非有强 verifier 和 family-heldout 设计。小模型不是同一层级的任务场景，而是横向实验载体和系统 worker 形态，见 [[future-small-model-landscape|小模型研究谱系调研]]。

## 与控制反馈线的关系

两条线都从 `Token` 不只是普通 word 的直觉出发，但关注点不同。

| 研究线 | 理论直觉 | 现实问题 | 当前最小切口 |
| --- | --- | --- | --- |
| 控制反馈 | RAM/RASP、Load/Store、状态读写 | 模型能否主动控制局部反馈信源 | A: 显式状态语义；B: 局部状态访问 |
| 递归分解与 memory | lambda 演算、函数组合、递归展开 | 模型能否生成可调用、可验证、可复用的子问题结构 | D²: 分解多样性与分歧熵路由 |

这条线不应直接声称“lambda 演算优于 RAM/RASP”。更稳的说法是：

> 类 RAM/RASP 路线强调状态访问；类 lambda / functional 路线强调抽象、应用、替换、组合和递归。二者都与可计算性有关，但对应的 AI 工作方式、训练对象和实验指标不同。

## 当前最小可输命题

第一命题：

> 在同一基础模型、同等或可核算计算预算下，结构化分解多样性产生的分歧熵，能否比固定 self-consistency、plan-execute、ReAct、Tree-of-Thought 类基线更好地分配推理计算，并提升 cost-normalized accuracy。

第二命题：

> 在高分歧或失败样本上，trace memory / verified subproblem memory 是否比 answer-only voting、plain re-solving、普通 context replay 更能提升局部纠偏成功率和未来任务复用率。

第三命题：

> 将问题表示为可递归展开的 typed subproblem graph，并只在高不确定子节点继续展开，是否比固定深度 plan-execute 或 flat multi-agent voting 有更好的 cost-quality Pareto。

横向对标见 [[mechanism-landscape|对标机制谱系：递归分解与 Memory]]。尤其需要区分：

- D² 当前更接近 `structured ensemble + adaptive compute + trace-aware arbitration`。
- RLM 是外部环境化上下文上的递归 self-call 强基线。
- HRM / TRM 是模型内部 latent recursion，不是显式 memory 或 verified subproblem memory。

## 当前建议

短期不要把研究线命名为“memory 已经证明有效”。更合适的主线是：

> D² / Decomposing Decomposition: 用结构化分解多样性获得难度信号，并用 trace-aware arbitration 做自适应纠偏。

Memory 暂时作为第二层机制：

- 存什么：失败 trace、verified subproblem、子问题依赖、修复策略。
- 怎么用：给 arbiter、给后续相似任务、给继续训练。
- 如何证明：通过 answer-only / trace-only / verified-memory / unverified-memory 对照。

如果要把 memory 提升为真正主线，一个更硬的候选切口是 Lean verified lemma memory：利用 Lean proof checker 解决 verification，把问题收缩为“能否自动生成、证明、索引并复用新的中间 lemma”。详见 [[future-scenarios|未来研究候选场景]] 和 [[future-lean-landscape|Lean 方向详尽调研]]。

如果不用 Lean，候选方向应优先选择程序验证、SMT / rewrite rule memory、算法合成等仍有局部验证对象的任务；普通代码修复更适合作为工程 sanity check。

GPU / NPU kernel 优化是一个更工程化的非 Lean 分支：正确性和性能都可验证，但必须对标 autotune、compiler search、Agent+Skills 和 evolutionary coding agents。详见 [[future-kernel-landscape|Kernel 性能优化工作谱系]]。
