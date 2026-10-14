---
type: semantic-version-record
status: active
semantic-version: tide-core-5
as-of: 2026-10-14
tags:
  - tide
  - semantic-version
---

# 语义版本差异与下游采用

本页集中记录版本差异、教材修订和下游采用信息。数学定义见[语义锚点](semantics-anchor.md)所列教材。

## 简短差异

| 版本或修订 | 变化 | 下游核对事项 |
|---|---|---|
| 2026-10-14 KV 非空选择，沿用 tide-core-5 | 有效候选非空时至少激活一个；软质量下限为 $\min(1,\sum_v\mu_v)$，硬选择在全低分时保留最高分候选；同步手算、连续性证明、投影反向及架构计数 | 正典及共同签名不变，KV 数值语义改变。核对上下质量界、零上界、全低分与单候选、$k_j=1$ 的阈值无关性及逐情形硬化间隔；全连接每层全部节点写入，当前 HB 每位置所有区域到达。本次未验证下游采用 |
| 2026-10-13 KV 选择族与 HB 组合，沿用 tide-core-5 | 聚合增加节点／来源特化绑定；时间摘要／内容检索与独立／区域 Attention 评分组成四个选择，共用预算和 Full；新增多区域展开收拢的 HB 实例，补充投影反向、固定图证明与全图成本 | 正典及共同签名不变。原 KV 数值对应区域共享聚合、时间摘要与独立评分；其他选择须按描述空间成对绑定 Read／SelStep。核对弱候选对 query 的影响、检索零极限、自由区梯度、HB 候选覆盖和分块记录；本次未验证下游采用 |
| 2026-10-13 KV 位置与继续修订，沿用 tide-core-5 | 局部函数增加固定 Pos、NoPE／完整及部分 RoPE，窗口与摘要率可逐节点声明，窗口允许全部接收历史；分层实例逐区域组合，连续性正式证明与实现验证要求集中到局部教材附录 | 四篇正典及共同签名保持不变。旧数值配置对应恒等 Pos、零旋转维数及原窗口、衰减和距离斜率；采用 RoPE 等新配置会改变局部数值。核对原始时间、旋转表示、弱消息及硬化条件、整段／分块／decode 一致性；未声明下游已采用 |
| 2026-10-12 KV 文档分工，沿用 tide-core-5 | 局部函数、连续性和批量契约保留在原 KV 文档；分层拓扑、时间与端口绑定、模型接入和训练目标集中到分层架构实例 | 函数与既有架构语义保持；组合时分别引用局部定义和结构绑定。局部公式重新编号；训练方案见新实例 §4，下游采用状态保持原记录 |
| tide-core-5（2026-10-12） | SettleGraph 完整沿用 TimedDAG 的空间、原子集合、局部签名及逐边／逐端口返回族；单次结算由严格分层和时间对齐给出。共同输入、广播和终端读出归为局部实例 | SettleGraph 绑定独立 $X_v$；单一载荷函数命名 EmitValue，Full 取广播提升或直接返回两个值族；保留平行边及一般端口。旧记录须按声明的边界映射比较 |
| 2026-10-12 教材重整 | 保留 TimedDAG 的 P/S/U/F 结果元组，区分调用标签与结果；统一区间转导 Phi、记录粘合、块名称与表示解码 | Next 的旧状态须显式保留；区间数值输入不含关闭证明，共享边界只识别一次；BatchRegionState 只含 P/S/U，含 Full 时为 BatchRegion；Decode 后再作遗忘投影 |
| tide-core-3 | 聚合输入保留入口、父边、终端或端口的来源标签 | 聚合参数保留来源；裸值聚合通过忽略标签表达 |
| tide-core-4 | SettleGraph 激活容量取上界，允许少选与空选择；无激活终端时输出槽为 $\bot$ | 覆盖非空候选但空选择、未激活候选状态更新、缺席输出及编码恢复。旧选满规则仍是具体选择函数 |
| 2026-10-10 教材修订，沿用 tide-core-4 | 统一局部函数与块接口；补齐变化支持集、普通作用覆盖及关闭依赖 | 核对边界、返回记录、调用条件及下述名称对应；核心局部递归与切面状态定义保持 |
| 2026-10-10 带权 KV 架构修订，沿用 tide-core-4 | 特例具体化为来源聚合、时间窗口 KV、多尺度评分、可弃权预算选择与 Attention／前馈残差；补充训练目标与成本分析 | 局部函数已有变化，旧特例的数值不能直接沿用；连续性按有效时间窗口状态比较，硬化条件增加弃权阈值间隔。本次仅修订上游设计，未验证下游采用 |

tide-core-5 保持 TimedDAG 与 PositiveDelayGraph 的局部函数、参数顺序和作用结果不变，扩大 SettleGraph 可表达的实例范围。2026-10-12 的核心修订保留了当时的 KV 数值函数，三个层级统一使用 Full = Delta ∘ EmitValue 和端口记录读出；后续 KV 配置变化由上表单独记录。分层基线直接在终端端口产生记录，外部汇集不另造图内输出事件。旧输入／输出适配节点可以显式保留为一种边界配置，但不能据新旧原始记录的无映射比较宣称一致。

名称对应按修订列出：

- 2026-10-12：事件边统一为 $\mathscr A^{\mathrm{ev}}$，发送前缀为 $M_{<b}^{\mathrm{send}}$；单步下一状态为 $q^{\mathrm{next}}$，位置边界状态为 $q_v^{[t]}$；阶段数统一为 $R$。旧 Run 区间函数对应 Phi；StatePath 仍只返回状态轨迹。
- 2026-10-10：Choose 统一为 Allowed；块输出与参考函数统一为 BlockOut、RefBlock；联合契约归属为 ContractOwner/cown，作用归属仍为 own。PublishedDoneTo 包含消息已纳入的条件。BatchFull 经 ExpandFull 返回规范块记录。

tide-core-4 的引入提交为 [d60d1cf](https://github.com/ZichaoLong/ObsidianVault/commit/d60d1cf)。教材勘误及符号整理由采用的不可变提交精确定位；涉及允许的核心行为变化时另记语义版本。新增特例可以在同一核心版本下独立演进。

## 下游采用记录

采用声明与符合性验证分别记录；本表保留有日期和来源的信息。

| 下游 | 采用声明 | 依据与范围 | 符合性证据 |
|---|---|---|---|
| [graph-execution-foundation](https://github.com/ZichaoLong/tide/tree/graph-execution-foundation) | tide-core-3；已包含若干局部模块特化，带权 KV 特例尚未实现 | 2026-10-10 维护者在本次文档修订中说明；本地目录为 ~/llm/graph-execution-foundation | 由下游固定提交、检查及报告给出；本次文档修订未审计其实现 |
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

## 来源与迁移材料

SettleGraph 的早期定义参考了 fractal-latcarf 的实验语义文档。历史名称、旧资料与目录迁移见 [迁移索引](memos/history/migration-map.md) 和 [LH 历史](memos/history/lh-history.md)。

学习资源的早期书目来自 `133d638:20-tide-decentralized-neural-network/appendices/tide-directed-learning-roadmap.md`。

TIDE 的历史全称为 Topology-Invariant Degree-bounded Expansion Architecture for Autoregressive Token Inference。目录名保留既有链接；架构与数学含义以教材定义为准。
