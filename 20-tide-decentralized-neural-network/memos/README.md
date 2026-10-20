---
type: research-memo-index
status: active-index
tags:
  - tide
  - index
---

# Tide 研究备忘

备忘保存补充定理、设计分析、研究问题、外部背景和历史材料。正典、局部模块与组合实例的阅读路线见[教材入口](../README.md)；具体局部函数以相应教材为准。

## 设计与研究

| 文档 | 职责 |
|---|---|
| [局部架构设计总览](architecture/local-architecture-design.md) | 设计能力、依赖路径、候选取舍、外部证据与可修正的判断 |
| [学习风险与诊断](learning-systems/learning-risks-and-diagnostics.md) | 跨架构的路径漂移、信用距离、状态负担、饥饿与干预机制 |
| [可选研究问题与对照](learning-systems/local-architecture-research-questions.md) | 按问题取用的训练目标、对照、观测和结果解释 |

设计总览用于掌握整体；诊断用于解释学习现象；研究问题用于安排具体比较。实施的优先级与结论由研究者和下游记录。[实现核对](../local-architecture-implementation-checks.md)单独检查所实现的函数与数学定义是否一致。

## 数学补充

| 文档 | 对象与结论 |
|---|---|
| [函数保持生长](mathematics/function-preserving-growth.md) | 投影 simulation、中性 residual、有限 DAG 细化及受限 fixed-merge 闭包 |
| [来源、聚合与读出](mathematics/provenance-and-readout.md) | 安全商、保守依赖集合与未来可观察行为 |
| [自适应路由下界](mathematics/adaptive-routing-prefill-lower-bound.md) | 确定性精确黑盒查询模型的轮数下界、完整证明及向具体模型转用的条件 |

这些材料在各自声明的模型内给出结论。局部架构的函数与组合定理仍由[局部教材](../local-architecture-learning-note.md)承担。

## 外部背景

- [人脑信号传播调查](background/neuroscience-survey.md)：解剖、生理与文献事实。
- [脑科学启发与边界](background/neuroscience-model-ideas.md)：由调查提出的数字模型问题。
- [编译器与 dataflow](background/compiler-and-dataflow.md)：程序表示、验证、通信模型与逻辑进展。
- [统计力学与信息动力学](background/statistical-mechanics.md)：路径相关、路由熵与宏观极限的候选研究。
- [学习资源](../resources/learning-resources.md)：按问题选读的书目与练习。

## 历史与追溯

- [版本差异与下游采用](../semantic-versions.md)：当前迁移要点、采用声明与引用方式。
- [文档修订记录](history/document-revisions.md)：带日期的编辑过程与旧章节线索。
- [内容迁移索引](history/migration-map.md)：旧文件的现行落点。
- [LH 历史](history/lh-history.md)：早期实现与语义设计来源。
