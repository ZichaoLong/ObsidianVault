---
type: semantic-version-record
status: active
semantic-version: tide-core-4
as-of: 2026-10-10
tags:
  - tide
  - semantic-version
---

# 语义版本差异与下游采用

本页集中记录版本差异、教材修订和下游采用信息。数学定义见[语义锚点](semantics-anchor.md)所列教材。

## 简短差异

| 版本或修订 | 变化 | 下游核对事项 |
|---|---|---|
| tide-core-3 | 聚合输入保留入口、父边、终端或端口的来源标签 | 聚合参数保留来源；裸值聚合通过忽略标签表达 |
| tide-core-4 | SettleGraph 激活容量取上界，允许少选与空选择；无激活终端时输出槽为 $\bot$ | 覆盖非空候选但空选择、未激活候选状态更新、缺席输出及编码恢复。旧选满规则仍是具体选择函数 |
| 2026-10-10 教材修订，沿用 tide-core-4 | 统一局部函数与块接口；补齐变化支持集、普通作用覆盖及关闭依赖 | 核对边界、返回记录、调用条件及下述名称对应；核心局部递归与切面状态定义保持 |
| 2026-10-10 带权 KV 架构修订，沿用 tide-core-4 | 特例具体化为来源聚合、时间窗口 KV、多尺度评分、可弃权预算选择与 Attention／前馈残差；补充训练目标与成本分析 | 局部函数已有变化，旧特例的数值不能直接沿用；连续性按有效时间窗口状态比较，硬化条件增加弃权阈值间隔。本次仅修订上游设计，未验证下游采用 |

名称对应：Choose 统一为 Allowed；块输出与参考函数统一为 BlockOut、RefBlock；联合契约归属为 ContractOwner/cown，作用归属仍为 own。PublishedDoneTo 明确包含消息已纳入的条件。BatchFull 经 ExpandFull 返回规范块记录；带权 KV 通过 EmitValue 与广播提升绑定 Full。

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
