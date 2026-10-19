---
type: research-memo-index
status: active-index
tags:
  - tide
  - index
---

# Tide 研究备忘

这里保存数学补充、机制取舍、学习风险、实验方案、外部背景和 LH 历史。数学入口见 [Tide 主入口](../README.md)。局部函数以相应教材为定义来源；研究候选、对照方案和外部证据在备忘中分别说明，具体实现与实验结果由下游维护。

## 数学补充

- [局部架构](../local-architecture-learning-note.md)：共同带权消息、状态与控制的组合定义。
- [区域分配](../region-allocation-learning-note.md)：评分、发送、梯度及局部连续性与极限。
- [KV 记忆](../weighted-kv-sparse-activation-example.md)、[循环记忆](../recurrent-memory-learning-note.md)：完整状态模块及证明。
- [全连接实例](../weighted-kv-layered-example.md)、[HB 实例](../weighted-kv-hb-lattice-example.md)：图与时间绑定、异构记忆组合和成本。
- [函数保持生长](mathematics/function-preserving-growth.md)：投影 simulation、中性 residual、有限 DAG 细化及受限 fixed-merge 闭包。
- [来源、聚合与读出](mathematics/provenance-and-readout.md)：安全商、保守依赖集合与未来可观察行为。
- [自适应路由下界](mathematics/adaptive-routing-prefill-lower-bound.md)：自足的 deterministic exact 黑盒查询模型与证明；不能直接当作任意具体 selector 的下界。

## 机制与学习风险

- [局部架构设计总览](architecture/selector-and-memory.md)：整体能力、依赖路径、候选取舍和可修正的研究判断，外部证据及适用范围。
- [学习风险与诊断](learning-systems/learning-risks-and-diagnostics.md)：跨架构的路径漂移、信用距离、粒度与状态负担、饥饿及辅助监督。

## 实验与实现对应

- [可选研究问题与对照](learning-systems/weighted-kv-experiment-plan.md)：按问题选取的比较、观测和训练目标，具体安排由研究者决定。
- [局部架构：实现核对](../weighted-kv-implementation-checks.md)：数学定义、分段导数、连续性、位置和继续关系的程序证据。

## 外部背景

- [人脑信号传播调查](background/neuroscience-survey.md)：保留 2026-07-22 调查的解剖、生理与文献实质。
- [脑科学启发与边界](background/neuroscience-model-ideas.md)：将调查中的事实转成可检验的数字模型问题。
- [编译器与 dataflow](background/compiler-and-dataflow.md)：ISA、SSA、抽象解释、验证、KPN/SDF、logical progress 与 provenance。
- [统计力学与信息动力学](background/statistical-mechanics.md)：路径相关、路由熵与宏观极限的候选研究。

## LH 历史与资源

- [LH 历史位置](history/lh-history.md)：带日期的早期实现与语义设计来源。
- [按问题选读的资源](../resources/learning-resources.md)：书目与小练习，无强制课程门槛。

## 使用与维护

共同框架以正典教材为准，局部函数及其定理由局部教材定义，实例绑定图与边界。备忘给出补充推导、机制假设、训练方案、背景调查和历史线索。阅读时区分教材实例、有前提的局部推导、核心之外的扩展问题、经验假设与外部类比。历史来源与追溯入口见 [版本与采用说明](../semantic-versions.md)。
