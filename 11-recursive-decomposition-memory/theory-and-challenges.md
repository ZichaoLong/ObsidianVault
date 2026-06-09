---
type: theory-challenges
status: active
tags:
  - recursive-decomposition
  - memory
  - theory
  - challenge
---

# 递归分解与 Memory：理论与挑战

这份文档保存理论定位、现实对手和主要攻击面。

## 理论定位

递归分解线的理论动机可以从 lambda 演算出发，但不能止步于类比。

### Lambda 演算的位置

lambda 演算与图灵机在可计算性上等价。它的核心对象包括：

- 函数抽象。
- 函数应用。
- 变量绑定。
- 替换。
- 递归。

现代相关形态包括：

- Lisp。
- ML / OCaml。
- Haskell。
- 函数式编程。
- 闭包。
- continuation。
- graph reduction。
- term rewriting。

但 lambda 演算本身不直接给出现代 AI 里的训练优势、推理成本优势或 memory 机制。它提供的是一种工作方式直觉：

> 复杂问题可以被表示为可组合、可调用、可替换、可递归展开的中间对象，而不是一次性线性文本。

### 与 RAM/RASP 路线的差异

| 路线 | 关注对象 | AI 映射 |
| --- | --- | --- |
| RAM/RASP | 地址、状态、读写、指令执行 | Load/Store、workspace、局部反馈 |
| Lambda / functional | 抽象、应用、组合、递归 | subproblem function、proof fragment、decomposition graph |

二者并不冲突。

- 控制反馈线问：下一步看哪里、改哪里、验证哪里。
- 递归分解线问：下一步调用哪个子问题、展开哪个节点、复用哪个证明片段。

## 现实对手

这条线不可回避的对手是现代 Agent decomposition 家族。

主要包括：

- Chain-of-Thought。
- Plan-and-Solve。
- Least-to-Most。
- Decomposed Prompting。
- ReAct。
- Reflexion。
- Self-Consistency。
- Tree-of-Thought。
- Graph-of-Thought。
- Multi-agent debate。
- AutoGPT-style planning。
- Hierarchical agents。
- Recursive Language Models / recursive reasoning。

因此不能主张：

> 我们第一次让模型做递归分解。

可守主张只能是：

> 某种结构化分解多样性、分歧熵路由、trace-aware arbitration 或 verified subproblem memory，在强对手下形成可核算的 cost-quality 增量。

## 主要攻击面

### 攻击 1：只是 self-consistency 的结构化版本

D² 同时运行三个 agents，可能只是 self-consistency / ensemble 的变体。

防守边界：

- 比 same prompt x3。
- 比 self-consistency k=3/5。
- 比 random prompt variants。
- 报告 error decorrelation。
- 报告 majority-correct 和 all-wrong rate。

如果 structural diversity 不稳定优于这些基线，应降级为 ensemble engineering。

### 攻击 2：只是多花 compute

Agent v6 成本高于单次 CoT。收益可能只是多跑几次。

防守边界：

- 统一成本账本。
- 同等 token budget 下比较。
- 同等 model call budget 下比较。
- 报告 cost-normalized accuracy。
- 比 fixed 5-agent majority。

如果同成本 self-consistency 或 5-agent majority 追平，D² 没有独立机制优势。

### 攻击 3：entropy routing 是事后解释

分歧熵与难度相关，不等于它能做有效路由。

防守边界：

- 与 random routing 比。
- 与 HCE routing 比。
- 与 oracle routing 上界比。
- 固定 arbitration fraction。
- 预注册 hard-case recall 和 false arbitration rate。

如果 entropy routing 不优于 random routing，路由主张失败。

### 攻击 4：arbiter 只是重新解题

Arbiter 可能没有真正使用 traces，只是又做了一次或两次解题。

防守边界：

- answer-only arbiter。
- no-trace re-solve。
- random trace。
- corrupted trace。
- verified trace。
- trace utilization analysis。

如果 answer-only 与 trace-aware 相同，trace memory 主张失败。

### 攻击 5：memory 只是污染或 retrieval

如果 memory 存了相似题和答案，收益可能只是查表。

防守边界：

- family split。
- parameter split。
- template-heldout。
- distractor memory。
- stale memory。
- 只允许 verified subproblem，不允许最终答案直接命中。

如果 memory 只在近邻模板上有效，应降级为 retrieval engineering。

### 攻击 6：递归分解不真实

当前 v6 更像 flat multi-agent ensemble，不是真正 recursive decomposition。

防守边界：

- 引入 typed subproblem graph。
- 子问题节点可验证。
- 高不确定节点继续展开。
- verified nodes 可缓存和复用。
- 局部失败可修复，不必全局重启。

如果没有这些结构，不应强称 recursive decomposition 已经成立。

### 攻击 7：baseline 弱

Plan-and-Solve、ReAct、Least-to-Most 等 baseline 在小模型上表现差，可能因为实现或 prompt 不够强。

防守边界：

- 使用公开强 prompt。
- 多轮调参预算相同。
- 记录每个 baseline 的最佳 prompt。
- 引入 external implementations 交叉验证。
- 增加 stronger agentic baselines。

### 攻击 8：benchmark 偏置

SynthMath-1K 可能天然适合结构化分解。

防守边界：

- 保留 SynthMath 作为第一阶段可控 benchmark。
- 增加 sorting、algorithm tracing、program synthesis、多文件代码修复。
- 增加 surface-form perturbation。
- 增加 family-heldout。

### 攻击 9：小模型特化

D² 可能只是 3B 小模型短板补丁，在 thinking models 或大模型上收益消失。

防守边界：

- 同一 agent framework 跑 Qwen2.5、Phi、Qwen thinking、DeepSeek-R1-distill 等。
- 对每个模型比较 bare model vs agent。
- 不再强行 suppress CoT。
- 报告 delta 随模型能力变化的曲线。

如果大模型上收益消失，应收缩为：

> 小模型推理增强和成本控制工程。

## 更好的理论问题

### 问题 1：结构化多样性是否降低错误相关性

形式化直觉：

> 对同一模型 `M`，不同 decomposition operator `d_i` 诱导不同错误集合 `E_i`。若 `E_i` 的相关性低于随机采样或同质 prompt 变体，则 ensemble 和 entropy routing 有结构性优势。

这比“递归分解有用”更可测。

### 问题 2：分歧是否是可用的不确定性估计

形式化直觉：

> 多个 structured solvers 的输出分布 `q(a|x)` 的 entropy `H(q)` 是否校准任务失败概率 `P(error|x)`，并能在固定追加计算预算下最大化收益。

这把 v6 的核心压成 calibration / routing 问题。

### 问题 3：trace 是否含有可纠偏信息

形式化直觉：

> 给定同样的题目和候选答案，失败 trace `T_i` 是否提供额外信息，使 arbiter 的纠偏概率高于 answer-only setting。

这把 trace memory 从“日志”变成可检验的信息变量。

### 问题 4：verified subproblem 是否可跨任务复用

形式化直觉：

> 若一个子问题节点 `s` 具有 verified input/output 和依赖边，则在同 family 但不同参数或表面词的任务中，检索并实例化 `s` 能否降低求解成本或错误率。

这才是 memory 的强版本。

## 当前 Defense

当前 defense 不是：

> 递归分解与 memory 已经成立。

而是：

- Phase 1 已经找到一个有证据的机制核心：结构化分解多样性和分歧熵路由。
- 这个机制与递归分解 / memory 有自然连接，但连接还需要实验补齐。
- 下一步不是扩张叙事，而是把 diversity、routing、arbitration、memory 分开做可输实验。
- 如果 memory 和 recursive DAG 失败，D² 仍可能作为 adaptive multi-agent reasoning 工程方向保留。
- 如果 memory 和 recursive DAG 成功，才有资格重新提升为“可复用子问题结构”的研究线。

