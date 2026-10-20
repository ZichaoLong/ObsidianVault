---
type: semantic-version-record
status: active
semantic-version: tide-core-5
as-of: 2026-10-20
tags:
  - tide
  - semantic-version
---

# 语义版本差异与下游采用

本页记录影响采用的语义差异、配置迁移与有来源的采用声明。数学定义见[接口索引](../reference/semantic-interface-index.md)所列教材；编辑历程见[文档修订记录](history/document-revisions.md)。

## 核心语义

| 版本 | 变化 | 采用时核对 |
|---|---|---|
| tide-core-3 | 聚合输入保留入口、父边、终端或端口的来源标签 | 保留来源；裸值聚合由忽略标签表达 |
| tide-core-4 | SettleGraph 激活容量取上界，允许少选与空选择；缺席终端输出为 $\bot$ | 空激活、未激活候选的状态作用、缺席输出与编码恢复 |
| tide-core-5 | SettleGraph 沿用 TimedDAG 的独立 $X_v$、原子集合、局部签名及逐边／逐端口返回族；以严格分层和时间对齐给出单次结算 | 保留平行边与一般端口；广播取 $\operatorname{Full}=\Delta\circ\operatorname{EmitValue}$；旧记录按明确边界映射比较 |

tide-core-5 保持 TimedDAG 与 PositiveDelayGraph 的局部函数、参数顺序和作用结果。局部特化可独立演进；核心版本与采用的不可变提交共同定位定义。

## 局部支线的采用要点

| 修订 | 影响 |
|---|---|
| 2026-10-14 非空约束分配 | 数值语义改变：总发送下限为 $\min(1,\sum_v\mu_v)$；配对硬函数在全低分时保留最高分候选 |
| 2026-10-17 稠密 Attention | 增加 direct 与固定总强度 attention；各自的发送上限、零边界和总量性质分别使用，整网软硬极限仅覆盖约束分配与配对硬函数 |
| 2026-10-19 模块组合 | 分开 memory_family、memory_read、region_score 与 selection_mode；增加循环模块、received 权重、pooled 和 Read 模式组合。既有默认数值保持，迁移见下表 |
| 2026-10-20 定理整理与勘误 | 既有函数及默认数值保持。整网定理移到共同架构 §6 和附录 A，记忆模块验证局部条件；修正区域分配 §5.3／附录 A.2 中应使用第二名评分 $t_{(2)}$ 的有限温度条件，旧 $t_{(4)}$ 条件不足 |
| 2026-10-20 反向与零消息条件勘误 | 函数定义保持。quad 总和松弛时使用独立响应导数；固定总强度 mu 支持零消息删除，uniform 须区分缺席与零消息；softmax 的前向等值与边界反向分别判定。下游核对范围见实现检查 §3、§5 |
| 2026-10-20 目录分层与拓扑拆分 | 核心版本、局部函数与配置取值保持。拓扑定义独立，实例引用图和函数形成完整绑定；下游更新正文路径，并区分通用图结论与依赖局部绑定的性质 |
| 2026-10-20 定义顺序与正典引用边界 | 局部函数及默认数值保持，配置名称和局部符号按下表迁移。共同架构补入有限正温度精确运行推论。四份正典清除向下引用，PDG 的有限检验段落改为自足说明；其数学定义、公式、命题与证明保持 |
| 2026-10-20 完整循环记忆候选 | 增加 memory_family=gated_delta／ssd 与固定逻辑时间短卷积；给出完整局部函数、状态引理、原模型对应、两类拓扑绑定和实现核对。既有 affine／delta／kv、评分与发送函数保持；本轮四份正典逐字保持 |

截至 [e6f5513](https://github.com/ZichaoLong/ObsidianVault/commit/e6f5513) 的目录与局部整理保持四份正典原文；随后引用清理的逐篇差异见[修订记录](history/document-revisions.md#2026-10-20定义顺序与正典引用边界)。局部 Attention 份额使用 $p_v^{\mathrm{sel}}$，标量响应及导数使用 resp 上标。旧路径的直接落点见[迁移索引](history/migration-map.md#2026-10-20-移除转向入口)。

## 完整循环候选的采用范围（2026-10-20）

核心版本继续为 tide-core-5。基础 delta 没有被重命名或替换；新配置选择不同的状态、参数和数值函数。memory_read=state 在新模块中表示短期摘要与矩阵查询两个通道，具体定义见相应教材 §3。

| 新配置 | 定义与对应范围 | 下游需新增的内容 |
|---|---|---|
| gated_delta | [Gated DeltaNet 局部教材](../local-semantics/weighted-message/gated-delta-memory-learning-note.md)，等间隔单位接收下对照 FLA [9d478fac](https://github.com/fla-org/flash-linear-attention/tree/9d478facb282410dc150051d5f57205cd3812f31) 指定开关的记忆混合器 | 多头矩阵、Q/K/V 短卷积、L2、保留／写入／输出门、逐头输出 RMS、描述与完整状态 |
| ssd | [SSD 局部教材](../local-semantics/weighted-message/ssd-memory-learning-note.md)，等间隔单位接收下对照 Mamba [e9594ce1](https://github.com/state-spaces/mamba/tree/e9594ce1c732d97440f0332fdc43170a2294dbfa) 的 Mamba2Simple | x/B/C 短卷积、头组映射、标量门与 dt 写入、D 直通、先门控后整体 RMS |
| conv_size／conv_stride | [固定时间短卷积](../local-semantics/weighted-message/causal-convolution-learning-note.md)的抽头数与逻辑步长 | 原始时间槽、带权历史、快照重建、空档与分段状态；分层绑定的步长为 $D$ |

对原模型的对应是指定实数公式与参数形状的对应；源码版本、门开关、归一化常数及参考输入由各教材附录 S 固定。带权接收、逻辑空档、selector 摘要与图广播为 Tide 的显式适配。旧模型的缓存不自动成为新模型从头运行的状态，切换配置后的继续须重算或声明转换。

本次未审计下游对新候选的支持，也未做训练、吞吐或 GPU 内核一致性验证。实现核对集中在[记忆模块检查](../reference/weighted-message-implementation-checks.md#4-记忆模块)，论文证据与推断边界集中在[设计总览](../memos/design/weighted-message-design.md#8-外部证据)。

## 局部名称迁移（2026-10-20）

以下名称替换保留原来的数值函数、参数值及默认选择；核心版本仍为 tide-core-5。

| 旧名称 | 当前名称 | 所指函数或参数 |
|---|---|---|
| selection_mode=soft | selection_mode=constrained | 约束分配，包含稠密与可稀疏的正则族 |
| selection_mode=direct | selection_mode=direct_attention | 直接 Attention |
| selection_mode=attention | selection_mode=unit_attention | 固定总强度 Attention |
| selection_mode=pooled | selection_mode=pooled_attention | 区域总量分配 |
| selection_mode=dense | selection_mode=proportional | 按比例分配 |
| selection_mode=hard | selection_mode=hard_selection | 硬选择 |
| budget_family | regularizer | 约束分配的正则函数 |
| tau_soft | allocation_temperature | 发送分配的温度 |
| 局部接收强度 $r,r_v$ | $r^{\mathrm{in}},r_v^{\mathrm{in}}$ | 与正典的节点秩 $r_v$ 分开 |
| 局部激活集合 $A$ | $\mathcal A$ | 与图的边集 $A$ 分开 |
| 分配温度 $\tau_{\mathrm{soft}}$ | $\tau_{\mathrm{sel}}$ | 与正典读取模式 $\tau_j$ 分开 |

下游旧配置按表映射；新旧键同时出现时检查数值一致或拒绝冲突。函数完整定义及参数适用范围见[区域分配附录 S.1](../local-semantics/weighted-message/region-allocation-learning-note.md#s1-配置名称)。有限正温度推论只覆盖满足条件的 quad 与固定 $\alpha>1$ 的 ent；它补充已定义函数的性质，未改变任何分配规则。

## 局部配置迁移（2026-10-19）

下表保留该次修订的名称；其中的发送模式再按上节迁移为当前名称。

| 既有名称或类型 | 该次修订的对应 | 数值与采用说明 |
|---|---|---|
| memory=sum／qry | memory_family=kv，memory_read=sum／qry | 区分状态类型与描述读取，保留原读取函数 |
| attention_base=uniform／reception | selection_mode=attention，allocation_base=uniform／mu | 旧 reception 使用的是 $\mu$，包括增益；数值保持 |
| direct 未声明基权重 | allocation_base=mu | 保留原直接 Attention；received 是使用 $w$ 的新增分支 |
| att 未声明 query 权重 | query_weight=mu | 保留原 query；received 为新增分支 |
| KV 固定 Read$^+$ | read_mode=+ 为默认，可另取 -／0 | 既有默认数值保持；模式改变属于新组合 |
| $D^{\mathrm{ind}}=(\mu,s)$、$D^{\mathrm{att}}=(\mu,x,K,s)$ | 分别在首位加入 $w$ | 支持 query 与份额读取接收量。只采用 mu 分支的旧表示可保留；适配时 $w$ 从本次聚合取得，不能一般由 $\mu$ 反推 |

共同载荷与六个正典签名保持，局部描述空间的具体绑定扩充。下游兼容解析若同时收到新旧键，须检查对应一致或拒绝冲突；不可把旧 reception 解释成 received。正温度连续性新增覆盖 pooled、dense 及 received 分支，硬化定理仍仅比较约束分配与原硬函数。循环模块采用自己的状态投影与时间规则。

## 下游采用记录

采用声明与符合性验证分别记录；本表保留有日期和来源的信息。

| 下游 | 采用声明 | 依据与范围 | 符合性证据 |
|---|---|---|---|
| [graph-execution-foundation](https://github.com/ZichaoLong/tide/tree/graph-execution-foundation) | tide-core-3；已包含若干局部模块特化，带权 KV 特例尚未实现 | 2026-10-10 维护者说明（当日记录）；本地目录为 ~/llm/graph-execution-foundation | 由下游固定提交、检查及报告给出；本次文档修订未审计其实现 |
| fractal-latcarf | 具体采用范围由实验记录声明 | SettleGraph 实验平台，维护模块、模型接入和训练设置 | 以该平台的版本对应和实验报告为准 |

## 下游引用

每份采用声明记录：

| 字段 | 内容 |
|---|---|
| upstream repository | https://github.com/ZichaoLong/ObsidianVault |
| upstream revision | 采用的不可变提交 |
| semantic version | 核心语义版本 |
| adopted family | PositiveDelayGraph、TimedDAG 或 SettleGraph，以及附加条件 |
| local choices | 局部函数、尺寸、初态、输入日程、聚合、发送、状态和读出 |
| local extensions | 改变公共函数类型或依赖关系的内容 |
| validation | 比较对象、投影、数值容差、固定提交和验证结果 |

离线副本保留来源与提交，从上游单向更新。具体实现的最新支持范围和验证结果由下游维护；上游保留一般定义、证明与教学参考程序。

## 来源

SettleGraph 的早期定义参考了 fractal-latcarf 的实验语义文档。早期材料与来源见[迁移索引](history/migration-map.md)、[LH 历史](history/lh-design-origins.md)和[文档修订记录](history/document-revisions.md)。TIDE 的历史全称为 Topology-Invariant Degree-bounded Expansion Architecture for Autoregressive Token Inference。
