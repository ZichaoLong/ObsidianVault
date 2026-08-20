---
type: index
status: active
tags:
  - tide
  - decentralized-nn
---

# TIDE / 去中心化神经网络

> [!summary] 本页定位
> 本页是 Tide 线的唯一入口，只负责战略路线、当前命题、文档地图、写作规则、主张边界与历史动机。正式数学见 [[tide-mathematical-foundations]] 和 [[adaptive-routing-prefill-lower-bound]]；模型候选见 [[tide-model-architecture-and-training]]；checkpoint 生长的当前实验政策见 [[tide-checkpoint-growth-experiment-contract]]；工程完成度见 [[tide-runtime-validation-and-status]]；统计力学类比及其严格边界见 [[tide-statistical-mechanics-and-information-dynamics]]。

## 一页版结论

TIDE 是 `Token Inference Decentralized Engine`。总体目标是研究同时具有下列性质的自回归神经系统：

1. 空间通信保持局部、有界度。
2. 每个输入位置只激活全部潜在计算中的稀疏子集。
3. `prefill` 与逐位置 `decode` 保持同一 reference semantics。
4. 有限 chunk 的执行能暴露完整的数据、状态、控制、可见性和提交依赖。
5. 经证明可批量化的 node、kernel 或 subgraph 可以获得低 span 实现；无法批量化的部分显式承担顺序成本。

当前结论分为五层：

- **Kernel 正向结果**：token-local、causal attention、affine scan、linear attention accumulator，以及由这些 kernel 组成的有限 Transformer/Mamba chain，已有 chunk correctness 证明路线。
- **函数保持生长结果**：单步 transition 的精确状态嵌入可推广到任意长度 fold；中性 residual 分支保持原函数；token-local selector、无操作未选分支和固定加法 merge 在分支 chunk correctness 已成立时保持 chunk correctness。
- **一般空间 DAG 正向结果**：显式 allocator、节点状态、带到达轮次的消息、边界在途消息和不等长路径可以按空间拓扑序构造；每个节点可一次处理窗口内属于它的时间桶，空间节点遍历次数不随 chunk 长度增长。
- **尚缺的正向结果**：空间拓扑序构造不自动推出时间分块组合律。完整 model-level `prefill = decode` 仍需从逐绝对轮次节点转移证明窗口折叠，并为各 node/subgraph 给出低-span execution witness。
- **反向结果**：若模型类别允许任意、不可组合的 pointer-chasing 式自适应 routing，则不存在对该类别所有实例都有效的 exact、work-efficient、次线性 adaptive-depth prefill。该下界不能未经 embedding 证明就直接套到每个具体 selector。

对一般 static schema Graph，可以先求 structural SCC 并得到 condensation DAG；这是已经成立的图论分解，只把循环求值义务局部化到各个宏节点，并不替 SCC 证明语义、有限前缀进展或低 span。开放 streaming 执行可以永不全局停止，但若要声明某个有限 cut 已完成，仍需 source seal、局部有限性、可续接的 pending/in-flight 状态和不允许未来回写过去的硬进展证书。相应 SCC macro contract 目前是候选数学/runtime 接口，尚未成为通用组合定理或已实现 executor。

因此，“能精确执行”“有限前缀必然返回”“是否整体静止”“能否沿序列批量执行”必须分别登记。高性能有限前缀执行依次接受 semantic、progress、parallel-complexity 与 hardware-lowering 四道 gate；这些 gate 是设计审查框架，不是只看 Graph 拓扑即可得到的完备分类。

LH 是“局部通信 + 超稀疏”的复杂机制样本和 CPU golden reference，不是理论必须完整复刻的终点。若 LH 的 selector、状态副作用或交错控制链破坏高性能 prefill，可以在不放弃总体目标的前提下简化、替代或移出 strict family。

当前不是只有一条模型设计路线。Graph 收缩线从 LH 和一般 Graph 出发，逐步加入高性能 `prefill`、可训练性与局部通信约束；checkpoint 生长线从可完整装载的预训练 Transformer/Mamba 出发，通过函数保持接口和可归因实验引入固定汇聚分支、selector、递归结构和空间化。两条路线都服务于“局部通信 + 超稀疏”的总体目标，但不预设它们必然得到同一个最终架构。

HB-Sliced 是 Graph 收缩线当前最具体的空间候选：有限空间基图 $H$ 定义每个深度切片中的局部邻接，实际消息边只从 $d$ 指向 $d+1$。最小实例 HB-Line-v0 已有结构 reference，验证 depth-major chunk、token-major decode 和分段 chunk continuation 的输出、route artifact 与状态相同；它尚未证明真实 kernel 低 span、模型可训练、可扩展或优于 Transformer/Mamba/MoE。checkpoint 生长线尚未形成同等级别的可运行 reference，这是当前最优先补齐的实验缺口。

Checkpoint 生长线当前不再由单一串行架构阶梯支配，而是并行推进两个工作流：工作流 A 建立 dense checkpoint、成熟 flat MoE 和 matched selected-dispatch control；工作流 B 从 checkpoint 中性生长，正面验证 broadcast-observe、private state 与 later readout 组成的局部计算介质候选。该政策允许完整候选联合采用有共同设计理由的机制以寻找存在性信号，但任何单项因果结论仍需要配对反事实。

Tide 当前最大的科学不确定性仍是 learning value：局部通信、持久状态、feedback 与动态 routing 是否能被稳定学到，并在匹配训练资源后改善能力、泛化或 scaling。sequence-level bulk execution 则是主要规模化风险。二者逻辑上不同、实验上耦合；现有并行计算谱系可以约束执行设计，却不能替代 compute-matched 神经架构实验。

## 两条战略路线

### Graph 收缩线

这条路线从表达力较强、机制混合且不保证高性能 `prefill` 的对象出发：

```text
一般 static schema Graph / LH mechanism pool
├── 对一次有限执行展开并验证
│   └── dependency-complete dynamic event DAG
└── 对可接受架构族施加结构约束
    └── 显式 allocator 的一般空间 DAG
        └── HB-Lattice 的历史几何直觉
            └── HB-Sliced / HB-Line / HB-Plane
                └── 有界递归、固定 merge 的结构化分支族
```

dynamic event DAG 是一次执行的 correctness 对象，空间 DAG 是静态架构限制；前者不是通往后者的中间拓扑。一般 static schema Graph 的 SCC condensation 又是第三种对象，不能与二者混写。condensation DAG 只规定宏节点之间的无环连接，不替宏节点内部选择 fixed-round 展开、scan、solver、sequential fallback 或其他求值语义。

它主要承担四项职责：寻找理论上限，给出 correctness 与 complexity 边界，识别会破坏 chunk composition 或低 span 的机制，并为局部通信、超稀疏和训练稳定性提供设计约束。LH 是这条路线的重要早期动机和机制样本，但不是必须逐项保留的终点。历史 HB-Lattice 是从一般空间 DAG 走向层级局部结构的中间直觉；当前 HB-Sliced 是消除“空间平面、模型阶段和 runtime lowering”混写后的正式继承者。

### Checkpoint 生长线

这条路线从已经可训练、可高性能 `prefill` 且存在预训练 checkpoint 的架构出发：

```text
原生预训练 Transformer / Mamba
-> Tide 中的完全等价装载与函数保持接口
├── 工作流 A：dense / flat MoE 基线与 Group-receiver selected control
└── 工作流 B：broadcast-observe 完整候选
      ├── private state 与 later readout
      ├── 有界局部 selector、active/message/depth budget
      ├── always-on backbone 与 fixed merge
      └── 按观察引入递归、会聚、空间化与结构变异
```

它主要承担可重复实验、正面候选发现、配对归因、训练稳定性验证和实际推广。早期必须完整保留原参数与初始化语义；工作流 A 与 B 共享数据、correctness oracle、成本口径和实验账本。随着证据积累，后期允许删除冗余节点、改变状态布局、重写 kernel 或形成不再与原 Transformer 结构兼容的后代模型。此时应保留 checkpoint 谱系和实验归因，不能继续声称结构或函数仍然完全兼容。

### 期待汇合而不预设汇合

递归固定 merge 分支是当前两条路线共同指向的候选交界面，但“共同指向”不是已证明的汇合定理。后续可能出现三种结果：

1. 两条路线得到同一个可训练、可高性能实现的结构族。
2. 两条路线只共享固定 merge、selector scope、局部 DAG 等部分契约，具体拓扑不同。
3. 两条路线保持分离：Graph 线提供更高表达上限，checkpoint 线提供更可靠的工程模型。

因此，Tide 不以强行统一为目标。理论约束应裁剪明显不可行的 checkpoint 扩展；checkpoint 实验也应反过来检验 Graph 线的约束是否过强、遗漏了哪些有效结构。

## 文档地图

当前核心研究线保留八个职责文件：

| 文档 | 职责 | 结论类型 |
| --- | --- | --- |
| 本页 | 入口、术语、阅读顺序、主张边界 | 导航 |
| [[tide-mathematical-foundations]] | StepTransition、fold、kernel theorem、logical event DAG、显式 allocator general DAG、归属/因果证书、structural SCC 与 condensation、多端口 finite-cut 候选契约、函数保持生长及 fixed-merge 闭包 | 正式定义、正向定理与明示的 proof obligations |
| [[adaptive-routing-prefill-lower-bound]] | 黑盒自适应路由链的 parallel-query 下界及局部稀疏 Graph 嵌入 | 正式反向定理 |
| [[tide-model-architecture-and-training]] | 两条战略路线、递归固定 merge 分支、HB-Sliced/HB-Line、selector 与训练风险、四道 execution gate | 架构候选与研究备忘 |
| [[tide-checkpoint-growth-experiment-contract]] | checkpoint 生长的证据分级、并行工作流、配置坐标、配对反事实、五道实验 gate 与首个交付 | 当前实验政策与候选契约 |
| [[tide-runtime-validation-and-status]] | Runtime contract、LH 映射、artifact equality、CPU 对齐、候选 SCC macro 接口、性能和 backend 状态 | 实现规范、候选接口与动态快照 |
| [[tide-background-history-and-references]] | ISA/编译器/dataflow、SCC、finite-prefix progress 与相关脑科学谱系 | 外部背景，不承担证明 |
| [[tide-statistical-mechanics-and-information-dynamics]] | 碰撞历史、粗粒化、路径相关性、kinetic limit 与耗散结构类比的 Tide 评述 | 研究备忘与候选假设，不承担证明 |

建议阅读顺序：

1. 战略与模型：本页 -> [[tide-model-architecture-and-training]]。
2. Graph 收缩线数学：[[tide-mathematical-foundations]] -> [[adaptive-routing-prefill-lower-bound]]。
3. Checkpoint 生长实验：[[tide-checkpoint-growth-experiment-contract]] -> [[tide-runtime-validation-and-status]]。
4. 外部概念：遇到 ISA、SSA、MemorySSA、dataflow、fixed point 或脑科学类比时查 [[tide-background-history-and-references]]。
5. 统计力学假设：研究 coarse-graining、path correlation、route entropy 或宏观极限时查 [[tide-statistical-mechanics-and-information-dynamics]]；其中内容不进入正式证明链。

### 附录与研究暂存

下列文档不计入八份核心职责文件，也不进入正式证明、架构或 runtime 的依赖链：

| 附录 | 定位 |
| --- | --- |
| [[appendices/tide-directed-learning-roadmap|Tide 定向学习路线]] | 个人课程、证明和实现训练脚手架；不是研究结论或项目里程碑 |
| [[appendices/research-memos/scc-macro-node-logical-time-research-memo|SCC 宏节点剩余研究问题与迁移索引]] | 只保留尚未合入核心文档的开放问题及迁移状态；已合入内容不在此重复 |

## 核心术语

| 术语 | 本文含义 | 不表示 |
| --- | --- | --- |
| `token` | 输入序列中的离散输入单位；数学上通常由位置 $t$ 和输入值 $x_t$ 分开表示 | 消息、事件或计算轨迹 |
| 输入位置 | 全局流中的自然数下标 $t$ | 内部 round 或物理完成时间 |
| 空间基图 | 有限图 $H=(U,F)$；只定义一个切片中的局部邻接关系 | 同切片计算依赖图 |
| 深度切片 | 固定深度 $d$ 上的一组空间位置 $(d,u)$ | token 时间、层级尺度或 runtime phase |
| 空间节点 | 静态 Graph 中可复用的计算与状态持有位置 | 一次执行中的事件实例 |
| receiver | 能接收声明的局部上游消息，并拥有自身参数或语义状态的下游模块 | 必然执行昂贵计算的 active node |
| 消息 | 一次发送产生的有限记录，至少含消息标识符、源、目标、到达轮次和载荷 | 空间边或完整轨迹 |
| 事件 | 某次有限执行中实际发生的一次计算、状态、控制、消息或提交动作 | 可复用空间节点 |
| `owner label set` | 事件直接联合处理或对外标识的一组输入位置标签 | 数值依赖集合、消息身份或逻辑时间 |
| `dependency support` | 某个值可能实质依赖的有限输入位置集合 | owner 标签或物理收件箱 |
| `causal input frontier` | `dependency support` 的输入前缀上界；$-1$ 表示不依赖输入 | 调度 wavefront、消息到达时间或完成进度 |
| `progress frontier / hard output watermark` | 对过去区域的硬完成证书：合法 continuation 不会再产生落入该区域的新工作或输出 | 因果依赖上界、墙钟空闲或估计型 event-time watermark |
| structural SCC | static schema Graph 中极大的互相可达节点集合 | 同一 logical rank 的 zero-delay SCC 或一次运行的 event graph |
| condensation DAG | 以 structural SCC 为顶点的商 DAG；跨宏节点边仍保留 edge identity 与 port 边界 | SCC 内部求值算法或终止证明 |
| source seal | 输入源以后不会再提交某个 downward-closed cut 内新输入的硬承诺 | 暂时没有输入或队列为空 |
| 边界延续状态 | 从位置 $B$ 开始执行所需的节点状态与在途消息 | 仅由 chunk 长度决定的缓存 |
| 发送激活 | 节点在某逻辑轮次实际产生至少一条出站消息 | hidden activation tensor |
| logical event DAG | 一次有限执行的事件集合及其直接语义依赖关系 | 静态空间 Graph 本身 |
| `prefill = decode` | 任意合法 chunk 切分与逐位置 reference fold 产生相同可观察输出和边界状态 | 只比较最终 logits 或只允许从位置 0 开始 |
| 函数保持生长 | 扩展模型在指定初始参数和状态嵌入下，与原模型产生相同输出及下一状态 | 扩展模型在继续训练后永远不改变 |
| checkpoint 兼容 | 原 checkpoint 的每个参数都有声明的装载位置，并满足当前阶段规定的语义等价测试 | 后代模型永远保持原 state-dict 形状 |
| 结构变异 | 以已有 checkpoint 为初始化或 teacher，经过节点删除、重参数化或拓扑变化得到后代模型 | 仍可声称与原模型结构完全兼容 |
| 固定 merge | 候选分支的汇聚位置和汇聚算子由模型结构预先声明；激活集合可以动态变化 | 所有候选分支都必须执行或路径必须等长 |
| `selected-dispatch` | 只有 local selector 选中的 receiver 才 Receive/Update/Compute/Emit 的传播 profile | 所有 Tide 的默认语义 |
| `broadcast-observe` | active sender 沿全部声明局部出边发送；实际 receiver 都 Observe/Update，只有 active receiver 执行昂贵计算并继续发送 | 全局广播、已证明收益或所有 Tide 的必要条件 |

`token`、`prefill`、`decode`、`logits`、模型名、固定缩写、接口名和代码字段保留英文；其余解释性正文优先使用中文。

## 数学写作规则

Tide 正式数学文档遵守以下规则：

1. 一个对象进入定义、命题、定理或证明前，必须声明为集合、集合元素、函数、部分函数、关系、有限序列、多重集、有限元组，或由这些对象定义的性质。
2. 函数给出定义域和值域，关系给出所在笛卡尔积，元组给出各坐标所属集合。
3. 定义正文和证明正文都不能依赖未定义的工程名词。
4. 直观说明可以不形式化，但必须真正直白，并且不得暗中承担后续证明前提。
5. 每个显示公式都应能逐项回答“该符号属于哪个集合”。
6. 定义、例、反例、引理、定理、证明、适用边界和工程含义按依赖顺序出现。
7. 正式数学文件自足；外部文档只能提供历史、例子和参考，不能成为隐式定义来源。
8. 明确区分定义性等价、充分条件、必要条件、充要条件、工程验证和历史类比。
9. 同一个英文词有多种含义时，先给出 Tide 本文含义与排除含义。
10. 新概念首次出现时，声明它是数学对象、语义 profile、实现字段、历史用语或待定义研究占位词。

推荐章节模板：

```text
动机问题
-> 最小例子
-> 数学定义
-> 正例与反例
-> 引理 / 定理
-> 完整证明
-> 适用边界
-> 对实现与实验的约束
```

## 当前研究顺序

### Graph 收缩线

1. 为显式 allocator 一般空间 DAG 定义逐绝对轮次节点参考转移。
2. 从该转移证明窗口时间分块组合律，而不是把 node chunk contract 直接作为前提。
3. 先对一个受限 SCC family（例如 fixed-round 或带显式 delay 的有限 family）实例化多端口 boundary、finite-cut、continuation、seal 与 output-watermark 契约，再尝试证明宏节点 DAG 的组合定理。
4. 给每类 node/subgraph 声明 `token-local`、`scan-composable`、`causal-bulk`、`ready-set-local` 或 `sequential-fallback`，并分别证明 lowering contract；`certified SCC` 只表示这些证书的封装范围，不是第六种 capability。
5. 把 semantic、progress、work/span/memory/communication 与 hardware measurement 分账，并给具体候选登记正交的语义/进展和 sequence-bulk 等级。
6. 对具体 stateful selector 判断它落入结构化可并行特例，还是能嵌入自适应路由下界。

### Checkpoint 生长线

1. 选择一个 pre-norm decoder-only checkpoint，完成原生参数、logits、cache/state、`prefill/decode`、梯度与 fresh save/reload equality。
2. 建立函数保持 growth operator 和两条工作流共同使用的 reference contract、成本口径与 ExperimentLedger。
3. 工作流 A 建立 dense continued-pretraining、成熟 flat MoE、checkpoint-grown MoE 与 Group-receiver selected control。
4. 工作流 B 同步建立最小但机制完整的 BO 候选，并保留 matched selected-dispatch、state knockout 与 route replay。
5. 以“探索—诊断—确认”闭环推进；递归、stateful selector、会聚和空间化由完整候选需要或已观察问题牵引，不再由固定阶段号禁止。

### Selector 与训练

1. 固定/hash、content-only、pre/post-Update state-aware 和 load-aware 是诊断 profile，不再承担全局开发顺序。
2. selector 可以按完整候选需要读取当前内容、receiver semantic state 和逐序列 history/load state，但每个输入必须显式登记。
3. 任何改变 route/output 的跨 Token state 都必须进入 reference state，支持 continuation、save/reload 与 replay。
4. BO 读取 post-Update proposal/state 时，必须另有“读取/忽略”和 matched/replay route 对照。
5. 分别记录 route churn、receiver exposure、梯度覆盖、state use、write-to-read 延迟和 chunk/decode artifact equality。

### Runtime

1. 固定 model-level `prefill()` 的输入、读出和 boundary-state contract。
2. 让 Event IR 显式表示事件标识符、逻辑时间、状态版本、依赖与提交。
3. 先完成 CPU semantic gate 和逐阶段 artifact equality。
4. 再进行 packed/crossbatch lowering、并行 executor 与 Ascend backend。

若某个实验引入 SCC macro，应在通用 executor 之前先实现最小受限 profile：稳定 edge/port identity、`AdvanceUntil(cut)`、source seal、完整 continuation、hard output watermark，以及 zero-delay/Zeno/backdating 反例测试。当前仓库尚未实现这套接口。

## 当前主张边界

当前可以主张：

- Tide 的 role-aware phase abstraction 能承载当前覆盖范围内的 LH C++ 计算。
- 独立 Tide CPU kernels 在当前覆盖配置和 hidden/cache mode 上数值对齐 native LH。
- Transformer/Mamba 主力 kernel family 已有构造性 chunk correctness 证明路线。
- 单步精确状态嵌入、有限 DAG 节点细化和 token-local 固定 merge 分支已有明确前提下的闭包定理。
- 显式 allocator 的一般空间 DAG 已证明常数次空间拓扑遍历，但没有自动证明时间分块组合律。
- 任意有限 static schema Graph 的 structural SCC 与 condensation DAG 分解成立；这只是图论结构结论，不包含 SCC 内部求值或性能结论。
- 自适应路由下界已在明确的 deterministic exact black-box query model 中证明。
- HB-Line-v0 reference 已验证 toy 语义下 depth-major chunk、token-major decode 和分段 continuation 的 artifact equality。
- 两条路线是否最终汇合仍是研究假设，而不是当前结论。
- 四道 gate、正交 execution profile 和候选 SCC macro contract 已形成设计框架，但具体 family 仍需逐项提交证明、实现或测量证据。

当前不能主张：

- 任意一般 Graph 都有高性能 chunk prefill。
- SCC 分解、宏节点封装或 termination certificate 本身解决了循环求值、有限前缀组合或低 span。
- 当前完整 LH 自动满足 strict model-level `prefill = decode`。
- 任意具体 selector 已经落入自适应路由下界。
- CPU 数值对齐证明了模型可训练性、scaling 或性能优势。
- 当前 runtime 已实现通用 `AdvanceUntil(cut)`、source seal、hard output watermark 或 SCC continuation/replay。
- Tide 的 feedback、持久状态、局部通信或动态 routing 已经带来优于强基线的 learning value。
- `broadcast-observe` 已经具有 learning、scaling 或端到端系统收益。
- receiver 收到消息或状态发生变化，等于该状态已在以后有效读出。
- 路径相关 receiver exposure 变薄必然等于当前 hidden 丢失上下文，或多父会聚必然恢复无损记忆。
- 一个联合使用递归、private state、selector 和 fixed merge 的候选成功，分别证明了这些部件必要。
- Head/Group-wise、全维 mixer 或逻辑局部邻接本身已经证明去中心化系统收益。
- HB-Sliced/HB-Line 已经稳定训练或优于现有 Transformer、Mamba、MoE。
- 已经完成预训练 Transformer/Mamba checkpoint 到递归 Tide 分支模型的函数保持生长链。
- 通用 packed/crossbatch lowering、异步执行或 Ascend backend 已经完成。
- Zero-delay algebraic loop 可以由普通 Graph 调度器自动解释。
- 统计力学、熵增或耗散结构类比已经构成 Tide correctness、prefill 或训练稳定性定理。

## 整合记录

Tide 在 2026-08-07 先被整合为六个职责文件，随后增加统计力学与信息动力学评述。2026-08-20 又加入 checkpoint 生长实验契约，因此当前共有八个职责文件。整合前的逐文件版本保存在 Git 提交 `d27819f`；实验契约初始政策对应 tide 仓库 `fractal-latcarf` 分支提交 `19999de069fa15c39b7bbf2e46db33c723c3b456`。其中：

- `step-transition-mathematical-specification`、`explicit-allocator-general-dag-model` 和 `token-owned-general-dag-routing` 进入数学基础。
- `adaptive-routing-prefill-impossibility` 改名为更准确的 lower-bound 文档。
- HB-Lattice 历史草案、HB-Sliced/HB-Line 当前候选、selector capability 和训练稳定性进入模型架构与训练。
- checkpoint 生长的并行工作流、BO 主假设、matched control、五道 gate 与首个交付进入实验契约。
- 实现规范、当前状态和 LH/tide.old 历史进入 runtime 文档。
- 编译器/dataflow 谱系和脑科学调查进入背景参考。

已降级文档中的重复定义和过时状态没有继续复制；若需要考古其逐行推导，以提交 `d27819f` 为准。

## 历史动机

MoE 让参数计算稀疏化，但 expert dispatch、全局路由、负载均衡和跨设备同步仍可能形成集中式或 all-to-all 通信压力。Tide 的早期问题是：能否用长期稳定的有界度局部通信替代一部分全局 dispatch，同时保留自回归序列执行和可训练性。

概念上，可以把 dense Transformer block 看作 attention/FFN 顺序链，把标准 MoE block 看作带全局 router 的星型阶段，再把 Tide 的候选看作局部连接、分层且稀疏激活的 Graph。下图只表达研究动机，不是对所有实现的精确通信模型。

![[assets/images/linked-list-transformer-star-moe-decentralized-graph-nn-01.png|48%]] ![[assets/images/linked-list-transformer-star-moe-decentralized-graph-nn-02.png|48%]]

最早的流式原型按输入位置和内部 round 双重循环：

```python
for token in input_tokens:
    input_signal = embed(token)
    for internal_round in range(route_length):
        parallel_emit(graph)
        parallel_receive(graph)
    output_token = readout(output_node)
```

它适合 streaming/decode，却没有自动获得序列方向的高性能 prefill。后来引入：

```text
absolute_round = input_position * external_period + internal_round
```

作为时间锚点，并进一步区分输入位置、绝对轮次、阶段、消息到达时间和可选 `owner`。这条演化最终形成当前的有限事件 DAG、窗口边界状态、显式 allocator 和自适应控制下界两条数学主线。早期 LH 吞吐记录与实现演化见 [[tide-runtime-validation-and-status#第三部分：LH 与 tide.old 历史上下文|LH 与 tide.old 历史上下文]]。
