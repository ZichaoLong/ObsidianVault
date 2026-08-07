---
type: index
status: active
tags:
  - tide
  - decentralized-nn
---

# TIDE / 去中心化神经网络

> [!summary] 本页定位
> 本页是 Tide 线的唯一入口，只负责当前命题、文档地图、写作规则、主张边界与历史动机。正式数学见 [[tide-mathematical-foundations]] 和 [[adaptive-routing-prefill-lower-bound]]；模型候选见 [[tide-model-architecture-and-training]]；工程完成度见 [[tide-runtime-validation-and-status]]。

## 一页版结论

TIDE 是 `Token Inference Decentralized Engine`。总体目标是研究同时具有下列性质的自回归神经系统：

1. 空间通信保持局部、有界度。
2. 每个输入位置只激活全部潜在计算中的稀疏子集。
3. `prefill` 与逐位置 `decode` 保持同一 reference semantics。
4. 有限 chunk 的执行能暴露完整的数据、状态、控制、可见性和提交依赖。
5. 经证明可批量化的 node、kernel 或 subgraph 可以获得低 span 实现；无法批量化的部分显式承担顺序成本。

当前结论分为四层：

- **Kernel 正向结果**：token-local、causal attention、affine scan、linear attention accumulator，以及由这些 kernel 组成的有限 Transformer/Mamba chain，已有 chunk correctness 证明路线。
- **一般空间 DAG 正向结果**：显式 allocator、节点状态、带到达轮次的消息、边界在途消息和不等长路径可以按空间拓扑序构造；每个节点可一次处理窗口内属于它的时间桶，空间节点遍历次数不随 chunk 长度增长。
- **尚缺的正向结果**：空间拓扑序构造不自动推出时间分块组合律。完整 model-level `prefill = decode` 仍需从逐绝对轮次节点转移证明窗口折叠，并为各 node/subgraph 给出低-span execution witness。
- **反向结果**：若模型类别允许任意、不可组合的 pointer-chasing 式自适应 routing，则不存在对该类别所有实例都有效的 exact、work-efficient、次线性 adaptive-depth prefill。该下界不能未经 embedding 证明就直接套到每个具体 selector。

LH 是“局部通信 + 超稀疏”的复杂机制样本和 CPU golden reference，不是理论必须完整复刻的终点。若 LH 的 selector、状态副作用或交错控制链破坏高性能 prefill，可以在不放弃总体目标的前提下简化、替代或移出 strict family。

当前模型候选 HB-Lattice-v0 使用层级 backbone、有限生命周期的稀疏分支和固定 merge deadline。它已有结构 reference 和 `chunk == repeated decode` toy 验证，但尚未证明可训练、可扩展或优于 Transformer/Mamba/MoE。

## 文档地图

当前只保留六个 Markdown 职责文件：

| 文档 | 职责 | 结论类型 |
| --- | --- | --- |
| 本页 | 入口、术语、阅读顺序、主张边界 | 导航 |
| [[tide-mathematical-foundations]] | StepTransition、fold、kernel theorem、logical event DAG、显式 allocator general DAG、归属证书和 zero-delay 边界 | 正式定义与正向定理 |
| [[adaptive-routing-prefill-lower-bound]] | 黑盒自适应路由链的 parallel-query 下界及局部稀疏 Graph 嵌入 | 正式反向定理 |
| [[tide-model-architecture-and-training]] | HB-Lattice、selector capability、work/span、训练风险与实验顺序 | 架构候选与研究备忘 |
| [[tide-runtime-validation-and-status]] | Runtime contract、LH 映射、artifact equality、CPU 对齐、性能和 backend 状态 | 实现规范与动态快照 |
| [[tide-background-history-and-references]] | ISA/编译器/dataflow 谱系与人脑传播调查 | 外部背景，不承担证明 |

建议阅读顺序：

1. 数学主线：本页 -> [[tide-mathematical-foundations]] -> [[adaptive-routing-prefill-lower-bound]]。
2. 模型设计：[[tide-model-architecture-and-training]]。
3. 工程实现：[[tide-runtime-validation-and-status]]。
4. 外部概念：遇到 ISA、SSA、MemorySSA、dataflow、fixed point 或脑科学类比时查 [[tide-background-history-and-references]]。

## 核心术语

| 术语 | 本文含义 | 不表示 |
| --- | --- | --- |
| `token` | 输入序列中的离散输入单位；数学上通常由位置 $t$ 和输入值 $x_t$ 分开表示 | 消息、事件或计算轨迹 |
| 输入位置 | 全局流中的自然数下标 $t$ | 内部 round 或物理完成时间 |
| 空间节点 | 静态 Graph 中可复用的计算与状态持有位置 | 一次执行中的事件实例 |
| 消息 | 一次发送产生的有限记录，至少含消息标识符、源、目标、到达轮次和载荷 | 空间边或完整轨迹 |
| 事件 | 某次有限执行中实际发生的一次计算、状态、控制、消息或提交动作 | 可复用空间节点 |
| `owner` | 可选的消息或输出归属位置标签 | 消息身份、路径身份或逻辑时间 |
| `support` | 某个值可能依赖的有限输入位置集合 | 物理收件箱 |
| `frontier` | 输入支撑位置的保守上界 | 调度 wavefront 或消息到达时间 |
| 边界延续状态 | 从位置 $B$ 开始执行所需的节点状态与在途消息 | 仅由 chunk 长度决定的缓存 |
| 发送激活 | 节点在某逻辑轮次实际产生至少一条出站消息 | hidden activation tensor |
| logical event DAG | 一次有限执行的事件集合及其直接语义依赖关系 | 静态空间 Graph 本身 |
| `prefill = decode` | 任意合法 chunk 切分与逐位置 reference fold 产生相同可观察输出和边界状态 | 只比较最终 logits 或只允许从位置 0 开始 |

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

### 数学

1. 为显式 allocator 一般空间 DAG 定义逐绝对轮次节点参考转移。
2. 从该转移证明窗口时间分块组合律，而不是把 node chunk contract 直接作为前提。
3. 给每类 node/subgraph 声明 `token-local`、`scan-composable`、`causal-bulk`、`ready-set-local` 或 `sequential-fallback`，并分别证明 lowering contract。
4. 把 correctness 与 work、span、memory、communication cost ledger 分开。
5. 对具体 stateful selector 判断它落入结构化可并行特例，还是能嵌入自适应路由下界。

### 模型与训练

1. 先验证 always-on backbone 和固定均衡稀疏路径。
2. 再加入 token-local learned routing。
3. 随后加入慢更新、逐序列隔离的负载偏置。
4. 最后才研究严格逐位置递推的 stateful selector。
5. 分别记录 route churn、负载、梯度覆盖、状态数值和 chunk/decode artifact equality。

### Runtime

1. 固定 model-level `prefill()` 的输入、读出和 boundary-state contract。
2. 让 Event IR 显式表示事件标识符、逻辑时间、状态版本、依赖与提交。
3. 先完成 CPU semantic gate 和逐阶段 artifact equality。
4. 再进行 packed/crossbatch lowering、并行 executor 与 Ascend backend。

## 当前主张边界

当前可以主张：

- Tide 的 role-aware phase abstraction 能承载当前覆盖范围内的 LH C++ 计算。
- 独立 Tide CPU kernels 在当前覆盖配置和 hidden/cache mode 上数值对齐 native LH。
- Transformer/Mamba 主力 kernel family 已有构造性 chunk correctness 证明路线。
- 显式 allocator 的一般空间 DAG 已证明常数次空间拓扑遍历，但没有自动证明时间分块组合律。
- 自适应路由下界已在明确的 deterministic exact black-box query model 中证明。
- HB-Lattice reference 已验证 toy 语义下 `chunk == repeated decode`。

当前不能主张：

- 任意一般 Graph 都有高性能 chunk prefill。
- 当前完整 LH 自动满足 strict model-level `prefill = decode`。
- 任意具体 selector 已经落入自适应路由下界。
- CPU 数值对齐证明了模型可训练性、scaling 或性能优势。
- HB-Lattice 已经稳定训练或优于现有 Transformer、Mamba、MoE。
- 通用 packed/crossbatch lowering、异步执行或 Ascend backend 已经完成。
- Zero-delay algebraic loop 可以由普通 Graph 调度器自动解释。

## 整合记录

当前六文件结构由 2026-08-07 的文档整合产生。整合前的逐文件版本保存在 Git 提交 `d27819f`。其中：

- `step-transition-mathematical-specification`、`explicit-allocator-general-dag-model` 和 `token-owned-general-dag-routing` 进入数学基础。
- `adaptive-routing-prefill-impossibility` 改名为更准确的 lower-bound 文档。
- HB-Lattice、selector capability 和训练稳定性进入模型架构与训练。
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
