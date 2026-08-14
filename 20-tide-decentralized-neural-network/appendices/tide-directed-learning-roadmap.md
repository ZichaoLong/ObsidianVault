---
type: learning-roadmap
status: draft
date: 2026-08-13
tags:
  - tide
  - appendix
  - learning-roadmap
  - algorithms
  - systems
  - machine-learning
---

# 附录：Tide 定向学习路线——从图算法到神经架构实验

> [!summary] 本页定位
> 本页是一份独立的个人学习与实现路线，面向“数学本科背景、未系统学习计算机科学、需要通过亲自证明和实现形成理解”的读者。它提供中文材料与英文材料两条平行、可独立完成第一轮骨架的路线；英文线不是中文线的补充，中文线也不是英文线的预备。进入前沿研究后的英文一手文献核验边界见第 8 节。它不承担 Tide 的正式定义或研究结论，也不替代任何已有研究备忘。

> [!warning] 与 Tide 主线的边界
> 本页中的课程、月份和项目只构成个人学习验收脚手架，不表示 Tide 已经实现这些项目，也不构成研究里程碑、正式定义、定理或架构承诺。任何 Tide 主张都必须回到七份核心职责文档或原始来源核验。返回 [[20-tide-decentralized-neural-network/README|Tide 主入口]]。

## 1. 结论先行

本页给出两个同等级选择：

1. **中文材料路线**：第一年只依赖中文版教材、中文原创教材和中文在线课程，形成完整骨架；
2. **英文材料路线**：第一年直接使用英文教材、英文课程与论文，独立完成同一组证明和实现。

两条路线不是逐本对应的翻译表，也不要求混读。它们使用不同材料覆盖同一组能力目标：

1. 有向图与算法；
2. computation models、并发语义与 logical time；
3. 并行算法、计算机系统和机器成本；
4. 编译器 IR、静态分析与 semantics-preserving lowering；
5. finite cut、progress frontier、watermark、continuation 与长期运行系统；
6. Attention、GNN、SSM、DEQ 与 learning value。

应先选择一条作为主线，至少连续执行一个阶段，不要把两套同类教材同时通读。后文的“六联件”、七个 Tide 项目与学习验收点是两条路线共用的验收协议，不代表材料需要混合。

推荐的总主轴是：

```text
有向图算法
→ 有状态与并发计算语义
→ 并行算法和机器成本
→ 编译器 IR 与静态分析
→ 流式系统的 logical progress
→ 神经算子、训练与 learning-value 实验
```

这条顺序有意把执行设计的四道 gate 分开：

- **Semantic gate——算的是什么**：reference semantics、状态、消息、时间和可观察 artifact；
- **Progress gate——声明的有限 cut 能否返回**：termination/productivity、seal、局部有限性和完成证书；
- **Parallel-complexity gate——算法上能否批量并行**：work、span、组合律、依赖深度与下界；
- **Hardware-lowering gate——机器上是否真的快**：访存、批量化、稀疏不规则性、kernel 和硬件利用率。

最后再加入独立的经验问题：

- **模型是否值得学**：可训练性、泛化、智能、动态机制是否被真正使用。

前四类成熟研究可以大幅约束 Tide 的执行与实现空间，却不能替代 learning-value 神经架构实验。

## 2. 为什么这些学科正好对应 Tide

| Tide 中的问题 | 对应研究谱系 | 需要掌握的最小内容 |
| --- | --- | --- |
| Graph、DAG、SCC 与 condensation | 图算法 | DFS、拓扑序、可达性、SCC、缩点图 |
| `prefill = decode` 到底在比较什么 | 程序语义、状态机、并发模型 | transition、trace、state、composition、causality |
| DAG 为什么不自动等于高性能 | 并行算法 | work/span、critical path、scan、通信成本 |
| 如何把 reference executor 变成 kernel | 编译器与静态分析 | IR、def-use、SSA、lattice、worklist、fusion、validation |
| SCC 如何对有限 prefix 宣告完成 | dataflow 与流式系统 | logical time、event time、progress frontier、watermark、continuation |
| 反馈、开放循环和不终止 | 计算理论、并发与数值方法 | decidability、liveness、fixed point、solver convergence |
| 图消息传播是否有 learning value | 深度学习、GNN、SSM、DEQ | 反向传播、优化、归纳偏置、受控实验 |
| 优化版本是否真的更快 | 体系结构、GPU 与 ML systems | cache、memory traffic、tiling、profiling、benchmark |

这里的“图”至少有三层，不应混为一谈：

1. **静态空间 Graph**：可复用节点及连接；
2. **一次执行的动态 event/dependency graph**：具体事件及真实依赖；
3. **物理执行 schedule**：CPU/GPU/runtime 实际采用的顺序。

图算法先帮助描述第一层；语义帮助构造第二层；编译器和 runtime 才负责合法地改变第三层。

## 3. 学习方法：每个主题都交付六联件

对每个核心概念，不以“读完一章”作为完成标准，而交付：

1. **定义**：不用原文句式，自己精确写出对象、前提和结论；
2. **证明**：闭书重建至少一个核心结论；
3. **反例**：主动移除一个前提，构造最小失败实例；
4. **reference**：实现慢但清晰、贴近定义的版本；
5. **optimized**：实现一个利用额外结构的版本；
6. **验证**：做 property test、复杂度账本和 profiling。

### 3.1 六种证据必须分栏记录

| 证据 | 能说明什么 | 不能说明什么 |
| --- | --- | --- |
| 数学证明 | 对抽象模型中的所有合法实例成立 | 代码无 bug、机器上快 |
| 语义等价证明 | 优化执行保留声明的可观察行为 | 浮点逐 bit 相同、吞吐高 |
| work/span 分析 | 理想并行模型中的操作量与依赖深度 | 实际 GPU 利用率 |
| 单元与 property test | 已测试实例符合性质，能发现大量错误 | 对无限输入空间构成证明 |
| profiling/benchmark | 指定硬件、实现、shape 下的真实成本 | 算法普遍更优 |
| 训练实验 | 指定预算与任务下的 learning behavior | 普遍智能更强或机制必然有效 |

一个常见错误是用后一栏越权替代前一栏。例如，随机测试通过不能证明 `prefill = decode`；理论上有 `O(log n)` span 也不能证明小 batch 的 GPU kernel 更快；训练 loss 更低也不能证明动态 routing 被使用。

### 3.2 编程工具的推荐顺序

```text
Python
→ NumPy reference
→ pytest / property testing
→ PyTorch
→ C/C++ hotspot
→ profiler
→ Triton / CUDA / NPU backend
```

前三步的目标是把语义说清楚。只有 reference、边界状态和差分测试稳定后，才值得写设备 kernel。学习初期不必同时掌握 C++、CUDA 和分布式框架。

### 3.3 开始前的编程门槛

本路线不是编程零基础教程。开始第一月前，先用一个周末做诊断：

```text
能用 Python 写函数、类、递归和迭代器
+ 能实现 stack、queue、set/map 与 adjacency list
+ 能解释 NumPy shape、indexing 和 broadcasting
+ 能用 pytest 写断言和参数化测试
+ 能用 Git 保存小步提交
+ 能在 shell 中运行程序、查看错误并做基本 debugging
+ 理解 O(1)、O(n)、O(n log n) 等渐近记号
```

若其中多项不熟，先增加 2–4 周。中文线使用中文 Python 入门材料，并从《算法导论》的基础数据结构章节补缺；英文线可用 *Python Crash Course* 或 *Think Python*，再配 Pat Morin 的 *Open Data Structures*。C、C++、CUDA 和分布式系统都不是开始第一月的先修条件；但若第 6 月要做 CSAPP 的程序与存储实验，应在此前补到能读懂小段 C、编译器输出和基础汇编。CUDA 与分布式实现仍可后置。

## 4. 阅读规则与时间预期

本路线中的资料分为三类：

- **主教材**：连续精读，做习题和实现；
- **项目教材**：跟着项目按主题选读；
- **参考书**：遇到具体问题再查，不从第一页通读。

按每周 8–10 小时，12 个月可以完成第一轮，形成能够继续跟进 Tide 讨论的骨架；要按“六联件”深度做完后文七个项目、神经训练实验、GPU kernel 和形式语义，更现实的是 18–24 个月。12 个月的目标限于系统主轴、CPU reference 和若干最小神经语义原型，不承诺完整复现所有架构或形成广泛的 learning-value 结论。

神经实验不应全部积压到最后。第 3 月起每周可固定约 2 小时，按概念螺旋式加入：

```text
state machine 后   → 最小 RNN
DAG/window 后      → causal Attention 的 prefill/decode
scan 后            → scalar/diagonal affine recurrence
fixed-round DAG 后 → 最小 GNN
fixed point 后      → 最小 implicit layer
```

建议每周固定分配：

- 3 小时读书并重写定义；
- 2 小时独立证明和构造反例；
- 3 小时实现与测试；
- 1–2 小时整理复杂度账本、实验结果和未决问题。

## 5. 中文材料：独立完整路线

本节单独构成中文路线。第一年不要求阅读任何英文教材；部分书是英文著作的中文版，但实际学习材料为中文。书目不要求全部通读；章节号在不同译本中可能变化，以下均按主题定位。每一阶段直接完成第 7 节对应项目，不依赖第 6 节英文书目。

### 5.1 离散基础与有向图算法

**主教材：**

- Cormen 等，《算法导论（原书第 3 版）》：数据结构、DFS、拓扑排序、SCC、动态规划和复杂度的主线。
- Rosen，《离散数学及其应用（原书第 8 版）》：仅在逻辑、归纳、关系、偏序、图与树存在缺口时补读。

**证明型补充：**

- West，《图论导引》：用于加强图论证明感，不建议第一遍通读。
- Sipser，《计算理论导引》：后期按需读图灵机、可判定性和归约，用于理解开放循环、一般程序执行与停机问题的边界。

**本阶段必须亲自完成：**

- 从定义证明拓扑序存在当且仅当有限有向图无环；
- 分别实现 Kahn 和 DFS 拓扑排序；
- 实现 Tarjan 与 Kosaraju 中至少一个，并能解释另一个；
- 证明 SCC 构成划分，condensation graph 必为 DAG；
- 用小图的暴力可达性程序对拍 SCC 实现。

### 5.2 计算模型、状态机与 logical time

**主教材：**

- Edward A. Lee、Sanjit A. Seshia，《嵌入式系统导论：CPS 方法（原书第 2 版）》。

重点不是嵌入式硬件，而是：

- state machine 及组合；
- concurrent models of computation；
- discrete-event model；
- logical time 与 physical time；
- feedback、causality、scheduling；
- 连续动力学与离散控制之间的边界。

读完后应能明确回答：同一张静态 Graph 在 Kahn process network、同步数据流、离散事件和共享可变状态语义下，为什么可能表示不同程序。

### 5.3 并行算法与机器成本

**算法主线：**

- 陈国良，《并行算法的设计与分析（第 3 版）》；
- Pacheco，《并行程序设计导论》，或 McCool、Robison、Reinders，《结构化并行程序设计》，作为实现辅助。

**机器主线：**

- Bryant、O'Hallaron，《深入理解计算机系统（原书第 3 版）》；
- Remzi Arpaci-Dusseau、Andrea Arpaci-Dusseau，《操作系统导论》（OSTEP），选读并发、虚拟内存和持久化；
- Kirk、Hwu 等，《大规模并行处理器编程实战》，在完成 CPU scan 后再读。

本阶段重点是：

- work、span、parallelism 与 critical path；
- reduction、prefix scan、segmented scan；
- cache、memory hierarchy、局部性与带宽；
- 线程、同步和任务分解；
- 理论操作数、内存流量和墙钟时间的区别。

Attention 与 SSM 必须分开分析。Dense causal Attention 有因果可见性，但已知整个 prefix 时，各位置的 query 可以 bulk 求值；标准 dense 形式的主要长度成本通常是二次 work 与 I/O，而不是 token recurrence 导致的线性依赖链。SSM/RNN 的朴素 recurrence 才通常有随长度线性增长的 span；只有转移具有可用的封闭 summary 等额外结构时，才可能用 scan 降低理想 span。两者都可能获得高吞吐 kernel，但理由不同。反过来，DAG 即使有许多 ready 节点，也不保证不规则 gather/scatter 在机器上会快。

### 5.4 编译器、IR 与静态分析

**主教材：**

- Cooper、Torczon，《编译器设计（第 2 版）》。

**静态分析项目参考：**

- Nielson、Nielson、Hankin，《程序分析原理》中文版：按需查阅格、单调数据流框架、抽象解释与 widening，不要求第一遍通读。

重点选读：

- 中间表示与控制流图；
- dominance、SSA 和 def-use；
- data-flow equations；
- liveness、reaching definitions；
- loop、scheduling 和局部优化；
- 优化正确性与 translation validation 的思想。

中文路线还可配合免费教材：

- 《机器学习系统：设计和实现》（OpenMLSys）：<https://openmlsys.github.io/>

编译器在这里不是为了学习语法分析器，而是为了获得一种工作方式：先定义 reference IR 和 observable behavior，再允许 SCC pass、fusion、packing 和 backend lowering 改变物理执行。

### 5.5 流式系统与长期运行计算

**项目教材：**

- Kleppmann，《数据密集型应用系统设计》；
- Akidau、Chernyak、Lax，《流式系统》。

重点是 log/replay、stateful processing、event time、window、watermark、trigger、checkpoint、backpressure，以及 exactly-once state/effect semantics 成立所需的具体条件。需要保留一个重要区别：

- 工程系统中的 watermark 常是“预计较早事件不会再来”的估计；
- Tide 若要精确证明某个 prefill cut 已完成，需要输入 seal、内部 pending work/生产能力的封闭证明、有限前缀终止性和完整 continuation；hard output watermark 或 progress frontier 是该证明的对外表示，不是单独充分条件。

因此不能把书中的工程 watermark 直接当成 Tide 的完成证书。

### 5.6 神经网络、GNN 与数值方法

**神经网络主线：**

- 邱锡鹏，《神经网络与深度学习》第 2 版：<https://nndl.ai/>
- 《动手学深度学习》中文第 2 版：<https://zh.d2l.ai/>

**实验方法项目读物：**

- Goodfellow、Bengio、Courville，《深度学习》中文版第 11 章“实践方法论”；配合 OpenMLSys 的 profiling 内容，用于第 12 月的实验设计与测量链路。

**图学习：**

- 刘知远、周界，《图神经网络导论》。

**数值方法参考：**

- 李庆扬等，《数值分析》，按需补 fixed point iteration、Newton 法、线性方程与误差分析。

学习目标不是复现更多模型名称，而是能够分别实现并比较：

- RNN 的逐步 fold；
- causal Attention 的 whole-prefix 与 KV-cache decode；
- 具有紧凑封闭 summary 的结构化 affine recurrence，其 serial 与 scan 实现；
- 固定 `K` 轮 GNN 与分层 DAG 展开；
- DEQ 的有限展开、求解器与 implicit differentiation。

### 5.7 中文核心精读书架与必需项目读物

连续精读的五本核心优先：

1. 《算法导论》；
2. 《嵌入式系统导论：CPS 方法》；
3. 《深入理解计算机系统》；
4. 《并行算法的设计与分析》；
5. 《编译器设计》。

这五本不是中文闭环所需的全部材料。静态分析项目按需使用《程序分析原理》；神经项目必须同时使用《神经网络与深度学习》《动手学深度学习》和《图神经网络导论》；流式项目必须使用《流式系统》和《数据密集型应用系统设计》；数值 fixed-point 项目按需使用《数值分析》；实验方法使用《深度学习》中文版第 11 章与 OpenMLSys。它们是项目读物，不要求全书精读，但不是可有可无。

### 5.8 中文路线的十二个月阅读与练习表

下表只引用中文材料。第 7 节给出项目的完整规格；这里规定每个月读什么、证明什么和实现什么。

| 时间 | 中文材料 | 证明与实现交付 |
| --- | --- | --- |
| 第 1–2 月 | 《算法导论》图算法部分；《离散数学及其应用》按需查漏 | `graph_core`；拓扑序、SCC 划分、condensation 为 DAG 三份闭书证明；小图暴力 oracle |
| 第 3 月 | 《嵌入式系统导论：CPS 方法》的状态机、组合、并发模型与 logical time；《神经网络与深度学习》的 RNN 部分 | timed state-machine simulator；同一 Graph 在不同计算模型下语义不同的反例；最小 RNN forward |
| 第 4 月 | 《嵌入式系统导论：CPS 方法》的 feedback、causality、discrete event；《动手学深度学习》的 Attention/Transformer 部分 | `dag_executor`；随机窗口切分测试；naive causal Attention 的 prefill/decode 对拍 |
| 第 5 月 | 《并行算法的设计与分析》的 reduction、prefix；《结构化并行程序设计》按需 | `scan_lab` 的 serial、Hillis–Steele、Blelloch、segmented 与 scalar/diagonal affine recurrence；work/span 证明 |
| 第 6 月 | 《深入理解计算机系统》的程序优化与存储器层次；《并行程序设计导论》按需 | 固定 benchmark protocol；对 scan/DAG traversal 做 locality 与 CPU profiling；GPU 仅选做 |
| 第 7 月 | 《编译器设计》的 IR、CFG、SSA、def-use 与数据流分析 | `mini_tide_ir` v1、SCC pass、state version 与 read/write contract |
| 第 8 月 | 《编译器设计》的 liveness/reaching definitions、优化；OpenMLSys 对应章节 | lattice/worklist 小实现；一项 fusion/batching；source 与 lowered executor 差分验证 |
| 第 9 月 | 《流式系统》的 event time/window/watermark/state；《数据密集型应用系统设计》的 log、stream、checkpoint | 全序整数时间版 `scc_stream_runtime`：source seal、`AdvanceUntil`、continuation、逐输出 port scalar watermark 与 replay |
| 第 10 月 | 《神经网络与深度学习》和《动手学深度学习》的自动微分、RNN、Attention | `micro_autograd` 核心；完善 canonical output/state 与浮点容差层面的 prefill/decode equality |
| 第 11 月 | 《图神经网络导论》；《数值分析》的不动点迭代、Newton 法与误差分析 | GNN、结构化 affine recurrence、implicit layer 三选一做完整六联件；另两项只做最小 forward prototype |
| 第 12 月 | 《深度学习》中文版第 11 章“实践方法论”；OpenMLSys 的 profiling 内容 | 一个可证伪假设、2–3 个 baseline/ablation 的 `mini_tide_benchmark` 测量链路 pilot；claim ledger 审计 |

这条路线的第一年交付不以英文教材或英文课程为前提。KPN、SDF、Naiad、S4、Mamba、DEQ、FlashAttention 等英文原论文可在第二轮文献研究时进入；不读这些原文不会阻止完成中文线的第一轮骨架，但会限制之后对原始契约和最新架构的核验。

## 6. 英文材料：独立完整路线

### 6.1 英文路线的定位

本节单独构成英文路线，可以完全不依赖第 5 节中文教材。自己的证明、注释和研究笔记仍可用中文书写，但定义、习题、课程和第一手主张直接取自英文材料。下面的说明文字使用中文只是为了便于选择，不属于学习资料依赖。

英文线按下面六个模块自足地展开：

1. algorithms and directed graphs；
2. models of computation and concurrency；
3. parallel algorithms, computer systems and GPU cost；
4. compiler IR and static analysis；
5. streaming/dataflow semantics；
6. neural architectures and ML systems。

选择英文线的理由可以是材料质量、习题风格或直接进入原始文献，而不是把它理解成中文路线完成后的“高级补充”。

### 6.2 算法与有向图

**第一主教材：**

- Jeff Erickson, *Algorithms*，免费：<https://jeffe.cs.illinois.edu/teaching/algorithms/>

它比 CLRS 更短、更强调“为什么正确”和如何发现算法，适合已经习惯数学证明的读者，但不是编程和数据结构的零基础教材。先通过 3.3 节的门槛；第一轮可从第 5 章 Basic Graph Algorithms、第 6 章 DFS 入手，再按需回读递归和动态规划，并认真做证明题。

**替代与参考：**

- Dasgupta、Papadimitriou、Vazirani, *Algorithms*：同样简洁，可与 Erickson 二选一，不建议两本并行通读；
- CLRS, *Introduction to Algorithms*, 4th ed.：查实现细节、图算法和 parallel algorithms；
- Pat Morin, *Open Data Structures*：若数组、链表、哈希表、堆和树的实现基础不足，再补；
- Bang-Jensen、Gutin, *Digraphs: Theory, Algorithms and Applications*：有向图专项参考，不作为第一本图论书；
- Sipser, *Introduction to the Theory of Computation*：后期读 decidability 与 reduction；
- Greenlaw、Hoover、Ruzzo, *Limits to Parallel Computation*：研究 Boolean Circuit Value 等 DAG 求值问题的 P-completeness 时再读。这类结论依赖“带足够表达力的节点语义，且电路本身也是输入”，不是裸 DAG 拓扑的性质，也不能直接套给固定有限图或受限结构族。

推荐实际组合是“Erickson 精读 + CLRS 查阅 + Digraphs 遇题再查”。

### 6.3 计算模型与并发语义

**主线与项目教材：**

- Edward A. Lee、Sanjit A. Seshia, *Introduction to Embedded Systems: A Cyber-Physical Systems Approach*，免费：<https://ptolemy.berkeley.edu/books/leeseshia/>
- Peter Van Roy、Seif Haridi, *Concepts, Techniques, and Models of Computer Programming*。

Lee–Seshia 提供 logical time、feedback 和 causality 的主轴，适合连续精读。Van Roy–Haridi 系统比较 declarative computation、dataflow variables、lazy streams、message passing、state 和 concurrency，但体量很大，第一轮只选上述主题。它使用 Oz；不必把学习 Oz 变成独立工程，可用 Python 写一个保留所选关键假设的微型解释器，而不声称与完整 Oz 语义等价。

**并发验证补充：**

- Jeff Magee、Jeff Kramer, *Concurrency: State Models & Java Programs*：重点读 labelled transition systems、trace、safety、liveness、deadlock 和 progress，Java 不是重点；
- Baier、Katoen, *Principles of Model Checking*：以后形式化 runtime 再查；
- Reisig, *Understanding Petri Nets*：若 Tide 越来越采用 token/event firing 语义，再学习 marking、boundedness、liveness 与 reachability。

可配一个很小的 `lts_checker`：枚举有限 LTS 的状态和 transition，检查 reachability、deadlock 与 safety；只有先明确 fairness 假设，才讨论 liveness。

### 6.4 并行算法、系统与 GPU

**主线与项目书：**

- Bryant、O'Hallaron, *Computer Systems: A Programmer's Perspective*；
- Remzi Arpaci-Dusseau、Andrea Arpaci-Dusseau, *Operating Systems: Three Easy Pieces*，免费：<https://pages.cs.wisc.edu/~remzi/OSTEP/>
- Grama 等, *Introduction to Parallel Computing*；
- McCool、Robison、Reinders, *Structured Parallel Programming*；
- Blelloch, “Prefix Sums and Their Applications”；
- Kirk、Hwu、El Hajj, *Programming Massively Parallel Processors*, 4th ed.；
- Sze 等, *Efficient Processing of Deep Neural Networks: A Tutorial and Survey*。

Grama 的具体硬件示例有年代感，但 decomposition、mapping、communication 和 cost model 仍然有用。GPU 学习顺序应是 CPU serial/parallel reference → profiler → PMPP/CUDA → Triton，而不是直接从设备代码猜语义。

### 6.5 编译器、静态分析与 ML systems

**主教材：**

- Cooper、Torczon, *Engineering a Compiler*, 3rd ed.；
- Anders Møller、Michael Schwartzbach, *Static Program Analysis*，免费讲义：<https://cs.au.dk/~amoeller/spa/>

前者负责 IR、CFG、SSA、dominance、优化与 scheduling；后者负责 lattice、least fixed point、monotone analysis、worklist 和 abstract interpretation。两者合起来比只读通用编译器教材更贴近 Tide。

**实现课程：**

- CMU 10-414/714, *Deep Learning Systems*：<https://dlsyscourse.org/>

CMU 课程中的 Needle 作业很适合理解框架怎样把神经语义 lower 到机器。第一轮只要求 autodiff 核心、少数 tensor operator、一个 CPU/vectorized backend 和基础 profiling；完整 GPU backend 接近一门学期项目，留到第二轮。

### 6.6 Streaming 与 dataflow

**主教材：**

- Akidau、Chernyak、Lax, *Streaming Systems*；
- Kleppmann, *Designing Data-Intensive Applications*。

前者精读 event time、window、watermark、trigger 和 state；后者选读 log/replay、batch/stream、partition、failure、consistency 和 backpressure。

“dataflow”至少有三种不同含义：

| 名称 | 研究对象 | Tide 中的用途 |
| --- | --- | --- |
| compiler data-flow analysis | CFG 上传播抽象事实并求 fixed point | IR 验证、liveness、状态版本分析 |
| KPN/SDF process networks | 进程通过 stream/channel 通信 | 节点 firing、静态速率、确定性与调度 |
| Naiad/Beam distributed dataflow | 分布式事件、时间戳与进度跟踪 | logical progress frontier、finite-cut completion |

三者共享 graph、lattice 或 fixed point 等数学形状，但语义契约不同，不能仅因都叫 dataflow 就互相套用结论。

类似的术语碰撞还包括 compiler abstract-domain lattice、Kahn stream CPO、timestamp partial order、DEQ numerical fixed point，以及 Tide 名称中的 HB-Lattice；它们不是同一个数学对象。

### 6.7 英文神经网络路线

**三本角色不同的主干：**

- Simon J. D. Prince, *Understanding Deep Learning*，免费正文与 notebooks：<https://udlbook.github.io/udlbook/>。负责现代直觉、公式和架构全景；
- Zhang、Lipton、Li、Smola, *Dive into Deep Learning*：<https://d2l.ai/>。负责把主题立即变成代码；
- William L. Hamilton, *Graph Representation Learning*，在线版：<https://www.cs.mcgill.ca/~wlh/grl_book/>。负责 message passing、aggregation、equivariance 与 expressivity。

**数学参考，不平行通读：**

- Bishop、Bishop, *Deep Learning: Foundations and Concepts*；
- Goodfellow、Bengio、Courville, *Deep Learning*：优先查前馈网络、优化、序列模型和实验方法；
- Deisenroth、Faisal、Ong, *Mathematics for Machine Learning*：只在矩阵微积分、概率和优化存在缺口时补。

**按研究主题进入一手材料：**

- 自动微分：Baydin 等的 survey + CMU Needle；
- RNN/Attention：D2L、CS224N、*The Annotated Transformer*、Transformer、Transformer-XL、FlashAttention；
- GNN：Hamilton、CS224W、Gilmer message passing、GIN；
- SSM：Boyd EE263 → *The Annotated S4* → S4 → Mamba → Mamba-2；
- DEQ：*Deep Implicit Layers Tutorial* → DEQ 原论文 → Kelley 的非线性迭代方法；
- kernel 与语言模型系统：GPU MODE、Triton tutorials、Stanford CS336，均作为第二轮或专题资源。

本模块直接通向 SSM、implicit layer、IO-aware Attention 和现代 GPU lowering 的一手材料。

### 6.8 英文路线的最小书架

英文闭环按八组组织：

1. Erickson, *Algorithms*；
2. Lee–Seshia + Van Roy–Haridi 选读；Magee–Kramer 作为并发项目读物；
3. *Computer Systems: A Programmer's Perspective*；
4. Grama 等的 *Introduction to Parallel Computing* + Blelloch 的 prefix-sum 原文；PMPP 作为 GPU 项目书；
5. *Engineering a Compiler* + 免费的 *Static Program Analysis*；
6. *Streaming Systems* + *Designing Data-Intensive Applications*；
7. Prince, *Understanding Deep Learning* + English *Dive into Deep Learning*；
8. Hamilton, *Graph Representation Learning*；Kelley 和 implicit-layer materials 按 DEQ 项目查阅。

Van Roy–Haridi 和 Hamilton 都只按项目选章，不要求通读。以上书架本身就是完整英文线；不需要配套中文版解释。可以维护英中术语表并用中文写自己的证明，但定义、习题和引用以英文原文为准。

### 6.9 英文路线的十二个月阅读与练习表

下表只引用英文材料，并独立通向第 7 节全部项目。编程门槛未通过时，先完成 3.3 节的 2–4 周预备期。

| 时间 | 英文材料 | 证明与实现交付 |
| --- | --- | --- |
| Months 1–2 | Erickson, *Algorithms*, Basic Graph Algorithms and DFS；*Open Data Structures* only as needed；CLRS 4e as reference | `graph_core`；closed-book proofs of topological ordering, SCC partition and acyclic condensation；independent small-graph oracle |
| Month 3 | Lee–Seshia on state machines, composition and concurrent models；selected Van Roy–Haridi chapters；UDL/D2L on RNNs | timed state-machine simulator；one Graph under several models of computation；minimal RNN forward |
| Month 4 | Lee–Seshia on causality/feedback；Van Roy–Haridi on streams/message passing；D2L and *The Annotated Transformer* | `dag_executor` and random chunk-split tests；naive causal Attention prefill/decode comparison |
| Month 5 | Blelloch, “Prefix Sums and Their Applications”；CLRS parallel algorithms；*Structured Parallel Programming* as needed | `scan_lab` serial/Hillis–Steele/Blelloch/segmented scan；scalar/diagonal affine recurrence；work/span proofs |
| Month 6 | CSAPP performance and memory-hierarchy chapters；PMPP as needed | fixed benchmark protocol；locality and CPU profiling；one CPU lowering；GPU optional |
| Month 7 | *Engineering a Compiler* on IR, CFG, SSA, def-use and data-flow analysis | `mini_tide_ir` v1、SCC pass、state versions、read/write contract and reference interpreter |
| Month 8 | *Static Program Analysis* on lattices, constraints, fixed points and worklists；CMU Deep Learning Systems selected notes | monotone worklist analysis；one fusion/batching pass；source-vs-lowered validation and counterexamples |
| Month 9 | *Streaming Systems*；DDIA streaming chapters；Lee–Parks/Kahn/SDF selected readings | total-order integer-time `scc_stream_runtime` with source seal, `AdvanceUntil`, continuation, per-output-port scalar watermarks and replay |
| Month 10 | UDL/D2L on backprop, RNN and Attention；Baydin survey；Needle autodiff portion | `micro_autograd` core；canonical/numeric prefill-decode equality；gradient and chunk-boundary tests |
| Month 11 | Hamilton；*The Annotated S4*；*Deep Implicit Layers Tutorial* | choose GNN, structured affine SSM or implicit layer for a full six-part study；build only minimal forward prototypes for the other two |
| Month 12 | *Deep Learning Tuning Playbook*；relevant profiling/evaluation sections from the preceding materials | one falsifiable hypothesis、2–3 baselines/ablations and a `mini_tide_benchmark` measurement-pipeline pilot；claim-ledger audit |

这张表不把任何中文教材当作先修或回查材料。第一年完成的是可验证的语义与性能骨架；完整 S4/Mamba、DEQ、GPU backend 和大规模 learning-value 实验进入第二轮。

## 7. 七个 Tide 定向项目

这些项目是中文线与英文线共用的学习顺序和验收标准，不是第三条材料路线。无论选择 5.8 还是 6.9，都完成同名交付物。每个项目先写语义清晰的 CPU reference，再考虑优化；代码规模宁可小，也要能够穷举、对拍和解释。

### 7.1 `graph_core`：从有向图到 condensation DAG

**实现：**

- adjacency list 与反向图；
- BFS、DFS 和小图可达性；
- Kahn 与 DFS topological sort；
- 先实现较直观的 Kosaraju SCC，再把 Tarjan 作为第二实现；
- condensation DAG；
- 随机小图生成器，以及独立实现的 Floyd–Warshall/transitive-closure oracle。

**亲自证明：**

1. 有限有向图有拓扑序当且仅当它无环；
2. “互相可达”是等价关系，因此 SCC 构成顶点划分；
3. 把每个 SCC 缩成一点后不可能仍有有向环。

**反例：**

- 有向环使拓扑排序失败；
- 只看无向连通分量不能替代 SCC；
- SCC 缩点不证明 SCC 内部会终止；
- condensation 是 DAG 不代表 critical path 很短。

**通过标准：**

- 对顶点数不大的所有或大量随机图，用暴力可达性矩阵验证 SCC，并覆盖 self-loop、平行边和不连通图；
- 验证缩点图中的每条跨分量边，并再次运行拓扑排序；
- 第一轮能闭书解释 Kosaraju 的正确性；第二轮能精确定义并解释 Tarjan 的 low-link invariant；
- 为一个加权 DAG 计算总 work `W` 与最长依赖路径 `S`，再模拟 `P` 个处理器的 ready-queue list scheduling，直接观察“无环”和“并行度高”不是一回事。

### 7.2 `dag_executor`：逐时刻 reference 与 whole-window 执行

先定义最小消息记录：

```text
message_id
edge_id
src_node / src_port
dst_node / dst_port
send_logical_time
arrival_logical_time
payload
```

再实现两种执行器：

1. **逐逻辑时间 reference**：外层遍历 logical time，内层按空间拓扑序处理节点；
2. **whole-window executor**：外层按空间拓扑序，单个节点一次处理窗口内的时间桶。

节点必须显式声明：

- 同一时间、不同 port 消息如何融合；
- 状态何时读、何时提交；
- 是否会在空时间桶推进状态；
- 出站消息的逻辑时间规则；
- 窗口末尾需要保留的 continuation。

**比较的 artifact 不能只有最终输出：**

- 每个可观察输出；
- 最终持久状态；
- route/message trace 的规范化结果；
- 尚未越过窗口边界的在途消息；
- timer、pending event 等 continuation。

**核心测试：**

- 随机生成小 DAG、节点函数和输入窗口；
- 比较两种执行器；
- 对同一长输入随机选择 cut，比较一次执行与多段执行；
- 对声明为 schedule-independent 的 profile，随机更换合法拓扑序后仍产生等价 artifact；
- 加入一条反向语义依赖，确认循环交换不再被错误接受。

本项目的目标是亲自感受：拓扑序只解决空间依赖顺序；窗口算子是否等于逐时刻 fold，仍是额外语义义务。

拓扑序置换测试成立还要求：没有未声明的共享可变状态；同刻融合和消息排序已经确定；独立操作可交换，或 trace 按明确的交换等价关系比较；拓扑序本身不属于模型语义。对声明为 order-sensitive 的 profile，不能用这项测试错误地拒绝合法程序。

### 7.3 `scan_lab`：理解 Line 上何时存在高性能 prefill

依次实现：

- serial fold；
- Hillis–Steele scan，用于建立直觉；
- Blelloch exclusive/inclusive scan；
- segmented scan；
- 依次对 scalar、diagonal、block/structured affine transition 做组合与 scan；
- dense affine transition 只作为语义与成本对照；
- CPU 并行版，最后才是 PyTorch/Triton 或 CUDA 版。

对

$$
h_{t+1}=A_t h_t+b_t
$$

把一步转移表示成 `(A_t,b_t)`，亲自推导

$$
(A_2,b_2)\circ(A_1,b_1)
=(A_2A_1,\ A_2b_1+b_2),
$$

再证明复合满足结合律，并用 scan 得到所有前缀状态。但“函数复合满足结合律”本身远远不够；work-efficient scan 还要求：

- 每一段可由大小可控的 summary 表示；
- summary 对 combine 封闭；
- combine 足够便宜；
- 每一步 summary 可从输入并行得到，而不是必须由前一状态逐步揭示；
- 总 work、存储和通信相对 serial reference 可接受。

**必须给出的账本：**

- serial fold 的 work 与 span；
- 在 unit-cost combine 模型下，说明 Hillis–Steele 为 `O(L\log L)` work、`O(\log L)` span，Blelloch scan 为 `O(L)` work、`O(\log L)` span，并记录额外存储；
- segmented scan 如何处理多个独立序列；
- 稠密矩阵、对角矩阵和标量情形的运算量差别；
- 实际 memory traffic 和墙钟结果。

对一般稠密 $d\times d$ 的 $A_t$，serial matrix–vector update 通常是 $O(Ld^2)$ work；直接组合 affine summary 涉及 matrix–matrix multiplication，朴素可达 $O(Ld^3)$ work，summary 本身也有 $O(d^2)$ 大小。因而“affine”不自动意味着 work-efficient；Mamba 的 selective scan 也依赖受限状态结构，不适用于任意 input-dependent dense transition。

**关键反例：**

- 为一个非结合运算强行改变括号次序；
- summary 大小随 segment 长度增长，或 combine 比 serial step 昂贵；
- 下一步算子或访存地址只能由前一状态揭示，因而不能预先生成 step summary；
- 未纳入 summary 的副作用；
- 浮点加法虽在实数模型中结合，机器浮点重排后不逐 bit 相同；
- 理论 span 较低，但小 shape 上同步与 launch overhead 更大。

data-dependent early exit 本身不是无条件反例：若停止标志能纳入紧凑状态并保持封闭、便宜的 combine，它仍可能形成 monoid；必须检查具体状态表示和成本。

这个项目是理解“空间拓扑仍是一条 Line，但不同节点转移具有完全不同的 prefill 性质”的最小实验。

### 7.4 `mini_tide_ir`：把语义义务变成可分析的 IR

设计一个很小的文本或 Python IR，显式记录：

- node、port、edge 与 logical-time rule；
- state namespace 与 state version；
- read set、write set；
- phase、visibility 与 commit；
- message production/consumption；
- observable artifact 与 continuation。

然后实现：

- SCC pass 与 condensation；
- reaching definitions 或 liveness；
- 基于 lattice/worklist 的单调分析；
- 一项局部 fusion 或 batching pass；
- source executor 与 lowered executor 的 translation validation。

**证明与反例：**

- 从 bottom/适当边界值初始化，用 join 形成单调上升更新；状态变化后重新调度依赖项，并采用公平 worklist。在有限高度 lattice 和单调 transfer function 下，证明迭代终止，并在标准数据流方程条件下得到相应 least fixed point；
- 若抽象域有无限升链，说明为什么还需额外收敛条件或 widening；不要把 fixed-point solution 与 distributive framework 中的 meet-over-all-paths 精确性混为一谈；
- 非单调 transfer function 如何破坏推理；
- 隐式 alias、不同 commit order 或被丢失的 pending message 如何使 fusion 不合法；
- static analysis 的 fixed point 与神经网络 DEQ 的数值 fixed point 为什么不是同一个问题。

优化器本身不必先被完全形式化证明。早期可对每个具体 lowering 运行差分验证；但 validator 必须针对明确的 observable contract。

### 7.5 `scc_stream_runtime`：finite cut、continuation 与长期运行

第一版只使用**全序整数逻辑时间**、标量 cut 和“每个输出 port 一个标量”的 hard output watermark。在 `dag_executor` 之上加入：

- SCC 宏节点和多入口、多出口 port；
- timed event priority queue；
- source seal 与至少一类严格正 delay edge；
- `AdvanceUntil(b)`；
- continuation 与逐输出 port 的 scalar hard output watermark；
- checkpoint/replay；
- 物理实现层的 bounded queue 与 backpressure。

精确完成 cut `b` 不能只看“队列暂时为空”，也不能只收到上游 watermark。至少要同时建立：

1. 所有外部输入源都已 seal 到 `b`，以后不会再到达时间 `<b` 的输入；
2. 队列、在途消息、timer、内部 pending event，以及仍被 operator 持有的生产能力都不可能再产生时间 `<b` 的事件；
3. cut 之前的事件数有限，且这些事件的求值会在有限工作后终止；
4. 所有跨越 cut 的状态、消息和能力都已完整进入 continuation。

第二版才引入偏序时间与 Timely-style progress capability。此时完成边界通常是 antichain/progress frontier 或已封闭 down-set，不再只是一个标量 `cut`；这里的 capability 是进展与未完成工作记账，不是 Tide 的五类 execution capability。需要另读 Naiad/Timely 的 progress tracking，不能只从 *Streaming Systems* 的 event-time watermark 推出。

可再实现两个最小 computation-model 对照，但必须保留各自契约：

- **简化 KPN**：确定性的顺序 process；point-to-point、保持顺序且概念上无界的 FIFO；blocking read、nonblocking write；不测试 channel emptiness。相应语义可理解为 Scott-continuous stream functions；
- **简化 SDF**：固定 production/consumption rate 先给出 topology 与 balance equations；正整数 repetition vector 只是 consistency 条件，还要找到 admissible、deadlock-free periodic schedule，才能进一步分析该 schedule 的 buffer bound。

bounded queue/backpressure 属于物理 realization，不应静默改写 KPN 的概念上无界、nonblocking-write 语义。在有环网络中，有限容量可能引入原模型没有的人工死锁；除了验证“不丢消息”，还要验证结果保持条件，并记录哪些容量下发生 deadlock。

还要区分：

- **structural SCC**：完整静态 Graph 上的强连通分量，用于宏节点与 condensation；
- **zero-delay SCC**：同一逻辑时间、zero-delay 依赖形成的环，用于 causality 检查；
- **Zeno 行为**：有限逻辑时间区间内产生无限事件，不等同于“存在 zero-delay edge”。

未声明求值语义的 zero-delay SCC 应拒绝；若声明了 constructive synchronous semantics、唯一 fixed point/root solve，或有界 micro-step kernel，则 zero-delay feedback 也可能合法，但存在性、唯一性、收敛、成本和微分都是额外义务。

**至少测试三类 SCC：**

1. **最终静止**：有限输入后可以 `RunToQuiescence`，并达到 `quiescence-total`；
2. **整体永久运行但 finite-prefix productive**：不能整体算完，却能在有限工作后封闭每个指定 cut；
3. **无合法完成证书**：未解决的 zero-delay loop、Zeno-like event generation，或无法排除未来产生更早输出。

还要加入：

- 固定 `R` 轮信息传播，验证展开为 layered DAG；
- 同一个 SCC 在不同 cut 处停止并接续；
- checkpoint/replay 保存持久状态、pending/in-flight message、timer、source offset/seal、逐 port scalar progress state、RNG 状态，以及具有语义意义的调度信息；第二版再加入 Timely-style progress capability 与 progress frontier；
- replay 后按事先声明的标准比较 artifact：逐项相同，或在允许交换的独立事件下 trace 等价；
- bounded realization 的结果保持与容量死锁测试；
- 一个工程估计 watermark 过早前进的反例。

本项目的完成标准不是“所有有环 Graph 都能跑得快”，而是能够对每一类 SCC 明确声明：

```text
termination / productivity contract
+ progress certificate
+ continuation schema
+ reference semantics
+ specialized kernel（若存在）
```

### 7.6 `neural_semantics_lab`：把系统语义连接到神经算子

这个项目可拆成五个小实验。

#### A. `micro_autograd`

- scalar computation DAG；
- shared-subgraph gradient accumulation；
- reverse topological traversal；
- VJP，JVP 可后置；
- finite-difference gradient checker。

亲自证明 reverse mode 的链式法则，并构造“共享节点梯度未累加”“原地修改破坏 saved value”“拓扑顺序错误”等测试。

#### B. RNN 与 Attention

- 字符级 RNN/GRU；
- naive causal attention；
- whole-prefix prefill；
- 带 KV cache 的逐 token decode；
- chunked prefill。

先关闭 dropout，并固定 position ID、causal mask、dtype 和 evaluation semantics。比较每个位置的 canonical output、canonical KV/state 与 chunk-boundary continuation；物理 cache layout 若不属于 observable contract，就先规范化后再比较。分别声明：

```text
实数模型中的语义等价
≠ 同一算法在 atol/rtol 下的浮点等价
≠ 不同 kernel 的逐 bit 等价
```

之后再单独研究训练态随机数、浮点归约重排和 kernel 数值误差。

#### C. SSM

- scalar → diagonal → block/structured affine recurrence 的 serial/scan；
- dense affine transition，只作为语义与成本反例；
- segmented scan；
- LTI 情形的 convolution/FFT，可后置；
- input-dependent selective recurrence。

交叉验证输出、末状态和梯度，并记录哪些结构提供紧凑、封闭且便宜的 summary。对 LTI 的 convolution/FFT 等价，显式声明固定的 `A,B,C`、有限 prefix、初始状态项与 terminal state；只算出卷积输出不自动得到 streaming continuation。

#### D. 固定轮 GNN

- node-by-node reference；
- synchronous `K`-round executor；
- `(node, round)` layered DAG；
- gather/scatter bulk executor。

只在下列前提下证明节点重编号的 permutation equivariance：node/edge update maps 在相应类型内共享；邻居 aggregation 对输入多重集的排列不变；节点、边、edge feature 与输入/输出索引一起一致重标号；readout 也具有声明的 equivariance/invariance。分别移除这些前提，构造最小反例。

验证固定 `K` 轮等价于有限 DAG 展开时，另需限定空间图有限、每轮只读前一轮已提交状态、node/edge maps 每轮产生有限事件，且 `K` 是预先给定的有限值。再用反例说明异步原地更新通常不等于同步 message passing；不得把这个受限结论提升为任意 GNN 或一般 Graph 的展开定理。

#### E. DEQ / implicit layer

对

$$
z^\star=f_\theta(z^\star,x)
$$

依次实现 Picard iteration、Anderson 或 Broyden、有限展开反传、implicit differentiation 和有限差分验梯。分别记录：

- forward residual $\lVert f(z^\star,x)-z^\star\rVert$、迭代数与停止原因；
- backward linear-system residual、迭代数与停止原因；
- tolerance sweep；
- double-precision directional finite difference 或 `gradcheck`；
- Jacobian/spectral-radius 的诊断性估计。

必须分开回答：

1. 数学上是否存在、是否唯一；
2. 求解器是否在给定预算内收敛；
3. forward 与 backward 误差是否足以支持稳定梯度与训练。

Contraction 是保证存在、唯一和 Picard 收敛的一组充分条件，不是必要条件；局部 implicit differentiation 需要 $f$ 可微且 $I-\partial f/\partial z$ 可逆。有限轮 unrolled model 与 equilibrium model 是不同目标，未充分收敛时不应期待梯度相等。保留不收敛、多个 fixed point、容差过松和 iteration cap 的反例。

### 7.7 `mini_tide_benchmark`：检验 learning value

实验方法按所选路线独立取材：

- **中文线**：Goodfellow、Bengio、Courville《深度学习》中文版第 11 章“实践方法论”，以及 OpenMLSys 的 profiling 内容；
- **英文线**：Goodfellow et al., *Deep Learning*, Chapter 11，以及 Google Research 的 *Deep Learning Tuning Playbook*：<https://github.com/google-research/tuning_playbook>。

英文 Tuning Playbook 不属于中文第一轮的必需材料；进入前沿研究后仍应按第 8 节核验英文一手来源。

不要先规定每个任务都比较五类模型。先写一个可证伪的 learning hypothesis，再选择与该命题最相关的 2–3 个强 baseline，以及去掉 feedback、routing 或持久状态的 ablation；只有第一轮结果值得追踪时，才扩大到 Transformer、GRU/RNN、结构化 affine-scan SSM、固定轮 GNN 和 Tide 原型的更完整比较。

候选任务包括 delayed/selective copy、associative recall、pointer chasing、长度外推和组合式图任务。不同任务需要不同的强 baseline；固定轮 GNN 不必被强行放进不适合它的纯序列任务。不要一开始用大规模语言建模掩盖机制问题。

每项实验至少分栏报告：

- 参数量；
- 训练 token 与 optimizer steps；
- 估算 FLOPs；
- 墙钟、峰值显存和可得时的能耗；
- 多随机种子；
- train/validation/test 划分、超参数调优预算、model-selection rule 与失败 run；
- 优化稳定性；
- 长度外推与组合泛化；
- 动态路由或迭代是否真的被使用；
- reference 与 optimized runtime 的数值偏差。

参数量、训练 token、FLOPs 和墙钟通常不能同时匹配。每个实验应预先声明主要公平性约束，例如 compute-matched、token-matched 或 wall-clock-matched，其余指标只报告而不声称同时受控。动态模型另报告实际 iteration 数、active node/event/message 数、route entropy/load balance、solver tolerance 与失败率。

性能测量至少固定：

```text
hardware / software version
dtype / shape / batch
warm-up 与首次编译是否排除
device synchronization
重复次数、median 与离散程度
memory allocation 是否计时
correctness tolerance
```

必须把“算法成本”和“当前实现的硬件效率”分开；也必须把“模型 learning value 不足”和“当前 kernel 太慢导致训练预算不足”分开。放弃高性能 prefill 的 streaming-only 架构仍可做 learning-value pilot，但结论必须绑定它实际获得的训练计算与数据预算。第一年的结果只称作“机制与测量链路 pilot”，不能据此宣称一般泛化、智能或 scaling 优势。

## 8. 英文路线的原论文阶梯与第二轮研究桥

本节属于英文路线；中文路线第一轮不依赖本节。这里用原论文核对各研究谱系真正承诺了什么，推荐先读综述，再读经典语义，最后读 Tide 最接近的现代系统。

“中文线与英文线都独立完整”是指两者都能在第一轮形成知识骨架并完成同一组证明、reference 和测试。进入研究前沿后，核验 KPN、SDF、Naiad、S4、Mamba、DEQ、FlashAttention 等原始契约仍必须阅读英文一手文献；中文线不能被描述成永远无需英文即可完成最新文献研究。

### 8.1 Dataflow、编译分析与 logical progress

| 顺序 | 材料 | 阅读时只追问的核心问题 |
| ---: | --- | --- |
| 1 | Lee、Parks, “Dataflow Process Networks” | KPN、SDF、dynamic dataflow 的假设如何不同？ |
| 2 | Kahn, “The Semantics of a Simple Language for Parallel Programming” | 确定性来自 blocking read、FIFO 和连续函数中的哪些条件？ |
| 3 | Lee、Messerschmitt, “Synchronous Data Flow” | 固定 rate 如何给出 balance equation；consistency、可接受的周期 schedule 与 buffer bound 还各需什么条件？ |
| 4 | Lee、Sangiovanni-Vincentelli, “A Framework for Comparing Models of Computation” | 应如何比较计算模型，而不是只比较 Graph 外形？ |
| 5 | Blelloch, “Prefix Sums and Their Applications” | 结合律、紧凑封闭 summary 与便宜 combine 怎样共同给出 work-efficient parallel prefix？ |
| 6 | Kildall, “A Unified Approach to Global Program Optimization” | lattice、数据流方程与 worklist fixed point 的契约是什么？ |
| 7 | Murray 等, “Naiad: A Timely Dataflow System” | partially ordered logical time、progress tracking 和 logical progress frontier 如何工作？ |
| 8 | Akidau 等, “The Dataflow Model” | event time、window、trigger、watermark 如何分工？ |
| 9 | Benveniste 等, “The Synchronous Languages 12 Years Later” | zero-delay feedback、同步反应与 constructiveness 的边界是什么？ |
| 10 | Dao 等, “FlashAttention” | algorithmically exact（不近似）Attention、IO complexity 与 GPU lowering 如何共同产生高性能 prefill；为何浮点重排仍不保证逐 bit 相同？ |

读每篇论文只写一页：

```text
研究对象
前提
结论
不保证什么
最小可运行例子
与 Tide 的可用映射
不能直接类比的地方
```

### 8.2 神经架构专题顺序

**自动微分：**

1. Baydin 等, “Automatic Differentiation in Machine Learning: a Survey”；
2. CMU Deep Learning Systems 的 autodiff notes 与 Needle 作业。

**Attention：**

1. “Attention Is All You Need”；
2. FlashAttention；
3. Transformer-XL，在研究跨段记忆与 continuation 时选读；
4. FlashAttention-2，作为性能深化。

**GNN：**

1. Hamilton 教材的 message-passing 主线；
2. Gilmer 等, “Neural Message Passing for Quantum Chemistry”；
3. Xu 等, “How Powerful Are Graph Neural Networks?”。

**SSM：**

1. Boyd EE263 中 linear dynamical systems；
2. *The Annotated S4*；
3. S4；
4. Mamba；
5. Mamba-2 / “Transformers are SSMs”。

HiPPO 和 S5 在需要追溯状态构造与多输入 scan 时再读。不要把复现完整 S4 kernel 当成入门任务。

**DEQ：**

1. *Deep Implicit Layers Tutorial*：<https://implicit-layers-tutorial.org/>；
2. Bai、Kolter、Koltun, “Deep Equilibrium Models”；
3. Multiscale DEQ；
4. Kelley, *Iterative Methods for Linear and Nonlinear Equations*，按求解器问题查阅。

## 9. 两条路线共用的时间边界与学习验收点

中文路线的逐月表见 5.8，英文路线的逐月表见 6.9；不再提供把两套书混在一起的第三张表。两张表均按每周 8–10 小时设计。编程诊断未通过时，先增加 2–4 周预备期；第一年深做系统主轴并穿插最小神经语义原型。`neural_semantics_lab` 五个子实验的完整六联件、完整 `mini_tide_benchmark`、偏序时间、GPU backend 和大规模训练属于 18–24 个月路线。

### 9.1 共用的三个学习验收点

**第 2 月后：**

- 能从头实现 SCC；
- 能证明 condensation 为 DAG；
- 不再把“无环”误说成“低 span”或“高性能”。

**第 6 月后：**

- 能区别语义等价、work/span 与机器性能；
- 能亲自推导 affine composition，并判断某种结构是否具有紧凑、封闭、便宜的 summary；
- 能解释 Attention 的 causal-bulk 结构与 SSM 的 scan-composable recurrence 为什么以不同方式获得高吞吐 prefill。

**第 9 月后：**

- 能为全序整数时间上的一个 SCC 写出 source seal、termination/productivity、cut、continuation 与逐 port scalar progress contract；
- 能区分整体完成、有限前缀完成和 best-effort streaming；
- 能说明何时 SCC 只是图分解，何时还有专用求值器。

## 10. 何时才算“掌握”

对 Tide 而言，能复述教材不算掌握。至少应能独立完成以下口试：

1. 给一个有向图，手算 SCC、condensation 与两种合法拓扑序；
2. 解释静态空间 Graph、动态 event DAG 和物理 schedule 的区别；
3. 给出一个 DAG：拓扑遍历正确，但 span 仍为线性；
4. 给出一个 Line recurrence：它不仅有结合的复合，还具有可预先生成、紧凑封闭且 combine 足够便宜的 summary，因此能 work-efficient 地用 scan 降 span；
5. 给出一个 SCC：整体永不结束，但每个有限 cut 都能完成；
6. 给出一个未解决的 zero-delay loop：既没有普通拓扑顺序，也没有 constructive、fixed-point 或有界 micro-step semantics；
7. 解释 compiler fixed point、DEQ fixed point 和 runtime 开放循环的对象为何不同；
8. 写出 `prefill = decode` 应比较的 canonical output、state、route/message 与 continuation，并声明实数、浮点容差或逐 bit 等价中的哪一层；
9. 说明一次 property test、一次复杂度证明和一次 profiling/benchmark 各自能支持什么结论；
10. 为一个“更聪明”的动态图架构设计能证伪 learning-value 假设的对照实验。

如果其中某题只能复述 AI 的措辞，尚未形成自己的感知；应退回最小例子、手算和 reference implementation。

## 11. 与 AI 协作的学习协议

AI 最适合做陪练、审稿人、反例生成器和代码 reviewer，不应代替第一次证明。推荐按以下顺序：

1. 先让 AI 只给定义来源、必要前置和三道递进问题；
2. 自己闭书写证明或算法，不先看完整解答；
3. 让 AI 寻找证明漏洞，并要求给最小反例；
4. 自己修订后，再让 AI 给另一种证明；
5. 自己先写 reference，AI 只做 code review 和测试建议；
6. 用独立 oracle 或两种算法对拍，避免 AI 同时生成实现和“同源测试”；
7. 优化后，让 AI 帮助审查语义差异、复杂度账本和 benchmark 公平性；
8. 最后做一次口头答辩：要求 AI 连续追问前提、边界和反例。

每个学习条目建议使用统一笔记模板：

```markdown
# 概念或命题

## 我的定义
## 原始来源与准确表述
## 前提
## 我的证明
## 破坏前提后的最小反例
## Reference implementation
## Optimized implementation
## Property tests
## Work / span / memory 账本
## Profile 与硬件条件
## 对 Tide 可用的结论
## 不能推出的结论
## 未解决问题
```

还应维护一份 claim ledger，为每个研究判断记录：

- claim；
- 来源或自己的证明；
- 依赖前提；
- 证据类型；
- 当前状态：定义、猜想、已证明、仅实验支持、已反驳；
- 最小复现实验或代码位置。

这能直接缓解 AI 共创笔记中“措辞很确定，但理解、来源或前提仍有歧义”的问题。

## 12. 第一周如何开始

通过 3.3 节诊断后，第一周只做有向图，不碰 GPU，也不需要先搭大框架；未通过则先完成 2–4 周预备期。

### 选择一条阅读入口

**中文线：**

- 《算法导论》中图的表示、BFS/DFS、DAG 与拓扑排序；
- 《离散数学及其应用》中关系、偏序和数学归纳只按需查漏。

**英文线：**

- Erickson 第 5 章 *Basic Graph Algorithms*，再进入第 6 章 *Depth-First Search*；
- 若基础数据结构不熟，只查 *Open Data Structures* 的对应部分。

二者选一，不在第一周同时阅读。

### 证明

闭书写出：

> 一个有限有向图存在拓扑序，当且仅当它没有有向环。

分别尝试：

- 用入度为零的点做归纳证明；
- 用 DFS finishing time 给出构造性证明；
- 把 DFS 证明拆成两个引理：有向图含环当且仅当 DFS 发现指向灰色祖先的 back edge；在 DAG 中每条边 $u\to v$ 满足 $finish(u)>finish(v)$；
- **选做边界题**：比较有限图上的 Kahn 归纳、无限偏序的抽象线性扩张与按 $0,1,2,\ldots$ 枚举的拓扑序。例：顶点 $\mathbb N$、边 $n+1\to n$ 无有限环，却没有源点，也不能按自然数位置枚举出尊重全部边的序列；这不否定适当选择原则下的抽象线性扩张。

### 实现

- adjacency list；
- Kahn topological sort；
- DFS topological sort；
- cycle witness 必须是一条闭合有向路径，而不是只返回 `False` 或 Kahn 剩余顶点集；Kahn 失败后可在剩余子图中再做 DFS 取 witness；
- 随机生成小图，用独立的 transitive closure/Floyd–Warshall oracle 对两种实现做对拍。

### 周末验收

不看笔记回答：

1. 为什么 Kahn 算法卡住意味着剩余子图有环？
2. DFS 中哪类边构成 cycle witness？
3. 同一 DAG 为什么可以有多个拓扑序？
4. 拓扑序为什么只证明已声明的静态跨节点依赖可以线性化，而不单独证明节点操作有定义且终止、所有语义依赖都已显式，更不证明可以高性能 prefill？

第二周再进入 SCC；不要为了追赶书目跳过第一周的证明、反例和对拍。

## 13. 路线的最终目的

完成这条路线后，理想状态不是知道更多术语，而是能把一个新的 Tide 构型拆成一组可独立审查的问题：

```text
它的 reference semantics 是什么？
静态 Graph 与一次执行的 event graph 各是什么？
有限输入是否终止；若不终止，有限 cut 是否 productive？
SCC 宏节点的接口、continuation 和 progress certificate 是什么？
正确的 window execution 是否存在？
是否有 batching / matmul / scan / fixed-round / solver 等 execution witness？
work、span、memory traffic 与实际吞吐分别是多少？
训练时机制是否可学、是否被使用、是否改善泛化？
```

届时，与 AI 的合作也会从“接受一段听起来合理的说明”，转变为共同维护定义、证明义务、实现、反例、证据等级和真正未决的研究问题。
