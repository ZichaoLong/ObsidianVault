---
type: theory-challenges
status: active
tags:
  - control-feedback
  - theory
  - challenge
  - defense
---

# 控制反馈：理论与挑战

这份文档保存当前主线背后的理论支撑、现实对手和主要攻击面。它不是执行入口；执行入口见 [[10-control-feedback-token-instruction/current-mainline|当前主线]] 与 [[10-control-feedback-token-instruction/experiment-protocol|实验协议]]。

## 理论层级

当前理论内容分三层。

| 层级 | 作用 | 当前位置 |
| --- | --- | --- |
| 信仰牵引 | 解释为什么 `Token = Instruction` 值得想 | 历史动机、RAM/RASP、write-once、time scaling |
| 机制支撑 | 解释 A/B 为什么不是随意拆分 | [instruction 可训练性](<experiment-protocol.md#A 分支：显式状态语义与训练可行性>)、局部状态更新闭包、全局重解释 |
| 裁决层 | 判断现实价值是否站住 | 强基线、[成本账本](<experiment-protocol.md#成本账本>)、[A+B 交互](<experiment-protocol.md#A+B 交互指标>)、任务迁移 |

历史理论动机不能直接证明今天的 `Load/Store` 应成为一等公民，但保留了重要直觉：

> 复杂任务的推进，本质上是有限状态下的连续决策、状态管理与外界交互。

## 历史动机留下的三个问题

历史动机最后沉淀出三个问题。

第一，instruction 怎么训练？

- word token 的训练数据天然丰富。
- instruction token 若依赖探索，会面对低效 RL 攻击。
- 这要求 instruction 事件可回放、可监督、可归因、可构造反事实。
- 这支撑 A 分支。

第二，反馈信源怎么选择？

- AI 不应只被动 append。
- 系统应能主动选择观察什么、读取什么、修改什么、验证什么。
- 这支撑 B 分支。

第三，什么控制原语值得稳定下来？

- 不是所有 tool call 都应进入底层词表。
- 也不是 `Load/Store` 名称天然正确。
- 只有在训练、成本、纠偏和生态压力下稳定下来的事件，才有资格成为候选控制原语语言。

## 对标机制谱系

当前路线真正的对手不是某一个 agent，而是当前最强 `LLM + Agent + Tools` 已吸收的机制族。

主要对手包括：

- ReAct：交替推理与行动。
- Plan-Then-Execute：先规划，再执行。
- Reflection / Self-Correction：失败后反思再修。
- Search / Deliberate Inference：多分支探索。
- Program / Tool Delegation：外包给程序或工具。
- Recursive Context Management：递归管理上下文。
- Skill / Memory Accumulation：技能与经验沉淀。
- Recursive Decomposition：递归分解与问题分解。

这些机制已经能部分模拟 `Load/Store`：

- 调用工具。
- 读写文件。
- 使用数据库。
- 使用 regex、SQL、LSP、索引。
- compact、summarize、重新规划。
- 短上下文循环中做局部修复。

因此当前问题不是“能不能模拟”，而是：

> 这种模拟是否代价过高、轨迹过乱、错误边界过粗、训练信号过弱、局部纠偏不稳定？

## 局部状态更新闭包

局部状态更新闭包仍有价值，但它不再是唯一主线。

当前位置：

> 它是 B 分支和效率桥的理论支撑，解释为什么局部访问与局部修复可能是自然机制，而不是单纯工程偏好。

### 直观问题

> 对某类任务，求解与纠错是否可以主要通过有限组局部状态更新原语完成，而不必频繁退回全局重解释？

### 最小对象

状态空间 `S`：

- 某个工作区。
- 某个结构化对象。
- 某个可被局部读写的中间表示。

局部更新原语 `U`：

```text
ui : S -> S
```

直观要求：

- `ui` 只改动状态的有限局部部分。
- 其余大部分状态保持不变。

任务空间 `T`：

- 初始状态 `s0(tau)`。
- 目标条件 `Goal(tau, s)`。

全局重解释算子 `G`：

> 当系统不足以仅凭当前局部状态对象继续推进时，触发一次对更大范围任务状态的重新组织、重新摘要、重新检索、重新规划或重新解释。

`G` 不是：

- 是否重新 prefill。
- 是否重算 KV cache。
- 是否重跑模型。

`G` 是工作方式层概念：

- 下一步是否重新依赖更大范围语义理解。

### 当前缺口

局部状态更新闭包还必须补：

- 对“局部性”的任务内定义。
- 对 `G` 的行为判据。
- “近似闭包”的容许边界。
- 至少一个现实任务族到 `S/U/G` 的映射。

不能先追求一般定义，应 task-first。

## 确定性层与智能层

纯确定性路线不够。

- 它可能只是算法复杂度或抽象状态机。
- 即使形式上成立，也未必对应现实 LLM/Agent 工作方式。

纯智能实验路线也不够。

- 它可能只是 prompt、tooling、agent engineering。
- 没有钉住机制对象。

正确结构是：

- 确定性层负责变量隔离和机制对象生成。
- 智能层负责验证机制对象是否能被现实预测型控制系统承载。

这也是为什么实验先从强结构任务开始，但不能永远停在强结构任务。

## Test-Time 状态层次

test-time 状态至少有三层：

- `token / context` 层。
- 中间状态系统层，包括 KV cache、RNN state、node memory、workspace。
- 参数层，即 test-time 更新后的权重。

当前阶段先冻结参数。

原因：

- 参数更新变量过多。
- 工程复杂且难复现。
- 容易掩盖显式状态语义与局部访问本身的作用。

长期可以继续问：

- session adapter 是否承载事件压缩。
- 临时 LoRA 是否吸收局部修复策略。
- 参数层是否减少全局重解释。

但这不是第一击。

## 主要攻击面

### 攻击 1：A 的低阶部分已被 Agent 工程吸收

现代 Agent + Tools 已经在很大程度上吸收了 A 的低阶收益，尤其是在 frontier / provider-level / serious agent runtime 中。

| 好处 | 当前 Agent + Tools 状态 | 边界 |
| --- | --- | --- |
| 稳定语法 / typed arguments | 大体已有 | JSON schema、strict tool use、MCP schema 已是主流方向，但不是所有实际系统都做到。 |
| trace / logging | 大体已有 | tracing 能记录 tool calls、LLM generations、handoffs、guardrails 等。 |
| 可监督轨迹 | 部分已有 | traces / eval datasets 可支持监督，但通常不是默认事件级状态监督。 |
| 可回放状态变化 | 部分已有 | checkpoint / replay / time travel 依赖框架设计，且 replay 不自动等于 semantic replay。 |
| 可构造反事实样本 | 较弱 | 可人工或程序构造，但通常不是一等机制。 |
| 可训练纠偏策略 | 较弱到部分已有 | trace/eval 可帮助改 prompt、orchestration、工具选择；事件级错误到局部修复再继续训练尚未成为通用闭环。 |

因此，A 不能再主张“第一次让工具调用结构化”。A 剩下的特殊点必须收缩为：

> typed tool traces 能否升级成 decision-active explicit state semantics，使事件不只是工具调用记录，而是可回放、可诊断、可局部修复、可构造反事实、可用于继续训练的状态转移对象。

防守边界：

- `tools vs typed tools` 只作为 Stage 0 sanity check。
- A 的核心对照必须是 `typed tools + trace/logging/transaction` vs decision-active explicit state semantics。
- 如果强 typed tools baseline 实现了同等显式状态语义，A 已被 baseline 吸收。

### 攻击 2：A 只是 schema engineering

A 的显式状态事件可能只是把 typed tools 包装成更规整的 schema。

若 strong typed tools + logging + transaction 达到同等训练、归因和纠偏效果，A 没有独立增量。

防守边界：

- A 必须证明事件进入后续决策。
- A 必须证明轨迹更可训练，而不是只更好看。
- A 必须证明局部修复和反事实样本构造更稳定。

### 攻击 3：A 的训练收益来自低熵动作空间

如果 action vocabulary 更短、更固定，NLL 下降可能只是格式收益。

防守边界：

- NLL 只能作为辅助指标。
- 主指标应是 repair success、sample efficiency、同类错误复发率、counterfactual validity。
- 必须控制 action entropy、schema 信息和输出格式复杂度。

### 攻击 4：B 只是 active retrieval

B 可能退化成 retrieval、memory system 或 POMDP。

防守边界：

- 固定 resolver，比 access interface。
- 固定 access interface，比 resolver。
- 预先定义 selector/resolver/reader。
- 若只证明检索有用，不算控制反馈主线胜利。

### 攻击 5：meaningful address 偷渡语义

`users[17].transactions` 已经携带大量语义，模型可能不是学会局部访问，而是吃到了地址标签。

防守边界：

- 做 meaningful / typed / hierarchical / opaque / learned address 消融。
- 若只在 meaningful address 下有效，结论必须收缩。

### 攻击 6：workspace 粒度由人工设计贡献全部收益

如果 cell/schema/scope 全由研究者手工定制，实验可能只是 DSL/task engineering。

防守边界：

- 记录人工设计成本。
- 做 [[10-control-feedback-token-instruction/experiment-protocol#Workspace 粒度消融|cell 粒度消融]]。
- 后续引入模型辅助或自动粒度生成。

### 攻击 7：scaffold 偷走全部困难

薄接口可能只是把复杂性转嫁给 runtime。

防守边界：

- 计入 [[10-control-feedback-token-instruction/experiment-protocol#成本账本|setup、runtime、人工成本]]。
- 区分 model-only proposal quality、runtime-corrected success、rollback-assisted success。
- 如果胜利来自 validator 自动拒错，不能说模型学会了状态管理。

### 攻击 8：任务选择偏置

JSON、AST、ledger、dependency graph 天然适合状态访问接口。

防守边界：

- 第一阶段允许用强结构任务切变量。
- 第一阶段结论必须收缩。
- 第二阶段必须进入半结构任务。

### 攻击 9：A+B 无交互

A 和 B 可能都是有用小技巧，但组合没有统一原语意义。

防守边界：

- 预注册 [[10-control-feedback-token-instruction/experiment-protocol#A+B 交互指标|交互指标]]。
- 强合流要求 `Y11` 优于 `Y10/Y01`，且 `Interaction > delta`。
- `Y11` 最大但 `Interaction <= 0` 只是弱合流，说明组合工程上有用，但不能强称统一低层原语站住。
- `Y11` 单指标不是最大但 Pareto 非支配时，只能算 Pareto 弱合流。
- 若 `Y11` 被 `Y10` 或 `Y01` 支配，则组合接口失败，但 A 或 B 单分支仍可能保留。

### 攻击 10：历史动机与实验指标之间仍有裂缝

RAM/RASP、write-once、time scaling 不能直接推出当前实验指标。

防守边界：

- 历史动机只提供“为什么值得想”。
- A 提供“instruction 是否可训练”的第一桥。
- B 提供“反馈信源是否可主动控制”的第二桥。
- A+B 交互和成本账本才提供“是否值得继续做”的裁决。

### 攻击 11：Agent+Tools 可以无限吸收

现有 Agent+Tools 可以吸收 typed schema、logging、transaction、retrieval、indexing，甚至局部访问形态。

防守边界：

- 不证明 Agent+Tools 不能做。
- 只检验某套状态访问接口是否在训练、纠偏、成本上形成更稳定非支配点。
- 若被强基线吸收，说明方向可能成为工程实践，而不是独立底层原语。

## 结果解释表

| 结果 | 解释 |
| --- | --- |
| A 成功，B 失败 | 更像 agent trace / schema engineering。 |
| B 成功，A 失败 | 更像 active retrieval / memory system。 |
| A 成功，B 成功，`Y11` 最大但无正交互 | 弱合流，工程组合有用，但统一原语未站住。 |
| `Y11` Pareto 非支配但主指标不最大 | Pareto 弱合流，可以继续工程推进。 |
| `Y11` 被 `Y10` 或 `Y01` 支配 | A+B 组合失败，单分支仍可保留。 |
| A 和 B 都只赢弱基线 | 不能说明独立增量。 |
| A 和 B 在强基线下都失败 | 当前形态应放弃或大幅转向。 |
| A+B 在强基线和成本账本下形成 `Interaction > delta` | 可以重新讨论统一状态访问接口或候选低层原语。 |

这张表的目的不是悲观，而是避免任何结果都能解释成胜利。

## 当前 Defense

当前 defense 不是“控制反馈已经成立”，而是：

- 历史动机足够严肃，值得提出问题。
- A 把 `Token = Instruction` 最大训练裂缝压成可实验问题，但必须承认其低阶部分已被现代 Agent 工程部分吸收。
- B 把“自主控制反馈信源”压成局部状态访问与地址生成问题。
- A/B 2x2 让结果可分解、可输、可降级。
- 强基线与成本账本避免自我奖励。

如果 A/B 都站不住，就不应继续扩张叙事。

如果 A 站住但 B 不站住，仍可保留为 instruction trace / data flywheel 工程方向。

如果 B 站住但 A 不站住，仍可保留为 active retrieval / memory system 方向。

只有 A+B 在强基线下形成交互收益，才值得重新讨论 `Load/Store` 或更底层控制原语语言。
