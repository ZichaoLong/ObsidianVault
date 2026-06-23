---
type: memo
status: active
date: 2026-06-17
tags:
  - control-feedback
  - local-state-access
  - navigable-structure
  - topology
  - workspace
---

# 可导航结构与 Workspace 拓扑备忘

本页是独立备忘，不合入当前主线。它回答一个前置问题：

> `learned noisy directional access` 里说的结构，到底以什么形式、什么拓扑存在？

这里不先追求“结构是什么”的终极数学定义，而是从研究可用性出发：

> 任务状态是否形成某种可导航空间，使局部观察能提供下一步该往哪里看的信号？

## 核心判断

对 TapeWalker / `learned noisy directional access` 来说，关键不是结构的抽象本体，而是结构是否同时支持：

- 局部观察。
- 方向判断。
- 缩小候选空间。
- 局部验证。
- 局部纠偏。
- 可训练轨迹。

一维 tape 只是很窄的一类拓扑。更一般的目标应是：

> 让模型在某种 workspace topology 上主动移动、缩放、标记、读取、写入、验证和回退。

这里的 `topology` 不一定是严格数学拓扑。工程上可先理解为：

- 哪些位置彼此相邻。
- 哪些位置可以一步到达。
- 哪些操作能改变当前位置或视野。
- 局部观察能暴露什么信号。
- 什么验证器能判断局部状态是否正确。

## 结构的常见形式

| 结构形式 | 例子 | 对主动访问的意义 |
| --- | --- | --- |
| 顺序结构 | 时间线、文本段落、trace step、数组 | 可前进、后退、二分、定位转折点 |
| 空间 / 度量结构 | 2D UI、地图、图像、人眼视野 | 可移动、缩放、局部扫描 |
| 层级结构 | 文件树、模块、章节、证明分层、OS 层次 | 可 coarse-to-fine 搜索 |
| 图结构 | 调用图、依赖图、概念图、证明依赖图、数据流图 | 可沿边扩展、回溯、找邻域 |
| 状态转移结构 | 程序执行、agent trace、proof state、workflow | 可定位首次错误、局部回滚 |
| 逻辑 / 验证结构 | 定理、引理、类型、测试、invariant | 可局部验证、局部纠偏 |
| 抽象-细化结构 | 摘要到原文、spec 到代码、lemma 到 proof | 可先看粗粒度，再放大细节 |

这些结构可以天然存在，也可以由系统主动构造。

天然结构：

- 文本段落顺序。
- 文件系统层级。
- 代码 AST。
- 函数调用图。
- 程序执行 trace。
- 数学证明依赖。
- UI 空间布局。

构造结构：

- bookmark。
- 摘要节点。
- 分段索引。
- 验证点。
- checkpoint。
- subgoal tree。
- error attribution graph。
- trace compaction hierarchy。

因此，更准确的牵引不是“结构普遍存在”，而是：

> 现实任务中存在大量可导航结构；有些是天然的，有些需要系统通过标记、摘要、分层、验证点主动构造出来。

## 一个工作形式化

可以把可导航 workspace 写成：

```text
Navigable Workspace = (S, N, A, O, V, C, H)
```

其中：

- `S`：状态单元，例如 workspace cell、proof state、code object、trace step。
- `N`：邻接关系或可达关系，也就是拓扑。
- `A`：可执行动作，例如 move、zoom、jump、read、write、verify。
- `O`：局部观察函数，决定当前位置和当前视野能看到什么。
- `V`：验证器，例如 test、type check、proof check、invariant。
- `C`：访问成本，例如 token、tool call、wall time、setup cost。
- `H`：层级、摘要或 coarse-to-fine 结构。

对主动访问真正有用的是 `N + O + V + H`。

- 只有图，没有局部观察信号，不够。
- 只有局部观察，没有验证，容易走错。
- 只有验证，没有导航，可能退化成穷举。
- 只有层级摘要，没有回到原状态的引用，也会变成不可纠偏的总结。

因此，实验不能只报告“有 workspace”。它应报告：

- `N` 是什么拓扑。
- `O` 返回什么局部信号。
- `V` 是否能验证局部结论。
- `H` 是否由人工构造，还是模型 / 系统生成。
- `C` 是否计入构造和维护成本。

## 结构一般化后，动作是否也要一般化

如果把结构从一维 tape 推广到图、树、层级、UI 空间、proof state、代码对象，那么“方向”也必须一般化。

但这里有一个重要风险：

> 结构可以一般化，动作集不能无限一般化；否则会牺牲 `Token = Instruction` 最重要的东西：稳定事件语义、可训练性、可回放性、可归因性。

如果每种结构都有一套专属动作：

- `move_left / move_right`。
- `go_parent / go_child`。
- `go_caller / go_callee`。
- `go_definition / go_reference`。
- `enter_subgoal / exit_subgoal`。
- `zoom_region / pan_region`。
- `follow_dataflow / follow_controlflow`。

那么系统会变得表达力很强，但也会带来问题：

- action vocabulary 膨胀。
- 不同任务轨迹难以对齐。
- 事件语义难以统一。
- 训练数据被切碎。
- 归因和纠偏标签变得稀疏。
- A 分支的显式状态语义被削弱。

更稳的设计不是“为每种结构发明一套方向”，而是：

> 保持少量稳定控制原语，把结构差异放进 typed operands、topology metadata、resolver 或 view 里。

例如：

```text
read(address, view)
write(address, delta)
navigate(address, relation, budget)
zoom(address, level)
mark(address, label)
verify(scope, invariant)
commit(tx)
rollback(tx)
```

这里 `direction` 不再只是 `left / right`，而是更一般的：

> 在当前 topology 上选择一个能缩小候选空间的局部转移。

它可以是：

- `next / prev`。
- `parent / child`。
- `caller / callee`。
- `definition / reference`。
- `producer / consumer`。
- `subgoal / lemma`。
- `nearby region`。

但这些应优先作为 `navigate` 的参数，而不是每种关系都变成新 opcode。

这有一个清楚的取舍：

- 少量 opcode + typed operands：更统一、更可训练、更可回放，但需要 resolver / runtime 解释 relation。
- 大量结构专用 opcode：更贴近原生结构、更短路径，但训练分散、语义碎片化、工程复杂。

因此，控制反馈线若要保持可训练性和显式状态语义，应优先押注：

> stable small opcode set + topology-aware operands。

而不是：

> unbounded topology-specific action set。

## Tape 作为通用 substrate 的边界

只要支持 `Load/Store + 间接寻址`，tape 理论上可以编码任何有限结构。

图、树、AST、proof graph、调用图、堆对象、文件系统、状态机，都可以放在线性地址空间上。真实计算机也常是这样：底层是线性地址空间，上层实现链表、树、图、对象系统、文件系统、数据库和虚拟内存。

因此，Tape 的强点是 `可表达性` 和 `统一性`。

Tape 的优点：

- 统一、简单，事件语义稳定。
- 易记录、回放、训练和 debug。
- 与 append、context、log、trace 自然兼容。
- 是很好的最小公共 substrate。
- 间接寻址后具备通用性。
- 成本账本更容易写清楚。

但这只是“能表达”，不等于“好导航”。

Tape 的缺点：

- 自然邻接关系可能被编码破坏。例如 graph 邻居在 tape 上可能相隔很远。
- `left / right` 方向太弱，不能自然表达 `caller / callee`、`parent / child`、`definition / reference`、`producer / consumer`。
- 如果依赖 resolver 找地址，复杂性被转移到 resolver。
- 如果依赖 hand-crafted layout，收益可能来自人工布局，而不是模型访问策略。
- meaningful address / typed address 可能偷渡大量语义。
- 对真实任务可能不如原生结构视图高效。

因此，Tape 不是错误的，但不能把它当成天然最优 topology。

更准确的表述是：

> Tape 是通用 substrate，不是必然最优 topology。

## Tape 与一般结构表示的比较

| 表示 | 优点 | 风险 |
| --- | --- | --- |
| 纯 tape | 最统一、最易训练、最易回放 | 破坏自然拓扑，方向信号弱，访问路径可能很长 |
| tape + resolver | 实用、通用、保留统一事件日志 | 复杂性转移给 resolver，若 resolver 太强会吸收 B 分支 |
| 原生 graph / tree / hierarchy | 导航自然，局部信号强，路径短 | 接口碎片化，动作语义难统一，scaffold 成本高 |
| tape log + topology views | 兼顾统一记录与自然导航 | 设计复杂，需要清楚成本账本和视图一致性 |

一个较稳的 hybrid 方案是：

> canonical state / event log 保持 tape-like；模型访问时暴露受控 topology view。

也就是底层保留统一事件语义，上层允许不同结构视图：

```text
linear view
hierarchical view
graph neighborhood view
trace view
proof-state view
code-AST view
UI-spatial view
```

这种方案避免两种极端：

- 纯 Tape：统一但不自然，很多结构导航低效。
- 纯原生结构：高效但碎片化，动作语义和训练接口容易失控。

但 hybrid 方案也不能免费使用。它必须回答：

- view 是谁构造的？
- view 是否可回放？
- view 和 canonical state 是否一致？
- view 构造成本是否计入 `C`？
- 模型收益来自 topology view，还是来自 resolver 偷渡答案？
- 训练数据能否跨 view 对齐？

如果这些问题回答不了，hybrid 也可能只是更复杂的 scaffold。

## 拓扑如何编码，间接寻址如何落地

一般拓扑必须被编码。没有编码，就没有可引用对象，也无法做间接寻址。

更准确地说：

> 间接寻址不是直接寻址“真实结构”，而是寻址某个已编码的结构表示中的节点、边、区域、视图或关系。

一个可导航 topology 至少需要这些对象：

```text
node_id / address
edge / relation
view / scope
resolver(address or query -> node_id)
reader(node_id, view -> observation)
```

常见编码方式：

| 编码方式 | 例子 | 特点 |
| --- | --- | --- |
| adjacency list | `node -> [(relation, node)]` | 最通用，图、调用关系、proof dependency 都可表达 |
| parent/child table | tree、章节、AST | 层级结构自然 |
| interval/range | 文档 span、trace step range、代码行范围 | 适合线性文本和 trace |
| coordinate | UI 坐标、图像 patch、地图位置 | 适合空间结构 |
| object reference | file path、symbol id、proof state id | 工程系统常用 |
| computed neighbor function | `neighbors(node, relation)` | 不必显式存全图，可由 LSP、parser、Lean、DB 动态给出 |
| embedding/index | vector id、cluster id | 可做候选邻居，但语义较弱，必须验证 |

因此，`Load/Store + 间接寻址` 要落地到一般结构，至少要回答：

- 地址指向什么对象？
- 这个对象属于哪个 topology？
- 允许沿哪些 relation 导航？
- reader 返回什么局部观察？
- resolver 是否参与地址解析？
- 解析失败、歧义、过多候选时如何处理？
- 地址是否可回放、可稳定引用？

一个更明确的分层是：

```text
canonical log / tape
  记录所有事件、状态变更、address 引用、验证结果

topology store
  保存或计算 node、edge、relation、view

model-visible interface
  read / navigate / zoom / mark / verify / write
```

Tape 的角色不是承载全部自然拓扑，而是做统一日志和可回放底座。一般结构的角色是提供更自然的可导航视图。

例如代码任务可以这样分层：

```text
canonical tape:
  event_001 read file A
  event_002 inspect symbol foo
  event_003 patch range A:10-20
  event_004 test failed

topology view:
  file tree
  AST nodes
  symbol graph
  call graph
  failing trace
```

模型可见的间接寻址可以是：

```text
read(symbol:foo, view=definition)
navigate(symbol:foo, relation=callers)
read(trace_step:384, view=local_window)
verify(scope=patch_003, invariant=tests)
```

底层仍可把这些全部序列化进 tape / log，但模型不必只用 `left / right` 在 tape 上移动。

这个方案的核心风险是：

> topology view / resolver 可能已经解决了大部分问题，TapeWalker 的贡献被吸收。

因此实验必须拆开：

| 实验组 | 描述 | 可解释结论 |
| --- | --- | --- |
| 纯 tape | 只用线性地址和局部窗口 | 若胜出，支持较强 TapeWalker 主张 |
| tape + opaque topology ids | 有图 / 树 / 层级结构，但地址不携带可读语义 | 检验结构本身是否有帮助 |
| tape + meaningful topology view | 有 typed relation，如 `caller/callee`、`parent/child` | 检验自然 topology view 的工程收益 |
| strong baseline | LSP / SQL / Lean / generated search code / RAG | 判断是否被现有工具链吸收 |
| hybrid | tape log + topology-aware access + explicit state events | 若胜出，只能说明“统一日志 + 结构视图”有价值 |

如果 hybrid 赢，不能直接说明纯 Tape 最优；只能说明统一事件日志与结构视图的组合有价值。

如果纯 tape 在强任务和强基线下也赢，才更接近 TapeWalker 的强主张。

## 数学任务中的结构

数学中，结构常以这些形式存在：

- 概念。
- 定义。
- 定理。
- 引理。
- proof state。
- proof term。
- 依赖图。
- subgoal tree。
- tactic 序列。
- rewrite rule。
- 实例化关系。

这些结构天然适合 `verified subproblem memory`，也适合局部验证：

- 一个 lemma 是否被 Lean 接受。
- 一个 subgoal 是否被解决。
- 一个 tactic 是否改变 proof state。
- 一个 rewrite 是否保持等价。

但数学里的难点是可导航性：

- 好 lemma 的搜索空间极大。
- proof dependency graph 可能稀疏但高维。
- 语义相近不等于可复用。
- 检索到相关定理不等于能实例化和组合。

因此，数学任务给出了非常强的 `V`，但 `N/O/H` 仍然需要研究。

## 程序任务中的结构

程序中，结构常以这些形式存在：

- 文件系统。
- AST。
- 类型系统。
- 函数调用图。
- 数据流图。
- 控制流图。
- 堆栈。
- 对象图。
- module / package graph。
- build graph。
- test / invariant。
- 操作系统资源。
- 指令序列。
- memory hierarchy。

程序任务天然给出多种 workspace topology：

- 代码文本顺序。
- 语法树层级。
- 调用图和依赖图。
- 运行时状态转移。
- 文件和模块层级。

但程序任务的强基线也极强：

- grep / rg。
- LSP。
- tree-sitter。
- compiler。
- debugger。
- tests。
- static analyzer。
- generated search code。

因此，程序任务若用于 TapeWalker，必须选择那些强索引不容易吃掉的切口，例如：

- 长 trace 中定位首次错误决策。
- 跨文件语义状态漂移。
- 无稳定符号的行为回归。
- compact / interrupt 后的动态 workspace recovery。

## 范畴论的位置

范畴论可以被理解为研究“结构及保持结构的映射”的数学语言。

它可能适合以后讨论：

> 不同 workspace 表示之间，哪些结构被保留下来，哪些被丢失？

例如：

- theorem graph 到 proof state trace 的映射。
- code AST 到 runtime trace 的映射。
- 长文档到摘要层级的映射。
- workspace cell 到训练样本的映射。
- agent trace 到显式状态事件的映射。

但当前阶段不应把范畴论作为第一工具。

原因：

- 它不会直接告诉我们某个任务有没有方向信号。
- 它不会直接告诉我们模型能否学会访问策略。
- 它不会直接给出访问复杂度优势。
- 它容易让研究过早抽象化，远离可输实验。

当前更适合的工具是：

- 图论。
- 状态机。
- 序结构。
- 层级结构。
- 搜索理论。
- 主动学习。
- 验证器。
- 成本模型。

范畴论可以作为远期整理语言，而不是当前推进实验的核心语言。

## 对控制反馈线的启发

`learned noisy directional access` 的研究命题可以进一步改成：

> 现实任务中存在大量可导航结构；有些天然存在，有些可由系统构造。模型若能学习这些结构上的带噪方向判断，就可能在局部观察预算下获得搜索和纠偏优势。

这比“结构普遍存在”更可检验。

它要求实验回答：

- 任务中的 `S/N/O/V/C/H` 分别是什么？
- 结构是天然存在，还是由 scaffold 构造？
- 局部观察是否真的给出方向信号？
- 模型是否学到方向判断，而不是吃到人工地址语义？
- 验证器是否能防止错误方向导致不可恢复失败？
- 构造结构的成本是否抵消访问收益？

如果这些问题回答不了，`active foveated workspace access` 就容易停留在哲学直觉。

## 当前较稳的立场

综合上面的取舍，当前较稳的立场是：

> 结构可以一般化为可导航 workspace，但 action language 应保持小而稳定；结构差异应主要进入 address、relation、view、resolver 和 topology metadata，而不是让 opcode 无限制膨胀。

以及：

> Tape 可以作为统一状态日志和通用 substrate，但不应预设为最优访问拓扑。真正要比较的是：纯 tape、tape + resolver、原生 topology view、tape log + topology views，哪一种在强基线和成本账本下更可训练、更可回放、更可归因、更适合局部纠偏。

这也给出一个直接实验要求：

- 同一任务同时实现 tape view 和 native topology view。
- 固定底层状态和验证器。
- 比较访问步数、观察 token、方向准确率、恢复率、训练样本效率。
- 计入 view / resolver 构造成本。
- 做 meaningful address、typed address、opaque address 消融。

如果 native topology view 明显胜出，说明 Tape 适合作为底层日志而非用户级访问接口。

如果纯 tape 在强任务上也能胜出，才更接近 TapeWalker 的强主张。
