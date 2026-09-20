---
type: migration-index
status: reference
as-of: 2026-09-20
tags:
  - tide
  - history
---

# 旧内容重写与追溯索引

2026-09-14 的整理将 20-tide 定位为数学教材与语义上游；本索引在 2026-09-20 随非正典目录重整更新。以下是内容去向，不是逐段复制关系。整理前完整版本可从提交 **133d638** 追溯；更早一次大整合前的材料见 **d27819f**。

例如在仓库根目录执行：

~~~bash
git show 133d638:20-tide-decentralized-neural-network/tide-mathematical-foundations.md
~~~

## 内容去向

| 原文件／部分 | 现行落点 |
|---|---|
| README、current-mainline 核心定位与学习路线 | [[../../README]]、[[../../semantics-anchor]] |
| 旧数学基础中的图、事件与切面定义 | 正典教材；不保留第二套核心定义 |
| transition、状态嵌入、生长与节点细化 | [[../mathematics/function-preserving-growth]] |
| kernel 分块、scan 与有限组合 | 图级条件见 [[../../timed-dag-chunk-prefill-learning-note|正典分块预填充教材]]；旧局部推导从 Git 历史追溯 |
| owner、数值依赖与读出归因 | [[../mathematics/provenance-and-readout]] |
| 自适应路由下界 | [[../mathematics/adaptive-routing-prefill-lower-bound]] |
| selector、记忆、恢复与负载 | [[../architecture/selector-and-memory]] |
| 训练困难、可归因比较与诊断 | [[../learning-systems/learning-risks-and-diagnostics]] |
| 执行能力、成本与物理映射 | 当前实现、设备映射和 profiling 由独立实验仓库维护；旧稿从 Git 历史追溯 |
| LH 早期实现与语义设计来源 | [[lh-history]]，不作为当前能力声明 |
| 脑科学调查与数字模型启发 | [[../background/neuroscience-survey]]、[[../background/neuroscience-model-ideas]] |
| 编译器与 dataflow | [[../background/compiler-and-dataflow]] |
| 统计力学与信息动力学 | [[../background/statistical-mechanics]] |
| SCC 旧迁移索引、学习路线 | [[../../resources/learning-resources]] |

## 退出的规则

- 旧文“唯一正式入口”“七份核心职责文件”等权威声明退出。
- 空输入时保存坐标自动逐时更新、从非候选中激活等旧规则不沿用。时间衰减重写为统一逻辑时间上的有效状态解码，不产生自主激活。
- 零时延不再列为研究候选；解释正时延为何重要的反例仍可用于教学。
- Full 结果回写未进入核心；边界说明见 [[../../timed-dag-region-selector-learning-note#134-让完整输出改变后续状态或选择|TimedDAG §13.4]]。
- region 隐含共同读写 KV／SSM 的处方删除；参数共享与明确 owner 的普通消息机制保留。
- 任意 DAG 分区收缩仍是 DAG 的泛化删除；合法分块必须检查真实跨块依赖。
- “stateful 但无负载历史就是 token-local”、全项目强制生长阶梯、已完成语义仍称待定义等表述删除。
- 旧单位时延窗口边界、显式 allocator 与固定 phase 只按原受限范围追溯，不覆盖一般正时延教材。

旧架构图、toy 代码与运行时计划不再作为当前目录内容；需要追溯时使用 Git 历史。当前正时延 Graph 教学 reference 由教材直接维护。

书籍目录保持为本地阅读资源，不纳入本次数学语义提交；不根据文件名判断或删除 PDF。
