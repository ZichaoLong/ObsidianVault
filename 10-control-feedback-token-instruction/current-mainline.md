---
type: current-mainline
status: active
tags:
  - control-feedback
  - token-instruction
  - current-mainline
---

# 控制反馈：当前主线

当前最可守的表述：

> 历史动机提供类似 `Next Token` 的信仰牵引；A 分支检验 instruction token 是否能形成可训练的数据飞轮；B 分支检验模型是否能主动控制局部反馈信源；`Token = Instruction` 是在 A/B 压力下演化出的候选控制事件语言。`Load/Store` 不是预设答案，而是二者合流后才有资格成立的候选低层控制原语。

## 一页版

控制反馈线现在不直接证明：

- `Load/Store` 已经优于最强 `LLM + Agent + Tools`。
- `Token = Instruction` 已经是基础模型接口。
- 现有 agent 无法模拟状态访问。
- 某种 TapeWalker 形态必然胜出。

当前先拆成两个正交分支：

| 分支 | 研究对象 | 主要价值 | 强基线 |
| --- | --- | --- | --- |
| [A：显式状态语义](<experiment-protocol.md#A 分支：显式状态语义与训练可行性>) | instruction 事件是否成为稳定运行时对象 | 可训练、可回放、可归因、可局部修复、可继续训练 | typed tools + logging + trace id + transaction |
| [B：局部状态访问](<experiment-protocol.md#B 分支：局部状态访问与地址生成>) | 模型是否主动控制隐藏全局状态中的局部反馈信源 | 细粒度控制反馈、地址生成、访问成本、长度泛化 | BM25 / vector / SQL / LSP / learned retriever / resolver |

二者合流时才接近完整主张：

> 统一状态访问接口是否在强工具、强检索、强日志、强事务基线下，仍形成不可被吸收的学习、纠偏或成本优势。

## 历史动机的位置

[[10-control-feedback-token-instruction/historical-motivation|历史动机]] 的核心作用不是证明现实系统结论，而是提供方向牵引。

它类似 `Next Token` 在 GPT 路线早期的作用：

- 不是严格证明最优。
- 不是排除所有竞争路线。
- 是一个能组织研究直觉、实验设计和工程选择的基础信念。

历史动机中最重要的判断是：

> 智能系统不应只被动 append word token，而应能生成控制指令，并主动选择下一步反馈信源。

这句话后来分裂成两个问题。

第一，instruction 怎么训练？

- word token 的数据天然存在。
- instruction token 若只靠低效探索或大规模强化学习，会立刻遭遇可行性攻击。
- 因而必须先问：instruction 事件是否有稳定语义、可监督轨迹、可回放状态变化、可构造反事实样本、可训练纠偏策略。

这就是 [[10-control-feedback-token-instruction/experiment-protocol#A 分支：显式状态语义与训练可行性|A 分支]]。

第二，反馈信源怎么自主选择？

- 历史动机里说的“自主控制反馈信源”，更具体地说，是生成地址、选择观察对象、控制局部读写范围。
- 它不是简单工具调用，而是模型是否能在隐藏的大状态中主动决定看哪里、改哪里、验证哪里。

这就是 [[10-control-feedback-token-instruction/experiment-protocol#B 分支：局部状态访问与地址生成|B 分支]]。

因此，A 不是偏离历史动机的工程化妥协。它填补的是 `Token = Instruction` 最先会被攻击的训练裂缝：

> 如果 instruction token 无法形成可训练数据飞轮，那么 `Token = Instruction` 无法从口号进入技术路线。

但 A 也不是历史动机的全部。B 才更直接承接“自主控制反馈信源 / address generation / 细粒度闭环”这条深层问题意识。

## Token = Instruction 的当前含义

当前不把 `Token = Instruction` 理解成推翻 `Next Token`。

更稳的理解是：

- 训练目标可以仍是 next-token prediction。
- 变化发生在 token 语义上。
- token 不只表示 word/data，也可以表示 control event。
- instruction token 必须有稳定执行语义，否则只是自然语言工具调用的重命名。

候选 instruction 事件包括：

- `address`
- `read`
- `write`
- `patch`
- `verify`
- `commit`
- `rollback`
- `diagnose`
- `replay`

这些不是预设最终 ISA，而是第一批可研究控制事件。

如果 A 失败，这些事件无法形成训练对象，`Token = Instruction` 会退化成协议命名。

如果 B 失败，这些事件即使可训练，也可能只是更规整的 agent trace，而不是自主控制反馈信源。

如果 A+B 无交互收益，`Load/Store` 仍不能成为统一低层原语。

## A 分支：显式状态语义

A 分支的问题是：

> instruction 事件是否能成为稳定、可回放、可归因、可纠偏、可训练的运行时对象？

它首先回答训练可行性，而不是直接回答能力上限。

### 为什么 A 是早期信心抓手

word token 的优势之一是数据飞轮天然存在：

- 语料丰富。
- 标注不需要人工定义动作语义。
- next-token 目标简单。
- scaling 信号清楚。

instruction token 的最大风险是相反的：

- 动作空间由研究者设计。
- 数据不像自然语言一样自然充足。
- 低效探索会让 RL 成本爆炸。
- 轨迹若不可回放，训练样本质量会很差。
- 错误若不可归因，负样本会污染整段轨迹。

A 分支的价值是把 instruction 训练问题压成一个较硬的问题：

> 显式状态事件能否把 agent 的失败转化为可回放、可局部修复、可继续训练的数据飞轮？

但 A 的低阶部分已经被现代 Agent 工程部分吸收。typed tool calling、schema、trace、logging、checkpoint 或 replay 已经在 frontier / provider-level / serious agent runtime 中成为常见方向。因此 A 不能把“工具调用结构化”当作主贡献。

A 剩下的特殊点是：

> typed tool traces 能否升级成 decision-active explicit state semantics，使事件不只是工具调用记录，而是可回放、可诊断、可局部修复、可构造反事实、可用于继续训练的状态转移对象。

如果能，A 提供早期信心：

- imitation learning 数据更干净。
- error attribution 标签更稳定。
- repair policy 样本更容易构造。
- 反事实轨迹更容易生成。
- 继续训练可以利用局部事件，而不必只用整段成功/失败。

如果不能，`Token = Instruction` 的训练路径会非常脆。

### A 不要求局部访问

A 不要求模型每一步只能看局部状态。模型可以看到完整 JSON、大块代码或较长上下文。

A 只问：

- 状态对象是否明确。
- 事件生命周期是否明确。
- 状态变化是否可回放。
- 事件是否进入后续决策。
- 错误是否能定位到事件。
- 纠偏是否能基于事件局部发生。

因此 A 的强对手不是普通 tools，而是 [[10-control-feedback-token-instruction/experiment-protocol#A 的强基线|强 typed tools 基线]]：

> `standard tools + typed schema + trace id + logging + transaction`

`tools vs typed tools` 应作为 [[10-control-feedback-token-instruction/experiment-protocol#总体设计|Stage 0 sanity check]]，用于校准任务和实现，而不是 A 的主贡献。

如果 A 只赢弱工具，不赢这个强基线，不能说明独立增量。

## B 分支：局部状态访问

B 分支的问题是：

> 模型是否能在隐藏全局状态中，通过受约束寻址主动选择局部反馈信源，并因此改善访问成本、长度泛化和局部修复范围？

B 更直接承接历史动机中的：

- 快速、自主控制反馈信源。
- address generation。
- 不把整个 context 当唯一状态。
- 分而治之与小颗粒闭环。

B 的关键不是工具支持局部读取，而是信息边界：

- global state 默认隐藏。
- observation budget 固定。
- 模型必须主动生成 query / intent / address / selector。
- runtime 只返回受限 cell / chunk / object。
- 任务推进依赖多轮局部访问。

B 的强对手不是普通工具，而是 [[10-control-feedback-token-instruction/experiment-protocol#B 的强基线|强检索与索引系统]]：

- BM25。
- vector search。
- SQL / index。
- tree-sitter / LSP。
- learned retriever。
- 任务专用 resolver。

如果 B 只证明“主动检索有用”，它应降格为 retrieval / memory system。

## A 与 B 的 2x2

A 与 B 是两个正交变量。

| 局部访问 / 显式语义 | 无显式状态语义 | 有显式状态语义 |
| --- | --- | --- |
| 无局部访问 | typed tools 强基线 | A：显式状态语义 |
| 有局部访问 | retrieval/index 强基线 | A+B：完整候选接口 |

这个设计用于切开三种贡献：

- A 的训练、回放、归因、纠偏贡献。
- B 的寻址、局部访问、长度泛化、成本贡献。
- A+B 的交互贡献。

结果解释：

| 结果 | 解释 |
| --- | --- |
| A 成功，B 失败 | 更像 agent trace / schema engineering。 |
| B 成功，A 失败 | 更像 active retrieval / memory system。 |
| A、B 都成功，`Y11` 最大但无正交互 | 弱合流，工程组合有用，统一原语未站住。 |
| `Y11` Pareto 非支配但主指标不最大 | Pareto 弱合流，可以继续工程推进。 |
| `Y11` 被 `Y10` 或 `Y01` 支配 | A+B 组合失败，单分支仍可保留。 |
| A+B 在强基线和 [成本账本](<experiment-protocol.md#成本账本>) 下形成 Pareto 优势 | 可以继续推进统一状态访问接口。 |

## Load Store 的降级位置

`Load/Store` 当前不应写成答案，而应写成候选低层控制原语。

它要重新上升，至少需要：

- A 在强 typed-tools/logging/transaction 基线上仍改善训练、回放、归因或纠偏。
- B 在强 retrieval/indexing 基线上仍改善访问成本、长度泛化或局部修复范围。
- A+B 的组合在预注册主指标上产生 `Interaction > delta`，而不是两个可独立吸收的小技巧。
- 计入 [[10-control-feedback-token-instruction/experiment-protocol#Workspace 粒度消融|workspace 粒度]]、resolver、runtime/scaffold 成本后仍成立。

这与计算机 ISA 类比更一致：没有人先验证明某个 ISA 最优，真正筛选来自训练、工程、成本、生态和任务分布压力。

## 当前最小可输命题

当前最小可输命题：

> 在同等模型能力、同等信息预算、预先定义 [[10-control-feedback-token-instruction/experiment-protocol#总体设计|A/B 阈值]] 并计入 [[10-control-feedback-token-instruction/experiment-protocol#成本账本|scaffold 成本]] 的前提下，显式状态语义与局部状态访问分别、以及组合后，是否相对强 typed tools/logging/transaction 和强 retrieval/indexing 基线，在训练、归因、纠偏或成本曲线上形成不可被 baseline、resolver、workspace 粒度或 runtime 解释掉的增量？

它输掉时：

- A 被强 typed tools 吸收，则显式状态语义不是独立抓手。
- B 被强 retrieval/indexing 吸收，则局部状态访问不是独立抓手。
- A+B 只有弱合流，则可继续工程推进，但 `Load/Store` 不是统一低层原语。
- scaffold 成本吞掉收益，则薄界面是假象。
- 轨迹不可训练，则 `Token = Instruction` 缺少数据飞轮。

它站住时：

- instruction token 有了比低效 RL 更可信的训练入口。
- 状态访问接口不只是工具别名。
- 事件语义和局部访问不是单独小技巧。
- 后续才值得讨论更底层模型接口、训练接口或神经架构承载。

## 当前推进计划

第一阶段：重写实验定义。

- 用协议中立的 semantic transition 写底层专家轨迹。
- 明确 A/B 操作性阈值。
- 明确 [[10-control-feedback-token-instruction/experiment-protocol#Selector Resolver Reader|selector / resolver / reader]] 分解。
- 明确 [[10-control-feedback-token-instruction/experiment-protocol#Workspace 粒度消融|workspace 粒度变量]]。
- 建立 [[10-control-feedback-token-instruction/experiment-protocol#成本账本|scaffold 成本账本]]。

第二阶段：做 Stage 0 sanity check。

- 比较 freeform tools 与 typed tools。
- 校准任务和实现。
- 不把 typed tools 胜出当作主贡献。

第三阶段：先做 A 的训练可行性实验。

- 任务用 JSON / AST / ledger / dependency graph。
- 比较强 typed tools 与显式状态事件。
- 先看轨迹是否更适合 imitation、归因、纠偏和反事实训练。
- 不把最终任务成功率作为唯一主指标。

第四阶段：做 B 的局部访问实验。

- 固定 resolver，比访问接口。
- 固定访问接口，比 resolver。
- 检验 address generation、局部读取成本、长度泛化、全局回退频率。

第五阶段：做 A+B 2x2。

- 检验是弱合流、Pareto 弱合流，还是 [[10-control-feedback-token-instruction/experiment-protocol#A+B 交互指标|强合流]]。
- 预注册主指标和 Pareto 裁决规则。
- 计入 setup、runtime、人工 schema、resolver 构造成本。

第六阶段：进入半结构任务。

- 长文档局部修订。
- 代码仓局部修复。
- 多文件一致性维护。
- 研究笔记状态更新。

只有前四阶段出现稳定收益，第五阶段才有意义。

## 阅读分流

- 实验定义和具体指标见 [[10-control-feedback-token-instruction/experiment-protocol|实验协议]]。
- 理论支撑、对标机制和攻击面见 [[10-control-feedback-token-instruction/theory-and-challenges|理论与挑战]]。
- 历史来时路见 [[10-control-feedback-token-instruction/historical-motivation|历史动机]]。
