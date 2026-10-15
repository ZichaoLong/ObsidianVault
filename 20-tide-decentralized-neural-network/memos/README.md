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

- [[weighted-kv-sparse-activation-example|带权 KV 局部教材]]：聚合、记忆与可组合评分，有界发送增益及二次／熵／entmax 非空预算；正式证明、求解与隐式反向、全图成本与批量契约。
- [[weighted-kv-layered-example|带权 KV 的全连接分层实例]]：拓扑、时间与边界绑定，因果读出、配置生效条件和架构成本。
- [[weighted-kv-hb-lattice-example|带权 KV 的 HB-Lattice 实例]]：先展开再收拢的多区域邻域图，局部函数组合、候选传播和成本比较。
- [函数保持生长](mathematics/function-preserving-growth.md)：投影 simulation、中性 residual、有限 DAG 细化及受限 fixed-merge 闭包。
- [来源、聚合与读出](mathematics/provenance-and-readout.md)：安全商、保守依赖集合与未来可观察行为。
- [自适应路由下界](mathematics/adaptive-routing-prefill-lower-bound.md)：自足的 deterministic exact 黑盒查询模型与证明；不能直接当作任意具体 selector 的下界。

## 机制与学习风险

- [Selector 与局部记忆](architecture/selector-and-memory.md)：评分结构、预算正则、饱和、有界增益与下限候选的取舍，外部研究证据及适用范围。
- [学习风险与诊断](learning-systems/learning-risks-and-diagnostics.md)：跨架构的路径漂移、信用距离、粒度与状态负担、饥饿及辅助监督。

## 实验与实现对应

- [带权 KV：训练实验与推进](learning-systems/weighted-kv-experiment-plan.md)：任务、成本与教师目标，初始化、温度和部署选择，单项比较及决定条件。
- [带权 KV：实现核对](../weighted-kv-implementation-checks.md)：数学定义、分段导数、连续性、位置和继续关系的程序证据。

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
