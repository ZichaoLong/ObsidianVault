---
type: research-question-index
status: open-questions
semantic-baseline: tide-core-2
---

# 教材之外仍值得研究的问题

本页吸收旧 SCC 备忘尚未解决的部分，并按当前教材重新限定范围。问题不是定义，也不预设必须扩展核心。旧迁移索引与问题原稿见 Git `133d638` 的 `appendices/research-memos/scc-macro-node-logical-time-research-memo.md`。

## 1. 更一般的节点级时间批条件

严格分层 region 提供一个清楚的充分条件；一般 TimedDAG 的 region 可以跨越空间依赖，区域商图也可能有环。需要判断哪些实例仍有与窗口长度无关的节点调用批数，哪些实例会通过正常消息边形成反复的 Full/后续区域控制依赖。这不表示当前 Next 可以读取 Full 结果；本节点 Full 回写状态是另一类尚未纳入的扩充。

目标应是额外的充分条件、反例及受限类的上下界，而不是从“空间图无环”直接推出一次批处理。[状态反馈与节点批](mathematics/state-feedback-and-node-chunks.md) 专门区分私有递归、控制递推和 Full 反馈。

## 2. 控制扫描什么时候也可以低 span

描述量、history、状态采用和 Next 可以在 Full 之前确定，不等于它们彼此无时间依赖。带恢复、阈值、Top-K 或选后清理的控制器，何时有紧凑、封闭且廉价的区间摘要？

时间衰减的半群只是一个局部正例。需要给定完整状态与选择规则后证明；不能把任意函数复合作为免费 scan。[自适应下界](mathematics/adaptive-routing-prefill-lower-bound.md) 也只有在完成具体 oracle embedding 后才适用。

## 3. 正时延 Graph 的宏节点组合

当前 [PositiveDelayGraph 教材](../positive-delay-graph-finite-cut-learning-note.md) 已证明固定正整数时延、有限节点/边及有限发射规则下的有限切面和继续性质。这部分不再记作未完成的 SCC 猜想。

剩余问题是怎样选择能独立执行的宏边界、保留跨边端口与在途消息，并处理跨 SCC 的 region/selector-history 依赖。空间 SCC 缩点得到 DAG，只说明消息结构；把跨块控制状态忽略后得到的 executor 仍可能错误。

若研究 payload-dependent 正时延或不同时间域，应另写扩展假设及有限性条件，不能让 runtime 参数静默改变当前固定时延语义。这里不引入零时延边。

## 4. 端口、消息和状态的安全商

哪些多端口、多来源消息可压成较少值，同时保持所有声明的后续输出和状态？[来源与读出](mathematics/provenance-and-readout.md) 给出因子分解条件，但对真实神经算子找到非平凡且便宜的压缩仍需研究。

精确变换、带误差界的近似、以数据拟合的蒸馏是三种主张；不能将它们合成一个模糊“Graph 收缩定理”。

## 5. 证明、数值实现与训练梯度怎样对应

实数模型中的等价不自动逐 bit 保持。应明确哪些归约重排被允许，如何处理状态压缩误差，以及 forward 的状态模拟怎样关联 backward 与截断边界。改变模型参数后继续使用旧 activation 的合法条件也需单独说明。

研究产物可以是一个有前提的局部证明或一个明确的数值契约；具体 backend、容差、测试覆盖及梯度记录由实验平台维护。

## 6. 机制是否带来可训练的价值

BO、私有记忆、层级局部路由、固定 merge 与 Next 清理是否真的被使用，并在匹配数据/计算/设备时间后改善质量？失败来自机制没有作用，还是训练预算与执行瓶颈？

问题与指标分别见 [训练诊断](learning-systems/learning-risks-and-diagnostics.md) 和 [执行成本](learning-systems/execution-and-cost.md)。上游不预写实验答案。

## 7. 如何维护这个索引

问题被教材部分解决后，只留下剩余部分并链接到已有结论。不同语义版本应显式分开；下游新增配置不是自动扩充 Graph 定义。脑科学、统计力学与编译器谱系仍是背景或假设，不因被多次引用就成为证明前提。
