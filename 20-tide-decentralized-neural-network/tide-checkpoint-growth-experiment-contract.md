---
type: checkpoint-growth-experiment-contract
status: active-candidate
source_repository: ZichaoLong/tide
source_branch: fractal-latcarf
source_revision: 19999de069fa15c39b7bbf2e46db33c723c3b456
updated: 2026-08-20
tags:
  - tide
  - checkpoint-growth
  - broadcast-observe
  - sparse-routing
  - experiment-contract
---

# Tide Checkpoint 生长实验契约

> [!summary] 本页定位
> 本页是 checkpoint 生长线当前实验政策、配置坐标、配对反事实、验收 gate 和首个交付的唯一概念源。架构推导与长期候选见 [[tide-model-architecture-and-training]]；正式数学只见 [[tide-mathematical-foundations]]；实现状态见 [[tide-runtime-validation-and-status]]。实验仓库的启动文档是面向开发者的实现镜像，不反向覆盖本页的证据边界。

> [!important] 当前证据状态
> 当前尚无可靠训练结果证明 Tide 的 learning value、scaling value 或端到端系统收益。Flat MoE 的现实成功、checkpoint 函数保持和若干有界图性质属于已有依据；broadcast-observe、receiver 私有状态、多次局部选择、Head/Group-receiver 和多父交叉会聚的净收益仍是待验证命题。

## 1. 判断类型

本页使用五类判断，后续实验记录不得把它们互相替换。

| 类型 | 含义 |
| --- | --- |
| 已有证据 | 来自成熟模型、公开规模实验、本仓库证明或可形式检查性质 |
| 条件性刚需 | 在明确接受一组目标约束以后才能推出；不表示某个实现已有效 |
| 工程护栏 | 为降低 checkpoint 生长和训练风险采用的约束；不声称对所有 Tide Graph 必要 |
| 研究赌注 | 有明确动机、值得优先正面验证，但当前没有可靠实验结论的机制 |
| 可选干预 | 可因共同设计理由进入完整候选，或由已观察失败牵引的结构工具 |

探索实验可以联合使用多个研究赌注以寻找正面存在性信号；联合候选成功不能单独证明每个部件必要。单项因果主张必须补只改变关键因素的配对反事实。

## 2. 两条研究逻辑链

### 2.1 从终极目标到局部多跳扩展

~~~text
已有证据：Flat MoE 已证明大潜在容量
          可以与每 Token 少量昂贵激活同时成立
    ↓
目标约束：容量随节点数增长 + 统一有界入度/出度
          + 不依赖全局 router + 输入自适应
          + 全局昂贵计算超稀疏
    ↓
条件性刚需：多跳、逐级的局部容量扩展
            + 多次有界局部选择或等价分布式路由
            + 显式 active、message 和 depth budget
    ↓
新增风险：早期选择延长控制寿命、改变下游输入分布，
          私有状态还可能引入跨 Token 延迟信用链
    ↓
工程护栏：checkpoint 中性生长、always-on backbone、
          有界局部 selector、函数保持接口和 fixed merge
~~~

严格推出的是有界度的多跳局部扩展，不是某一棵规则树。规则层次递归离现有 checkpoint 较近，便于控制发散、收拢和证据变量，因此是首选工程与证据前置；line、lattice、mesh、多尺度 backbone 和其他局部 DAG 都可能成为后续形式。

### 2.2 从路径相关历史到 broadcast-observe

~~~text
结构事实：多级 selected-dispatch 使固定 receiver
          只保存与自身路径前缀相符的消息历史
    ↓
待验证风险：receiver exposure 变薄、私有状态彼此碎片化，
            可能削弱局部记忆和后续处理
    ↓
研究赌注 A：broadcast-observe + private state
            + Update/ExpensiveCompute 分离
研究赌注 B：有界多父局部会聚或交叉传播
    ↓
最终待验证：这些机制是否产生 learning/scaling value，
            并覆盖状态、通信、selector 和调度成本
~~~

receiver exposure 变薄不等于当前 hidden 被机械切碎。active child 仍可能收到已整合完整前缀的 parent hidden；结构直接决定的是固定 receiver 的私有状态只记录实际送达的 route-conditioned 历史。该差异是否损害任务相关信息，选择性历史是否反而促进专门化，以及 BO 是否值得成本，都必须由实验回答。

## 3. 当前组件定位

| 组件 | 当前定位 |
| --- | --- |
| 统一有界局部入度/出度与多跳扩展 | 在终极目标约束下的条件性刚需 |
| 多次局部选择与全局 active budget | 在无全局 router、输入自适应和超稀疏前提下的条件性刚需 |
| 规则层次递归 | checkpoint 进入一般局部 DAG 的工程与证据前置，不是唯一数学形式 |
| broadcast-observe | 工作流 B 的定义性核心和首要研究赌注，不是已证明的唯一解 |
| 私有持久状态与 later readout | 验证未激活期间积累的局部记忆以后有用所必需 |
| post-Update selector | 只在验证当次 Observe 改变当次选择时需要；BO 也可使用 pre-Update/content-only selector |
| always-on backbone 与 fixed merge | 首个 checkpoint 候选的强工程护栏；分别保留稳定主路径并限制显式控制寿命 |
| Head/Group-receiver | 规则局部发散—收拢骨架和配对实验载体，不是独立第三条主线 |
| 多父会聚、不等长路径、空间化 | 可进入完整候选，也可由真实失败牵引的干预 |
| 纯 FFN 递归 | 区分条件计算收益与私有序列状态收益的重要对照 |

## 4. Receiver 与传播语义

### 4.1 术语

receiver 是能够接收局部上游消息，并拥有自身参数或状态的下游模块。Attention readout、FFN、大型 SSM 更新等主体工作称为 ExpensiveCompute；消息投递、轻量 Observe 和状态写入必须单独计费，不能藏入 active FLOPs。

一次局部 receiver transition 至少分开：

1. Receive：哪些声明的 receiver 实际收到哪些消息。
2. Update：收到消息后如何更新 receiver-private semantic state。
3. Select：局部预算如何形成 active set。
4. Read/ExpensiveCompute：哪些 receiver 读取状态并执行昂贵计算。
5. Emit：哪些 receiver 产生输出并继续传播。
6. Merge：输出在何处按预声明算子收拢。

### 4.2 两种传播 profile

| Profile | 语义 | 实验角色 |
| --- | --- | --- |
| selected-dispatch | 先形成 active children；只有被选 children Receive、Update、Compute 和 Emit | 成熟 MoE 邻近基线和 BO 的直接反事实 |
| broadcast-observe | active sender 沿全部声明局部出边发送；实际 receivers 都 Observe/Update，只有 active receivers Compute/Emit | 工作流 B 正面候选 |

BO 只广播到 active sender 的直接静态后继。未激活祖先之后的远端节点不会自动看到全局数据。Receive 或 state change 也不表示状态已经被以后有效读出。

两种 profile 都可扩展到多父局部 DAG。多父语义必须额外声明 inbox 完整条件、消息顺序或结合归约、空消息、重复消息、state commit 和跨父预算仲裁。多父拓扑不强迫使用 BO，同一拓扑应尽可能支持两种 profile。

### 4.3 Fixed merge 的准确作用

fixed merge 结束的是当前 Token 在本段内的显式分支身份，并给出稳定输出接口。它不删除：

- 已合入共同 hidden 的数值语义影响。
- 已写入 private state 的跨 Token 影响。
- 当前选择对更深层输入分布的间接影响。

因此控制寿命、数值语义距离和 write-to-read 延迟必须分开记录。

## 5. 配置坐标

每个实验必须完整记录下列字段，不能只写 Tide、Leaf-Gated 或 Receiver-Gated：

| 字段 | 例子 |
| --- | --- |
| checkpoint 谱系与 growth operator | native、zero residual、zero output projection、clone-and-split |
| branch grammar | atomic、serial、recursive、equal-depth、mixed-depth |
| 门控范围 | leaf、receiver、head/group、internal subtree |
| propagation profile | selected-dispatch、broadcast-observe |
| receiver state | none、ephemeral summary、persistent KV/SSM/summary |
| selector 输入 | content、pre-Update state、post-Update state、history/load state |
| selector 决策 | fixed/hash、soft mixture、hard Top-K、quota/eligibility |
| Head/Group layout | group 数、projection/slice、private pool、slot 与 mixer |
| 预算 | fan-in/fan-out、每级 Top-K、全局 active/message/depth budget |
| merge/backbone | always-on 比例、merge 范围、mixer、控制寿命 |
| 物理放置 | receiver、state、selector 与 mixer 的设备/region 归属 |

同时改变多个字段的配置可以回答完整候选是否存在正面信号，不能单独支持任一字段的因果结论。

## 6. Head/Group-receiver 配对骨架

需要区分三种对象：

| 对象 | 定位 |
| --- | --- |
| Group-wise FFN MoE | 所有 groups 参与，每组在私有 FFN expert pool 内选 K；group 层面不稀疏，不等于 BO |
| Attention head-group | 固定 head groups；只有明确 K/V 所有权后才能成为独立有状态 receiver |
| Tide Group-receiver cell | 固定、有界 receivers；显式分离 Observe、Update、ExpensiveCompute 与 Emit |

当前核心 matched pair 使用同一 Group-receiver 骨架：

1. 工作流 A selected control：只有 active groups Receive/Update。
2. 工作流 B BO candidate：inactive groups 也 Receive/Update。

两边必须保持 group 数、projection/slice、固定 slots、昂贵算子、Update/readout、state 形状和生命周期、active group 数、递归拓扑、merge/mixer 与物理放置一致。最干净的配对使用相同或 replay route，核心差异只是 inactive receiver 是否 Receive/Update。

若 BO selector 读取 post-Update proposal/state，还必须增加读取与忽略该状态的内部对照。若一边使用 FFN、另一边改用 Attention/SSM，或同时改变 group layout 与 mixer，它们只是两个组合候选。

全维 dense mixer 可以作为 checkpoint 生长的表达恢复接口；若它每次都要求跨全部设备 collective，只能证明局部分支或稀疏计算可能有效，不能证明完整去中心化通信有效。

## 7. 两条并行工作流

### 7.1 共同原则

两条工作流共享数据、训练配方、correctness oracle、成本口径、checkpoint 谱系和 ExperimentLedger。dense equality 就绪后可以并行推进，不要求 flat MoE 全部完成后才允许工作流 B。

实验分为三类：

- 探索实验：允许最小但完整的机制包，只主张是否出现正面存在性信号。
- 诊断实验：针对已观察问题做 knockout、paired counterfactual 或局部修改。
- 确认实验：冻结结构与训练配方，用新 seed、数据切片、硬件或规模复现。

### 7.2 工作流 A：基线与校准

工作流 A 包含：

1. 原生 checkpoint equality 与 dense continued-pretraining oracle。
2. 一套成熟 flat MoE reference recipe 或兼容原生实现。
3. checkpoint-grown flat MoE matched control。
4. 与工作流 B 共骨架的 Group-receiver selected control。
5. 可选的原始 Group-wise FFN MoE 辅助结构对照。

只优于尚未合理调优的 checkpoint-grown MoE，不能声称优于成熟 flat MoE。

### 7.3 工作流 B：BO 完整候选

首个完整候选允许联合采用：

- 完整保留的 checkpoint 与 always-on backbone。
- 中性 residual 接口生长的有界 fan-out branches。
- 至少一组与工作流 A 完全配对的 Group-receiver BO。
- active sender 向全部固定局部 children 发送。
- inactive receiver 也可写入、以后可真正读出的 private state。
- 只协调固定局部候选的 selector。
- 少数 receiver 执行昂贵 readout/FFN/SSM 并继续传播。
- 声明的有界递归深度与 fixed merge/region interface。

一层或多层递归、Leaf/Receiver gating、多父会聚和不等长路径可以从一开始进入组合候选，不再受旧阶段编号禁止。若要支持容量随节点数增长且局部连接有界的主张，后续 scaling 实验必须进入多跳扩展，不能永远停在一跳 BO。

BO 的两条可能作用路径必须分别观测：

~~~text
当前 Observe/Proposal
-> 当前 active set 或输出改变
-> 阻断该输入会可复现地改变 output/loss
~~~

~~~text
inactive receiver 收到消息
-> private state 改变
-> 以后激活时真正读出
-> 阻断或扰动该 write/read 会改变 output/loss
~~~

只有消息送达、但既不改变当前 proposal/selection，也没有以后读出，只证明传播语义运行和产生成本，不证明 learning value。

## 8. 问题驱动的干预

下一项机制由已观察问题牵引，而不是由固定阶段号牵引。

| 观察 | 优先诊断 | 候选干预 |
| --- | --- | --- |
| receiver exposure 随深度过低且伤害记忆 | coverage、state knockout、记忆任务 | 有界多父会聚、backbone reinjection、merge 后重新发散 |
| route churn 与表示跳变相关 | route replay、soft/fixed control、branch delta | 增大 overlap、稳定 gate、缩短 merge interval |
| 激活均衡但梯度或 state use 低 | read sensitivity、梯度覆盖、no-read | 辅助 readout、局部 loss、预算或 selector 调整 |
| 早期选择错误随深度放大 | 层级 matched control、路径 attribution | shared/core path、较短控制寿命、局部交叉 |
| BO 系统成本过高 | 分项 profiler、Update-only control | 更小 summary、稀疏 Update、region-local placement |
| stateful selector 破坏低 span | reference replay、span audit | token-local/pre-state selector、scan-composable state |

cross-coupling 与 fixed convergence/reset 必须分开。前者扩大局部 source coverage 但保留路径身份；后者收回共同接口并结束旧路径身份。

## 9. 五道验收 gate

### 9.1 Correctness

- 原 checkpoint state-dict 覆盖、logits、原 cache/state、loss 和主要 backbone 梯度对齐。
- 函数保持初始化时旧模型可观察输出与原有状态轨迹对齐。
- prefill、逐 Token decode 与任意合法 chunk continuation artifact equality。
- batch 组合与物理调度不改变单序列 reference semantics。
- Receive/Update/Select/Read/Emit、空消息、多父聚合与 merge 顺序明确。
- propagation、topology、state、selector 配置均写入 checkpoint/config。
- fresh save/reload 后 route 与 state 可重放。

中性初始化只表示旧输出保持。新增 private state 可以形成自己的轨迹，但不得在中性期影响旧输出。零 gate 或零输出投影还必须记录新增参数何时获得梯度。

### 9.2 Mechanism-use

至少记录：

- receiver proposal 对当前 route 的敏感度。
- inactive receiver 的 receive/update 覆盖率和状态变化量。
- write-to-read Token 延迟。
- 后续 readout 对 private state 的敏感度。
- freeze、clear、shuffle、no-read、reset 等 knockout 的 output/loss 差异。
- post-Update state 分别对当前选择和昂贵分支输出的因果作用。

机制运行、learning value、scaling value 和系统 value 是四层不同结论。

### 9.3 Training 与 learning value

- train/validation loss、perplexity 与任务质量。
- route churn、active-set overlap、分支输出跳变量和输入分布漂移。
- Receive、Update、ExpensiveCompute、Emit、有效梯度五类次数分账。
- receiver/selector/backbone 梯度覆盖和长期未更新参数。
- 按 selector profile、Head/Group 和递归层级分组的状态利用与负载。
- 多 seed、数据切片和后续规模复现。
- capacity/data/FLOP/resource/quality-matched 强基线。

激活均衡不等于训练均衡；状态发生变化不等于状态被使用。

### 9.4 Scaling

- 在统一有界入度/出度下增加潜在节点数、参数、递归深度或空间直径。
- 分开报告总容量、实际到达节点、昂贵激活、Emit 边、Observe/Update 次数和 state 容量。
- 检查收益是否依赖增长 fan-out、全局 mixer 或近似稠密 Update。
- 记录 receiver exposure、route churn、梯度覆盖、state use、控制寿命与 write-to-read 延迟如何随深度变化。
- 与 capacity/compute/resource-matched dense 和 flat MoE 比较。

### 9.5 System

- 总参数、active parameters 与 actual FLOPs 分项。
- 消息、Observe/Update、selector、state I/O、Compute、packing 和 merge/mixer 分项。
- 训练吞吐、prefill 吞吐、decode latency、峰值内存和 optimizer state。
- 静态/动态通信邻接距离、collective 范围、等待时间和尾延迟。
- grouped GEMM/packed kernel 利用率与设备空闲比例。

系统收益至少要求：

~~~text
被跳过的昂贵计算与远程通信
>
局部广播 + Observe/Update + selector + state I/O + packing + merge
~~~

## 10. Reference 与软件边界

近期共同底座使用以下最小抽象：

| 接口 | 责任 |
| --- | --- |
| CheckpointAdapter | 原生装载、状态映射与 equality oracle |
| BranchModule | atomic、serial 或 recursive 的单入口/单出口 branch |
| MessageProjection | 固定有界 receiver slots、局部拓扑和消息形状 |
| ReceiverCell | Observe、Update、ExpensiveCompute 与 Emit |
| PropagationProfile | 产生 receive、update、active、read 与 emit artifacts |
| SiblingSelector | 在固定局部候选中分配 active budget |
| StateUpdater | semantic/load state 更新、持久范围和空输入规则 |
| ReceiverState | receiver-private semantic state，支持 reset/save/reload |
| SelectorState | sibling-level、逐序列 history/load state |
| FixedMerge | 固定 slots、范围与算子 |
| RouteArtifact | 按 Token、parent、Head/Group、递归层记录五类 mask/artifact |
| ExperimentLedger | 谱系、配置、预算、数据、checkpoint、指标与结论边界 |

ReceiverState 与 SelectorState 必须分开，物理 runtime 负载不得混入模型语义状态。第一版底座不需要一般 Event IR executor、HB-Line executor、跨设备 allocator 或有环 Graph。

## 11. 首个交付

1. 选定可快速重复实验的 pre-norm decoder-only 开放权重 checkpoint、数据、框架和硬件。
2. 完成原生 equality oracle、continued-pretraining 校准和 fresh save/reload。
3. 同一拓扑可切换 selected-dispatch/BO、持久/无延迟状态和各类 knockout。
4. 工作流 A 建立 dense、成熟 flat MoE、checkpoint-grown MoE 和 Group-receiver selected control。
5. 工作流 B 建立一个含 BO、later-read private state、局部 sparse compute、always-on backbone 与 fixed merge 的机制完整候选。
6. 完成短程训练并输出 correctness、mechanism-use、质量、路由、梯度、状态利用、路径和系统成本报告。

成功标准是实验可重放、语义完整、问题可观测且关键反事实可运行；首轮不要求证明 Tide 有效。

## 12. 当前不能主张

- BO 已有 learning、scaling 或系统收益。
- 收到消息或 state change 就等于 later readout 有效。
- receiver exposure 变薄必然等于当前 hidden 丢失上下文。
- 多父会聚必然恢复无损记忆或解决路径漂移。
- 联合候选成功分别证明所有部件必要。
- 规则递归是一般 Graph 的唯一扩展形式。
- fixed merge、always-on backbone 或某个 mixer 对所有 Tide 必要或最优。
- Head/Group-wise 已成功融合进 Tide，或分组本身证明去中心化通信。
- 逻辑邻接局部自动带来物理通信局部和更低延迟。
- 任意 stateful selector 都具有高性能 chunk prefill。

## 13. 维护与同步

本页的初始实验政策来自 tide 仓库 fractal-latcarf 分支提交：

- revision：19999de069fa15c39b7bbf2e46db33c723c3b456
- stable source：https://github.com/ZichaoLong/tide/blob/19999de069fa15c39b7bbf2e46db33c723c3b456/README.md

后续维护规则：

1. 研究理由、证据分级、配置轴和 gate 先更新本页。
2. 实验仓库 README 维护面向开发者的当前实现入口，并记录所依据的 Vault revision。
3. 实验结果写入 ExperimentLedger 或独立结果文档，不把设计理由原地改写成已有证据。
4. 数学文档只有在对象、定义域、状态转移和证明完成后才升级相应结论。
