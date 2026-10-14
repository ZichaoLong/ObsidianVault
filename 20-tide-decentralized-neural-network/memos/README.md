---
type: research-memo-index
status: active-index
tags:
  - tide
  - index
---

# Tide 研究备忘

这里保存核心教材之外的数学补充、机制与学习风险、外部背景和 LH 历史。数学入口见 [Tide 主入口](../README.md)，版本差异见 [独立说明](../semantic-versions.md)；备忘中的候选不会自动修改 Graph、TimedDAG 或 SettleGraph 的定义。选定的模块、架构与训练机制可在上游局部实例中给出完整函数定义；具体实验配置、实现等价性、训练和性能结果由下游维护。

## 数学补充

- [[weighted-kv-sparse-activation-example|带权 KV 局部教材]]：三层共同的聚合、带权记忆、时间摘要／内容检索及独立／区域 Attention 评分，含保证有效候选非空选择的预算函数、连续性证明、全图成本与批量契约。
- [[weighted-kv-layered-example|带权 KV 的全连接分层实例]]：拓扑、时间与边界绑定，语言模型接入、训练目标和架构成本。
- [[weighted-kv-hb-lattice-example|带权 KV 的 HB-Lattice 实例]]：先展开再收拢的多区域邻域图，局部函数组合、候选传播和成本比较。
- [函数保持生长](mathematics/function-preserving-growth.md)：投影 simulation、中性 residual、有限 DAG 细化及受限 fixed-merge 闭包。
- [来源、聚合与读出](mathematics/provenance-and-readout.md)：安全商、保守依赖集合与未来可观察行为。
- [自适应路由下界](mathematics/adaptive-routing-prefill-lower-bound.md)：自足的 deterministic exact 黑盒查询模型与证明；不能直接当作任意具体 selector 的下界。

## 机制与学习风险

- [Selector 与局部记忆](architecture/selector-and-memory.md)：聚合共享、记忆检索、区域匹配、动态路径与状态机制的动机和取舍。
- [学习风险与诊断](learning-systems/learning-risks-and-diagnostics.md)：路径漂移、信用距离、粒度与状态负担、饥饿、辅助监督、带权 KV 的退火实验和机制对照。内容是实验前假设与诊断建议。

## 外部背景

- [人脑信号传播调查](background/neuroscience-survey.md)：保留 2026-07-22 调查的解剖、生理与文献实质。
- [脑科学启发与边界](background/neuroscience-model-ideas.md)：将调查中的事实转成可检验的数字模型问题。
- [编译器与 dataflow](background/compiler-and-dataflow.md)：ISA、SSA、抽象解释、验证、KPN/SDF、logical progress 与 provenance。
- [统计力学与信息动力学](background/statistical-mechanics.md)：路径相关、路由熵与宏观极限的候选研究。

## LH 历史与资源

- [LH 历史位置](history/lh-history.md)：带日期的早期实现与语义设计来源。
- [按问题选读的资源](../resources/learning-resources.md)：书目与小练习，无强制课程门槛。

## 使用与维护

对象定义、证明和正式能力声明以正典教材为准；备忘只提供局部推导、机制假设、背景调查和历史线索。阅读时区分教材实例、有前提的局部推导、核心之外的扩展问题、经验假设与外部类比。历史来源与追溯入口见 [版本与采用说明](../semantic-versions.md)。
