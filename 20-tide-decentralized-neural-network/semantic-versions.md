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

本页记录影响采用的语义差异、配置迁移与有来源的采用声明。数学定义见[接口索引](semantic-interface-index.md)所列教材；编辑历程见[文档修订记录](memos/history/document-revisions.md)。

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

2026-10-20 的四份正典逐字保持。局部 Attention 份额统一写作 $p_v^{\mathrm{sel}}$，标量响应及导数使用 resp 上标，避免与记忆描述和评分向量混用。文件更名与兼容入口见[迁移索引](memos/history/migration-map.md#2026-10-20-路径与内容归属)。

## 局部配置迁移（2026-10-19）

| 既有名称或类型 | 当前对应 | 数值与采用说明 |
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

SettleGraph 的早期定义参考了 fractal-latcarf 的实验语义文档。早期材料与来源见[迁移索引](memos/history/migration-map.md)、[LH 历史](memos/history/lh-history.md)和[文档修订记录](memos/history/document-revisions.md)。TIDE 的历史全称为 Topology-Invariant Degree-bounded Expansion Architecture for Autoregressive Token Inference。
