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
> 这条研究线与 [[10-control-feedback-token-instruction/README|控制反馈 / Token = Instruction]] 并列。控制反馈线从 RAM/RASP、指令集、Load/Store 出发；本线从递归分解、lambda 演算、函数组合、计划执行和 memory 出发，关注模型生成的中间对象能否成为可复用、可验证、可组合、可递归调用的子问题结构。

## 一页版结论

Phase 1 材料里最强的成果不是笼统的 `memory-augmented recursive decomposition`，而是：

> 结构化分解多样性产生低成本难度信号；用分歧熵做自适应计算分配，能在小模型上提升推理表现。

也就是说，当前 v6 / D² 最可守的核心是：

- `diverse decomposition`：三种结构化分解风格产生错误去相关。
- `semantic entropy routing`：答案分歧本身成为零额外 LLM call 的难度信号。
- `trace-aware arbitration`：高分歧样本把失败 traces 交给 arbiter 纠偏。

递归分解和 memory 都是自然方向，但当前证据强度较弱，需要单独做消融。

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

## 阅读路径

- 当前收敛判断：[[11-recursive-decomposition-memory/current-mainline|当前主线]]
- Phase 1 材料审视：[[11-recursive-decomposition-memory/phase1-review|Phase 1 审视]]
- 实验怎么做：[[11-recursive-decomposition-memory/experiment-protocol|实验协议]]
- 理论定位与攻击面：[[11-recursive-decomposition-memory/theory-and-challenges|理论与挑战]]

## 当前建议

短期不要把研究线命名为“memory 已经证明有效”。更合适的主线是：

> D² / Decomposing Decomposition: 用结构化分解多样性获得难度信号，并用 trace-aware arbitration 做自适应纠偏。

Memory 暂时作为第二层机制：

- 存什么：失败 trace、verified subproblem、子问题依赖、修复策略。
- 怎么用：给 arbiter、给后续相似任务、给继续训练。
- 如何证明：通过 answer-only / trace-only / verified-memory / unverified-memory 对照。

