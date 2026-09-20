---
type: research-memo-index
status: active-index
tags:
  - tide
  - index
semantic-baseline: tide-core-3
---

# Tide 研究备忘

这里保存核心教材之外的数学补充、机制与学习风险、外部背景和 LH 历史。数学入口见 [Tide 主入口](../README.md)；备忘中的候选不会自动修改 Graph、TimedDAG 或 SettleGraph 的定义。具体模块配置、实现等价性、训练和性能结果由实验仓库维护。

## 数学补充

- [函数保持生长](mathematics/function-preserving-growth.md)：投影 simulation、中性 residual、有限 DAG 细化及受限 fixed-merge 闭包。
- [来源、聚合与读出](mathematics/provenance-and-readout.md)：安全商、保守依赖集合与未来可观察行为。
- [自适应路由下界](mathematics/adaptive-routing-prefill-lower-bound.md)：自足的 deterministic exact 黑盒查询模型与证明；不能直接当作任意具体 selector 的下界。

## 机制与学习风险

- [Selector 与局部记忆](architecture/selector-and-memory.md)：评分、历史、衰减、恢复和清理的机制动机与设计风险。
- [学习风险与诊断](learning-systems/learning-risks-and-diagnostics.md)：路径漂移、信用距离、粒度与状态负担、饥饿、辅助监督和机制对照。内容是实验前假设与诊断建议。

## 外部背景

- [人脑信号传播调查](background/neuroscience-survey.md)：保留 2026-07-22 调查的解剖、生理与文献实质。
- [脑科学启发与边界](background/neuroscience-model-ideas.md)：将调查中的事实转成可检验的数字模型问题。
- [编译器与 dataflow](background/compiler-and-dataflow.md)：ISA、SSA、抽象解释、验证、KPN/SDF、logical progress 与 provenance。
- [统计力学与信息动力学](background/statistical-mechanics.md)：路径相关、路由熵与宏观极限的候选研究。

## LH 历史与资源

- [LH 历史位置](history/lh-history.md)：带日期的早期实现与语义设计来源，不是当前能力声明。
- [按问题选读的资源](../resources/learning-resources.md)：书目与小练习，无强制课程门槛。

## 使用与维护

对象定义、证明和正式能力声明以正典教材为准；备忘只提供局部推导、机制假设、背景调查和历史线索。阅读时区分教材实例、有前提的局部推导、核心之外的扩展问题、经验假设与外部类比。旧内容的去向和 Git 追溯方法见 [迁移索引](history/migration-map.md)；它是维护资料，不属于主要阅读路线。
