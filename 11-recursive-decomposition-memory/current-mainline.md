---
type: current-mainline
status: active
tags:
  - recursive-decomposition
  - memory
  - current-mainline
---

# 递归分解与 Memory：当前主线

当前最可守的表述：

> 递归分解与 memory 线不直接证明“模型需要像 lambda 演算一样工作”。当前先检验：结构化分解多样性能否产生稳定、低成本的难度信号；分歧熵能否驱动自适应计算分配；trace / verified subproblem memory 能否在高分歧和失败样本上提供独立纠偏收益。

## 历史动机的位置

这条线的理论动机来自与控制反馈线不同的计算观。

- 图灵机、RAM/RASP 更强调状态、寻址、读写、指令执行。
- lambda 演算更强调函数抽象、函数应用、变量绑定、替换、递归。
- 二者在可计算性上等价，但工作方式和成本直觉不同。
- 函数式编程、Lisp、ML、Haskell、闭包、continuation、graph reduction 等都可看作这一思想在工程或理论中的后续形态。

需要谨慎的是：lambda 演算早期主要回答可计算性与形式系统问题，并不天然给出现代 AI 里的计算复杂度、训练难度或数据飞轮优势。它更适合作为动机桥，而不是直接证据。

## 当前材料的真实核心

Phase 1 报告标题是 `Memory-Augmented Recursive-Decomposition Reasoning Agents`，但从证据看，当前真正站得住的是 v6 / D²：

> 三种结构化 decomposition styles 在同一模型上并行运行；它们的答案分歧形成 semantic entropy；entropy 决定 Direct、Majority、Arbitrate 三条路径；高分歧时 arbiter 读取失败 traces 后重解。

这可以拆成三层机制。

| 层 | 机制 | 当前证据 |
| --- | --- | --- |
| 多样性 | IPEV / Algebraic / Atomic 三种分解风格 | pairwise error Jaccard 约 0.53-0.55，说明错误有一定去相关 |
| 路由 | 答案分歧熵决定是否追加计算 | H=0、H≈0.637、H=log3 与准确率单调相关 |
| 纠偏 | arbiter 读取失败 traces 后重解 | v6 相对 v5 和多数基线有收益，但还需更多消融 |

Memory 当前不是最强证据点。材料里出现了：

- v1: networkx graph memory。
- v2: context envelope 和 reflection。
- v3: file workspaces、isolation、verified knowledge memory。
- v6: trace memory feeding arbiter agents。

这些说明 memory 是工程演进的一部分，但尚未单独证明 memory 本身是收益来源。

## 当前三个候选分支

### 分支 A：结构化分解多样性

问题：

> 固定同一基础模型时，预先设计的多种 decomposition styles 是否比随机采样、自一致性或同质 multi-agent 更能产生可利用的错误去相关？

它对标：

- self-consistency。
- same prompt repeated sampling。
- multi-agent debate。
- plan-execute。
- least-to-most。
- Tree-of-Thought。

它要证明的不是“多跑几次有用”，而是：

> 结构差异比采样差异更能产生低相关错误，从而提升 ensemble 和 routing 的价值。

### 分支 B：分歧熵路由

问题：

> 不额外调用 complexity estimator，仅利用多个分解策略的答案分布，能否得到足够好的难度信号，并据此自适应分配计算？

它当前是最强候选主线。

关键原因：

- v4 的 HCE complexity routing 需要额外 LLM call。
- v6 的 entropy routing 使用已有输出，额外成本低。
- 分歧本身包含失败模式信息，不只是一个标量。

### 分支 C：trace / subproblem memory

问题：

> 高分歧或失败样本中的 traces、verified subproblem、失败模式和修复策略，是否能作为 memory 改善当前纠偏和未来相似任务？

这是最接近“memory-augmented”的部分，但当前需要补实验。

Memory 不能只存：

- 最终答案。
- 原始全文 trace。
- 大段自然语言经验。

更应存：

- typed subproblem。
- verified intermediate result。
- failed branch。
- error type。
- correction pattern。
- dependency edge。

## 与 plan-execute 的关系

Plan-execute 是这条线不可回避的强对手，就像 Agent+Tools 是控制反馈线不可回避的强对手。

当前主张不能是：

> 我们第一次让模型分解问题。

因为这已经被 plan-execute、least-to-most、decomposed prompting、ReAct、Tree-of-Thought、multi-agent debate、Reflexion 等大量吸收。

可守主张应是：

> 不同 decomposition styles 的分歧可以作为难度估计和纠偏入口；trace-aware arbitration 和 verified subproblem memory 能否在强 agentic baseline 上形成 cost-quality 增量。

## 当前最小可输命题

主命题：

> 在同一基础模型、同等或可核算计算预算下，结构化分解多样性产生的分歧熵，能否比固定 self-consistency、plan-execute、ReAct、Tree-of-Thought 类基线更好地分配推理计算，并提升 cost-normalized accuracy。

次命题：

> 在高分歧或失败样本上，trace memory / verified subproblem memory 是否比 answer-only voting、plain re-solving、普通 context replay 更能提升局部纠偏成功率和未来任务复用率。

更长期命题：

> 将问题表示为可递归展开的 typed subproblem graph，并只在高不确定子节点继续展开，是否比固定深度 plan-execute 或 flat multi-agent voting 有更好的 cost-quality Pareto。

## 当前推进顺序

第一阶段：先把 D² 做实。

- 复现 v6 结果。
- 统一成本口径。
- 加强 agentic baselines。
- 做必要 ablation。

第二阶段：拆 trace-aware arbitration。

- answer-only arbiter。
- trace-aware arbiter。
- truncated trace。
- compressed trace。
- verified trace。
- corrupted trace。

第三阶段：引入真正 memory。

- verified subproblem memory。
- failure-pattern memory。
- family-split generalization。
- cross-task reuse。

第四阶段：再谈 typed recursive subproblem graph。

- 子问题节点有输入、输出、依赖、verifier。
- 高不确定节点继续展开。
- 低不确定节点缓存和复用。

## 当前防守边界

能说：

- D² 是一个有初步证据的自适应计算分配框架。
- 分歧熵是一个有证据的难度信号。
- trace-aware arbitration 是一个值得单独检验的纠偏机制。

不能说：

- memory 已经被证明是主要收益来源。
- 递归分解已经优于所有 plan-execute。
- lambda 演算路线已经得到实验验证。
- 当前结果已经证明了可复用子问题函数或长期 memory。

