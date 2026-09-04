---
type: current-mainline
status: active
as-of: 2026-09-04
tags:
  - tide
  - current-mainline
  - settlegraph
  - timed-dag
---

# TIDE 当前主线：从 SettleGraph 向 TimedDAG-v0 前进一步

> [!summary] 本页只回答三个问题
> 1. 当前正在完成什么？
> 2. 下一步只增加什么能力？
> 3. 满足什么条件后才能继续走向一般 Graph？
>
> 本页是当前学习与开发入口。TIDE 既有数学、架构、runtime 和 SCC 长文是按需查阅的研究资料库，不是继续推进前必须从头读完的教材。

## 一句话主线

```text
先完成 SettleGraph
→ 再只增加“不同 Token 的消息可以在同一节点、同一逻辑时刻相遇”
→ 得到 TimedDAG-v0
→ 最后才增加带正时延的环
```

当前不直接研究“任意 Graph 的通用解释器”。每一级都先形成可以手算、可以运行、可以暂停恢复、可以与前一级对拍的闭合对象。

## 当前台阶：SettleGraph

SettleGraph 是当前已经定义清楚的弱语义：对每个 Token，每条固定边恰好结算为 `DATA` 或 `CLOSED`；每个 selection region 等待本 Token 的候选情况完整确定，然后只选择和结算一次。不同 Token 即使被同一个 packed kernel 同时计算，语义上仍是不同事件。

唯一权威来源在 `fractal-latcarf`：

- [随分支更新的 SettleGraph 语义](https://github.com/ZichaoLong/tide/blob/fractal-latcarf/docs/experiment-semantics-and-naming.md)
- [本次整合所依据的固定语义版本 `32278d8`](https://github.com/ZichaoLong/tide/blob/32278d8315198ed613b26bb6584dee5e6aa64060/docs/experiment-semantics-and-naming.md)
- [实现与等价性验证计划](https://github.com/ZichaoLong/tide/blob/fractal-latcarf/docs/settlegraph-implementation-plan.md)

当前优先完成：

1. 证明 SettleGraph 通用解释器对每个合法 Plan 都存在并终止。
2. 完成 packed prefill，并与逐 Token decode reference 比较完整输出、状态和 trace。
3. 固定一个可复现版本，作为下一语义台阶的 oracle。

这些工作没有完成时，TimedDAG-v0 可以写例子和参考解释器，但不反过来改动 SettleGraph 的权威语义。

## 下一台阶：TimedDAG-v0

下一步只放松一条约束：

```text
SettleGraph：事件主要按 (sequence, token, receiver/region) 分开
TimedDAG-v0：节点事件按 (node, logical_time) 形成
```

因此，如果不同 Token 的消息具有相同逻辑到达时间，它们可以进入同一个关闭后的输入桶，由一次节点事件联合处理。

完整的学习规格、最小例子、解释器轮廓和待证命题见：

> [[timed-dag-v0-learning-note|TimedDAG-v0：从 SettleGraph 到跨 Token 汇合的最小一步]]

## TimedDAG-v0 明确不做什么

第一版暂不加入：

- 有向环和 SCC；
- 零时延边或代数环；
- 偏序时间、antichain 和 capability；
- 消息部分到达后立即提交不可逆状态；
- 迟到消息修改已经发布的输出；
- 随机或依赖墙钟竞争的模型语义；
- packed、GPU/NPU 或分布式优化；
- 一般 fixed-point、root-solve 或无限迭代。

这些不是被否定，而是被明确延期。延期可以保证当前每个新概念都有独立的例子、解释器和证明位置。

## TimedDAG-v0 的退出条件

只有下面六项全部完成，才进入带环 Graph：

- [ ] 能手算一个跨 Token 同刻汇合例子的完整消息与状态 trace。
- [ ] 有一个只依赖整数逻辑时间的 reference interpreter。
- [ ] 随机改变物理消息送达和独立 ready-event 顺序，完整结果不变。
- [ ] 一次运行与任意合法 cut 上暂停、保存、恢复后的结果相同。
- [ ] SettleGraph 可作为禁止跨 Token 汇合的受限 profile 嵌入，并通过 trace 对拍。
- [ ] 已明确证明或明确标记尚未证明：有限 cut 完成、调度无关、cut composition、SettleGraph refinement。

“代码可以跑一个例子”不等于退出；“已经写出所有一般定义”也不等于退出。退出标准是语义、例子、实现和证明义务彼此指向同一对象。

## 再下一步：DelayedGraph-v0

TimedDAG-v0 完成后，只再增加一项能力：允许静态图出现环，但仍要求每条边都是严格推进逻辑时间的正时延边（因此每个环当然也包含正时延）。

```text
静态图：可以有环
动态事件：θ 的事件只能影响 θ+d，且 d ≥ 1
```

这时一次开放执行可以永不全局静止，但每个已经获得足够输入 seal 的有限 cut 仍应在有限工作后完成。第一版 `DelayedGraph-v0` 明确拒绝全部 zero-delay cycle；SCC 只用于把结构图分成宏节点，不自动提供宏节点内部语义。

只有这一台阶闭合后，才讨论 zero-delay SCC、solver 或偏序时间。

## 推荐阅读顺序

1. 先读并运行 `fractal-latcarf` 当前 SettleGraph 语义和 reference。
2. 第一次只读 [[timed-dag-v0-learning-note]] 的第 0 节并完成四道题；不要继续读后面的定义。
3. 实现最小整数 payload 解释器，不接入神经网络。
4. 完成随机调度、cut/resume 和迟到消息拒绝测试。
5. 再按需查阅 [[tide-mathematical-foundations]] 中的绝对轮次、时间桶、时间分块反例和 finite-cut 定义。
6. 最后才将 Torch node 或 SettleGraph adapter 接入 TimedDAG-v0。

如果某个旧概念不能帮助解决当前例子、解释器或四个待证命题，就暂时不读、不迁移、不扩写。

## 本页维护规则

1. 本页保持短小，只记录当前台阶、下一台阶、延期范围和退出条件。
2. 活跃语义只在对应实验仓库的 `semantics` 文档中定义；本页只提供定位和固定版本链接。
3. 每次只允许一个“下一台阶”。不得同时把 TimedDAG、SCC、偏序时间和 solver 都标成当前主线。
4. 只有产生稳定语义、reference、证明或反例后，才把结论重新整合进 TIDE 长文。
5. 动态工程状态必须带日期和 commit；未提交 WIP 不进入能力声明。
