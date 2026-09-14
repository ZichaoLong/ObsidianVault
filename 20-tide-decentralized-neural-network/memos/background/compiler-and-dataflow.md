---
type: background-reference
status: reference
semantic-baseline: tide-core-2
---

# 编译器与 dataflow：对 Tide 有用的研究谱系

本页介绍外部思想，不从它们导入 Tide 的定义或定理。当前语义以核心 [教材](../../README.md) 为准；原始综述见 Git `133d638` 的 `tide-background-history-and-references.md` 第一部分。

## 1. 为什么区分参考语义与执行顺序

处理器可以乱序执行，但必须保持 ISA 声明的可观察行为。编译器可以融合、重排和消除中间表示，但必须保持源程序或 IR 的契约。对 Tide 有用的是同一个问题：哪些状态与输出属于模型，哪些只是运行时安排？

一个 pack/reorder 实现不必保留每个临时 buffer，却必须保持以后还会读取的节点状态、selector-history、消息及读出。只比较一次最终 logits，可能漏掉后续继续时的差异。

参考：[Tomasulo 1967](https://doi.org/10.1147/rd.111.0025)；Hennessy 与 Patterson 的 *Computer Architecture: A Quantitative Approach*。

## 2. SSA、状态版本与显式依赖

SSA 给每个变量定义独立名字，便于看清 def-use 关系；MemorySSA 等表示进一步处理可变内存。其启发是给实际函数作用、状态版本、输入来源与可见性清楚命名。

静态控制流图的循环不意味着一次有限执行有同刻循环依赖：循环迭代展开后，先后版本仍可构成 DAG。但不能因此声称所有有限输入都终止。Tide 的正时延图教材用自然数时间、有限节点/边与全函数构造有限切面；这是自身假设下的结果。

参考：[Cytron 等，SSA](https://doi.org/10.1145/115372.115320)；[LLVM MemorySSA](https://llvm.org/docs/MemorySSA.html)。

## 3. 抽象解释与安全压缩

抽象解释以较小的抽象状态追踪具体程序的性质。它通常追求健全的充分条件，并不总是精确恢复原程序。

Tide 的 cache 压缩、消息聚合也需要声明抽象映射，但精确等价与保守分析应分开：一个来源集合上界可以安全地多记依赖；一个替代原模型的压缩状态则要保证未来输出仍可由它决定。对应条件与反例见 [来源、聚合与读出](../mathematics/provenance-and-readout.md)。

参考：[Cousot 与 Cousot，Abstract Interpretation](https://www.di.ens.fr/~cousot/COUSOTpapers/POPL77.shtml)。

## 4. Translation validation 与验证编译器

Translation validation 检查一次具体变换的前后程序是否等价；验证编译器则证明整个编译过程保持语义。前者适合探索中的局部 lowering，后者需要更稳定、较小的形式核心。

Tide 实现可以为某种 map fusion、布局变换或 scan 提供局部证明及差分测试。测试能发现错误，不是对所有输入的数学证明；浮点、内存别名、状态提交和求解器覆盖范围都应注明。

参考：[Pnueli 等，Translation Validation](https://doi.org/10.1007/BFb0054170)；[Alive2](https://alive2.llvm.org/ce/)；[CompCert](https://compcert.org/)。

## 5. KPN 与 SDF：相同图可以表达不同程序

Kahn process network 使用确定的顺序进程、FIFO、阻塞读取与概念上无界的通道，结果确定性依赖这些通信条件。任意可查看队列是否为空、按先到者决定输出的网络不自动属于 KPN。

Synchronous Dataflow 则规定固定生产/消费率，适合推导重复向量、静态周期调度和 buffer 需求。动态稀疏选择可能改变实际事件集合，不能只看固定空间拓扑就套用 SDF 调度。

有环网络的 bounded queue 可能造成无限通道模型没有的死锁。背压属于实现时，还需证明它不会改写输出或让本可完成的有限切面永久阻塞。

参考：Gilles Kahn, *The Semantics of a Simple Language for Parallel Programming*, IFIP 1974；[Lee 与 Messerschmitt，Synchronous Data Flow](https://doi.org/10.1109/PROC.1987.13876)。

## 6. Logical time、seal 与进展

Lamport 的逻辑顺序区分因果先后与物理完成时间。Naiad/Timely 进一步跟踪带时间消息及未完成工作的能力，说明为什么“现在没看到消息”不等于“以后不可能再有早消息”。

流处理语境里的 watermark 强度并不统一：某些 event-time watermark 是估计，需要迟到数据策略；另一些进展跟踪从尚未完成的工作推出更严格的边界。Tide 的 seal 必须按教材的确定谓词使用，不能由超时、空队列或统计预测代替。

当前教材使用自然数全序时间。偏序时间与 antichain 是可研究的外部工具，不是已有定义的隐含组成部分。

参考：[Lamport 1978](https://lamport.azurewebsites.net/pubs/time-clocks.pdf)；[Naiad](https://www.cs.princeton.edu/courses/archive/fall22/cos418/papers/naiad.pdf)；[The Dataflow Model](https://doi.org/10.14778/2824032.2824076)。

## 7. 有限前缀完成与整体停止

持续运行的正时延环可以永远不整体静止，却在每个有限 cut 前只产生有限作用。这与流计算的 productivity 问题相近。当前 PositiveDelayGraph 教材已对自己的固定正整数时延与有限发射规则给出有限切面及继续结论，不应继续把这部分列成尚未解决的 SCC 猜想。

更一般的时间域或无限发射规则则可能失去局部有限性。例如可积聚到有限时刻的无限递增实数时间序列，会出现另一种问题；这不属于当前自然数正时延模型，也不是继续扩展它的计划。

参考：[Data-Oblivious Stream Productivity](https://doi.org/10.1007/978-3-540-89439-1_7)。

## 8. Scan、provenance 与 confluence

Prefix scan 的价值来自可结合且可有效表示的转移摘要，而不是“所有函数复合都结合”。相关推导见 [kernel chunk 组合](../mathematics/kernel-chunk-composition.md)。

数据库 provenance 提醒我们：聚合后能否回答来源问题，取决于是否保存相应信息；若后继只依赖总和，就无需为重建每项来源付费。CALM/confluence 研究顺序无关的分布式结果，但它们的前提不能直接替代任意神经状态更新的证明。

Differential Dataflow 的带时间集合与增量维护提供了另一种索引/布局思想；派生索引可以是执行表示，不应偷偷成为新的模型含义。

参考：[Blelloch，Prefix Sums](https://www.cs.cmu.edu/~guyb/papers/Ble93.pdf)；[Provenance Semirings](https://doi.org/10.1145/1265530.1265535)；[Logic and Lattices for Distributed Programming](https://doi.org/10.1145/2391229.2391230)；[Differential Dataflow](https://www.cidrdb.org/cidr2013/Papers/CIDR13_Paper111.pdf)。

## 9. 对实现仓库的实际用途

这些谱系支持一种工作方式：先固定模型和可观察行为，再用显式依赖表示设计变换，给局部充分条件，并验证实际 kernel、布局和状态保存。它们不要求上游笔记承担完整编译器、设备 runtime 或实验验收系统。
