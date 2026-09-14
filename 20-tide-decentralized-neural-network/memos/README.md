---
type: research-memo-index
status: active-index
semantic-baseline: tide-core-3
---

# Tide 研究备忘

这里保存核心教材之外的推导、可选构型、学习问题、外部背景与历史。数学入口见 [Tide 主入口](../README.md)；备忘中的候选不会自动修改 Graph、TimedDAG 或 SettleGraph 的定义。具体模块配置、实现等价性、训练和性能结果由实验仓库维护。

## 数学问题

- [函数保持生长](mathematics/function-preserving-growth.md)：投影 simulation、中性 residual、有限 DAG 细化及受限 fixed-merge 闭包。
- [Kernel 的 chunk 组合](mathematics/kernel-chunk-composition.md)：map、causal attention、affine scan 与 linear accumulator 的简短证明。
- [来源、聚合与读出](mathematics/provenance-and-readout.md)：安全商、保守依赖集合与未来可观察行为。
- [状态反馈与节点批](mathematics/state-feedback-and-node-chunks.md)：状态递推、控制扫描、私有计算与 Full 反馈的区别。
- [自适应路由下界](mathematics/adaptive-routing-prefill-lower-bound.md)：自足的 deterministic exact 黑盒查询模型与证明；不能直接当作任意具体 selector 的下界。

## 构型与机制

- [拓扑与生长候选](architecture/topology-and-growth-candidates.md)：有界度、多跳、HB、固定 merge、head/group 与 checkpoint 生长坐标。
- [Selector 与局部记忆](architecture/selector-and-memory.md)：内容/状态/history、时间衰减、恢复、Next 清理与单 owner 上下文。

## 学习与系统

- [学习风险与诊断](learning-systems/learning-risks-and-diagnostics.md)：路径漂移、三种信用距离、饥饿、辅助监督与机制对照。
- [执行与成本](learning-systems/execution-and-cost.md)：正确、有限、节点可批与实际更快需要哪些不同证据。

## 背景阅读

- [人脑信号传播调查](background/neuroscience-survey.md)：保留 2026-07-22 调查的解剖、生理与文献实质。
- [脑科学启发与边界](background/neuroscience-model-ideas.md)：将调查中的事实转成可检验的数字模型问题。
- [编译器与 dataflow](background/compiler-and-dataflow.md)：ISA、SSA、抽象解释、验证、KPN/SDF、logical progress 与 provenance。
- [统计力学与信息动力学](background/statistical-mechanics.md)：路径相关、路由熵与宏观极限的候选研究。

## 问题、历史与资源

- [教材之外的研究问题](research-questions.md)：只记录当前仍未解决的部分。
- [LH、旧 runtime 与 HB 历史](history/lh-and-runtime.md)：带日期的机制来源、旧程序与旧图。
- [按问题选读的资源](../resources/learning-resources.md)：书目与小练习，无强制课程门槛。

## 保留方式与来源

本次整理以 Git `133d638` 为旧材料追溯点。旧数学长文拆为可复用局部推导；旧架构长文按构型、状态、学习和系统问题拆分；旧 runtime 的当前政策身份移除，仅保留必要历史；背景调查与物理类比分开；SCC 原问题按教材已完成的范围收缩。

阅读时区分五种主张：已有教材实例、有前提的局部推导、核心之外的扩展问题、经验假设、历史/外部背景。发现冲突应修订备忘；不通过备忘反向扩大教材。研究问题被解决后链接正式落点，不再维持重复答案。
