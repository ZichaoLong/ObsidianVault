---
type: memo
status: draft
tags:
  - tide
  - prefill-decode
  - logical-event-dag
  - dynamic-runtime
  - zero-delay-loop
---

# Finite Event DAG And Zero-Delay Loops Memo

> [!note] 术语边界
> 本 memo 中的空间节点/空间边属于静态图，事件顶点/事件依赖边属于一次动态执行；`token` 是外部输入位置和值，不是计算轨迹；逻辑秩描述依赖推进方向，不等于消息 `owner`。选择器所谓“激活节点”统一理解为产生路由/消息，并使未来节点事件在消息到达后实例化，而不是创建静态空间节点。

## Position

本文记录一项尚未正式并入 Tide 数学主线的判断：

> 对有限 chunk，reference computation 应能展开为 dependency-complete logical event DAG。DAG 是承载有限执行因果结构的核心规范形；动态路由、循环 static graph、data packing 和乱序执行可以改变物理表示，但不能隐去 reference-visible 的依赖、状态可见性与 commit order。

这里的目标不是声称“所有语义等价证明只能使用 DAG”，也不是把任意有限计算平凡地塞进一个巨型节点。需要同时满足语义可审计性与工程可用性。

## Current Alignment

当前对齐结论是：

1. CFG loop、SSA $\phi$ 与 MemorySSA `MemoryPhi` 不是 finite logical event DAG 观点的反例。它们是 static cyclic representation；加入 dynamic iteration / memory-version index 后，有限执行依赖仍从较早实例指向较晚实例。
2. Tide static graph 可以有环，selector 也可以在线决定路径；strict runtime 的约束对象是每次有限 execution 产生的 logical events，而不是要求 static topology 本身无环。
3. logical time 是语义要求。底层 kernel 可以接收原始输入位置、绝对轮次、阶段与并列键，也可以接收由这些 metadata lowering 得到的 mask、segment、packed offset 或 sparse layout；消息 `owner` 单独作为归属字段处理。
4. 同一 logical rank 内的 zero-delay SCC 不存在普通 topological schedule。strict core 应默认拒绝；若确有任务需要，必须显式封装为具有独立 fixed-point contract 的 implicit kernel。
5. 当前优先目标不是寻找无约束的全局充分必要条件，而是建立 finite logical event DAG representation、local refinement sufficiency、zero-delay cycle dichotomy 与 non-degenerate performance witness 四层结果。

因此，zero-delay loop 对近期 Tide 的主要价值是提供 causality verifier 与负向设计约束，而不是成为默认支持的计算机制。

## Integration Boundary

本文保留完整推演，但不同内容应进入不同正式文档：

| 内容 | 正式归属 | 当前状态 |
| --- | --- | --- |
| finite logical event DAG representation、local refinement、zero-delay dichotomy | [[step-transition-mathematical-specification]] | [[token-owned-general-dag-routing]] 已证明固定周期 closed-finite spatial-DAG 特例；continuation-state embedding 与一般 dynamic/cyclic 情形尚未证明 |
| EventId、LogicalRank、Dependency、StateVersion、SCC verifier | [[step-transition-implementation-specification]] | 已成为目标接口，尚未由当前 runtime 完整实现 |
| 当前代码已有对象与缺口 | [[current-architecture-state]] | 以代码快照为准 |
| ISA、SSA/MemorySSA、scheduling、dataflow、fixed-point 历史谱系 | [[logical-event-dag-related-theories]] | 参考材料，不替代 Tide 证明 |

因此，本 memo 后续可以被拆分吸收，但在对应定义和定理完成前不应删除；它承担设计审计与问题边界记录。

## 1. 为什么有限 chunk 是更强的应用基础

Tide 后续需要动态性：

- 哪些空间边被选择、哪些未来节点事件会实例化，可能由 selector 或 controller state 决定。
- 从输入到输出不一定存在预先固定的单一路径或有限路径集合。
- 同一个静态空间图可以在不同输入位置、内部轮次和阶段上产生不同的动态事件执行。
- kernel 可以把多个 logical events pack、batch、fuse 后执行。

但正常 prefill 调用只处理有限 token 序列。若一次调用还满足以下条件：

1. internal round 数有限，或运行时有有限 event budget；
2. 每个 kernel 调用终止；
3. selector 不产生无限的同一逻辑时刻递归事件实例化；

那么该次调用只产生有限 logical event 集合。

注意：有限长度输入本身不自动推出有限执行。若 dynamic runtime 可以无限增加 internal round，或 fixed-point iteration 不收敛，则仍可能产生无限执行。Tide strict family 因而还需要终止性证明、单调推进的 logical rank，或显式有限 budget。

## 2. 有限 logical event DAG 的规范表述

给定长度为 $L$ 的有限 chunk，令 $\mathcal{N}_L$ 是该次参考执行中实际产生的有限逻辑事件实例集合。沿用统一对象模型，把事件写成事件头和值的有序对：

$$
e=(h_e,\nu_e),
$$

其中事件头为：

$$
h_e=(\eta_e,\kappa_e,\ell_e,\theta_e,\Omega_e,c_e).
$$

各字段分别表示：

- $\eta_e$：事件实例标识符。
- $\kappa_e$：事件种类。
- $\ell_e$：外部位置、空间节点、空间边或已声明子图位置。
- $\theta_e$：由语义 profile 定义的逻辑时间戳。
- $\Omega_e$：事件直接处理或在外部接口上标识的归属支持集。
- $c_e$：事件值的输入前缀依赖上界。
- $\nu_e$：事件值，其中可以包含数值产物、状态提交、路由记录和消息记录。

内部轮次、阶段与微步若属于时间语义，应进入 $\theta_e$ 或逻辑秩；role/type 若决定事件类别，应进入 $\kappa_e$ 或显式类型字段。状态版本、选择器来源信息和消息来源关系不应塞进一个无结构的 metadata 坐标，而应由事件值与后续依赖边明确表示。

给定 dependency relation：

$$
\mathcal{E}_L\subseteq\mathcal{N}_L\times\mathcal{N}_L
$$

若 $(e,e')\in\mathcal{E}_L$，表示 $e'$ 的 reference semantics 需要 $e$ 产生的 value、control decision、state version、visibility result 或 commit order。

称：

$$
D_L=(\mathcal{N}_L,\mathcal{E}_L)
$$

是 dependency-complete logical event DAG，当且仅当：

1. $D_L$ 有限且无有向环。
2. 每个 event 的所有 reference-visible 输入都有显式 producer、boundary input 或 state-version 来源。
3. 所有会影响 observable output、persistent state、visibility、exception、I/O 或 future routing 的顺序约束都被 edge、path 或 event 内部顺序表达。
4. 被省略的依赖必须有独立的 independence、commutativity、non-aliasing 或 semantics-preserving quotient 证明。

有限 DAG 等价于有限事件上的良基因果偏序的一种边表示。真正核心的对象是因果偏序；DAG 是它最直接、最适合 scheduling 与 lowering 的有限表示。

## 3. 动态 runtime 不需要预先知道完整 DAG

dynamic execution 可以在线产生 event，而不必在 prefill 开始前枚举完整路径。逻辑秩应由语义 profile 明确给出。例如 step-complete profile 可取：

$$
\rho_{\mathrm{step}}(e)
=
(\text{external step},\text{internal round},\text{phase},\text{microstep}),
$$

固定周期 streaming profile 可取：

$$
\rho_{\mathrm{stream}}(e)
=
(\text{absolute round},\text{phase},\text{semantic tie},\text{microstep}).
$$

消息 `owner` 与因果前沿不是默认时间字段；只有配置 O 明确以 `owner` 消解同刻并列时，它才进入 `semantic tie`。

这里 `semantic tie` 是参考语义为同一逻辑时间戳内必须有序的事件指定的确定性并列键；`microstep` 是阶段内部仍需展开多个有序子事件时使用的可选坐标。二者都不能由物理线程完成顺序临时生成，严格术语边界见 [[token-owned-general-dag-routing#时间与边界|时间与边界]] 与 [[token-owned-general-dag-routing#执行、调度与性能|执行、调度与性能]]。

并给 rank 空间规定良基的字典序。runtime 只允许产生满足下式的依赖：

$$
(e,e')\in\mathcal{E}_L
\Longrightarrow
\rho(e)<\rho(e')
$$

选择器输出可以动态决定 $e'$ 是否会在未来实例化、连接哪些前驱，或选择哪些空间边并产生后继消息；它不创建或销毁静态空间节点。一旦建立事件依赖，该依赖必须指向更大的 logical rank。这样可以增量构造 DAG，而不要求静态路径固定。

这里的时间 metadata 是语义要求，不一定要求每个底层数值 kernel 都接收若干独立整数 tensor。编译器或 runtime 可以把相应逻辑秩 lowering 为：

- segment offset。
- causal mask。
- packed row index。
- CSR / block-sparse layout。
- batch descriptor。
- 已验证的固定 schedule。

但这些物理表示必须足以恢复 kernel 所需的 logical partition 与 visibility。不能只依赖物理 arrival order。

## 4. DAG 为什么重要，但不能单独成为充分必要条件

### 4.1 过弱的必要性

任何有限、终止的顺序程序都可以按实际执行顺序建立 chain DAG。也可以把整个计算放进一个 `RunEverything` 节点。因此，“存在某个 DAG”几乎是平凡事实，不能单独说明存在并行性、可组合性或高性能实现。

### 4.2 工程可用的充分条件

更有用的充分条件需要同时固定：

1. reference semantic contract。
2. logical event granularity。
3. 与问题长度无关的 admissible primitive family。
4. dependency-complete logical event DAG。
5. implementation node 对 reference event / sub-DAG / quotient 的局部模拟关系。
6. output 与 final-state extraction 的交换条件。
7. work、span、memory、communication 与 representation conversion 成本。

这与当前 `Unified Contract-DAG-Quotient Theorem` 和 non-degenerate chunk certificate 的方向一致。

### 4.3 为什么全局充要条件不应成为第一目标

如果不固定 primitive family、event granularity 和 cost model，可以总是：

- 把整个 reference fold 放进一个 oracle node。
- 引入昂贵的全局编码与逆变换。
- 为某个固定输入专门构造一个函数。

此时形式上的必要充分条件会退化为“两个函数的输出相同”，对 runtime 设计没有约束力。

因此更现实的数学路线是：

1. 先证明 finite logical event DAG representation lemma。
2. 再证明 dependency preservation + local refinement 推出 chunk correctness。
3. 单独给出 zero-delay cycle 的判定与处理定理。
4. 用 non-degenerate / parallel-prefill witness 判断工程价值。

## 5. Node、Edge 与 Lowering 的核心性质

### 5.1 Node local refinement

每个 implementation node 应直接实现以下对象之一：

- 一个 reference event。
- 一个显式 reference sub-DAG。
- 一个 semantics-preserving quotient event。
- 一个经过证明的 batching / fusion / scan primitive。

若 reference event value 为 $v_n$，quotient value 为 $\widehat v_n=\alpha_n(v_n)$，则 quotient kernel 应满足局部交换关系：

$$
\alpha_n\circ F_n
=
\widehat F_n\circ
\prod_{m\in\operatorname{Pred}(n)}\alpha_m
$$

### 5.2 Edge dependency completeness

若 reference edge $(m,n)$ 表示真实数据、状态、控制或 commit dependency，则 lowering 后必须：

- 保留为 physical path；或
- 保留为 fused primitive 内部顺序；或
- 证明该依赖可以因 independence、commutativity、non-aliasing 或 quotient 被安全消除。

### 5.3 No Semantic Resurrection

若上层使用 many-to-one abstraction：

$$
\alpha:V\to\widehat V
$$

下游应直接在 $\widehat V$ 上实现所需语义，而不是通过昂贵的 reconstruction 恢复 fine representation，再运行原 kernel。

以：

$$
M=U\Sigma V^\top
$$

为例，乘积通常不能唯一恢复原始 $(U,\Sigma,V)$：符号、排列和重复奇异值子空间都带来不唯一性。如果 contract 只观察 $M$，乘法是合法 quotient，无需恢复因子；如果 contract 观察原始因子，则信息已经丢失；如果 contract 观察 canonical SVD，重新分解是在实现另一个 contract。

即使某个编码可逆，逆变换成本也必须进入 cost ledger。语义正确性不能自动升级为工程价值。

## 6. ISA、编译器与依赖图的准确类比

本节只保留与 Tide 设计直接相关的结论。更完整的历史、术语解释和原始参考统一见 [[logical-event-dag-related-theories]]。

### 6.1 ISA 与乱序执行

ISA 给出 architectural transition contract，而不是一张 DAG。乱序处理器在有限 instruction window 内构造或近似维护 dynamic producer-consumer dependencies：

- register renaming 消除 WAR / WAW false dependencies。
- reservation station / scheduler 选择 operands ready 的 operations。
- reorder buffer 保持 architectural commit 与 precise exception。
- load/store queue 预测 memory dependencies，并在预测错误时 replay。

所以物理执行可以推测、乱序甚至暂时漏掉一条 dependency，但被接受的执行最终必须满足 architectural dependency、validation 与 commit contract。有限 dynamic instruction execution 可以表示为 event DAG 或带 speculation / replay event 的扩展 DAG。

### 6.2 CFG、SSA 与 MemorySSA

CFG 可以有 loop back edge，因此 static CFG 不是 DAG。SSA 让 scalar definition 唯一并暴露 def-use，但 loop header 的 $\phi$ 可以引用前一动态迭代的 value，所以 static def-use representation 仍可含循环结构。MemorySSA 同样使用 `MemoryPhi` 表示来自 loop back edge 或 control-flow merge 的 memory version。

给 loop-carried value 增加 iteration index 后：

$$
v^{(i+1)}=F(v^{(i)},x^{(i)})
$$

依赖从 iteration $i$ 指向 $i+1$。对有限 iteration 数展开后，它成为 DAG。$\phi$ / `MemoryPhi` 不是 zero-delay algebraic loop；它们表示 control-flow merge 或跨动态迭代的 value selection。

### 6.3 Scheduling

basic block、trace 或已展开 region 的 instruction scheduling 常直接使用 dependency DAG。循环 scheduling 可以保留 cyclic dependence graph，并给 edge 标注 iteration distance；software pipelining / modulo scheduling 必须尊重 loop-carried recurrence constraints。对某次有限执行展开 iteration distance 后，仍得到 event DAG。

### 6.4 Memory model

memory model 通常不只是一张简单 DAG，而是 program order、reads-from、coherence、from-read、happens-before 等多种关系。合法执行常通过这些关系组合的 acyclicity 或一致性条件定义。它进一步说明，DAG 的关键不是图形本身，而是 dependency relation 是否完整表达 contract。

## 7. 什么是 Zero-Delay Algebraic Loop

普通循环的 back edge 跨越 iteration、tick、round 或 state commit。例如：

$$
x_{t+1}=F(x_t,u_t)
$$

它有明确 delay，有限展开后是 DAG。

zero-delay algebraic loop 则在同一个 logical instant 内出现：

$$
x=F(y,u)
$$

$$
y=G(x,u)
$$

没有 register、state version、token tick、round tick 或 phase barrier 把两条依赖分开。此时不存在普通 topological order；语义必须额外解释为 simultaneous equations 或 fixed point：

$$
z=H(z,u)
$$

仅写出这个方程还不够。还需要回答：

- fixed point 是否存在。
- 是否唯一。
- 多个 fixed points 时选择哪一个。
- solver 是否终止或收敛。
- 有限精度与停止条件是否属于 reference contract。
- 不同求解顺序是否得到相同结果。

## 8. Zero-Delay Loop 在相关领域的位置

| 领域 | 普通处理 | 对 Tide 的启发 |
| --- | --- | --- |
| Combinational circuit / HDL | combinational loop 通常被综合与 static timing analysis 拒绝；有状态反馈必须经过 register / latch | strict graph edge 应跨越显式 state/delay；不要让同一 logical instant 出现隐式反馈 |
| CFG / SSA / MemorySSA | loop back edge 与 $\phi$ 表示下一动态迭代，不是 simultaneous equation | 给 token / round / iteration 编号后展开为 DAG |
| Synchronous languages | Lustre 等通过 `pre` / delay 打断反馈，并进行 causality check；Esterel 使用 constructive causality 区分可解释与不可解释的瞬时循环 | 可以把 causality check 作为 Tide graph verifier 的参考，但不必直接继承完整同步语言语义 |
| Synchronous dataflow | cycle 通常需要 initial token / delay 才能开始 firing；无初始 token 的 blocking cycle 可能 deadlock | mailbox cycle 需要显式 initial state 或 delay event |
| Simulink / Modelica / DAE | algebraic loop 被识别为 simultaneous nonlinear equations，由专门 solver 在每个 time step 求解 | 若 Tide 真要支持，应成为显式 `FixedPointKernel`，而不是普通 graph cycle |
| Deep equilibrium / implicit layer | 定义 $z^*=F(z^*,x)$，通过 root/fixed-point solver 求平衡点，并用 implicit differentiation 训练 | 这是 Tide 可选的独立研究方向，但与 strict event-DAG prefill 不是同一个 kernel family |

zero-delay loop 因此不是编译领域完全无关的例外。它位于 causality analysis、combinational-cycle detection、dataflow scheduling、implicit equation solving 的交界处。它的主要启发是：

> compiler/runtime 不能只看到 graph cycle 就假设它表示普通 recurrence；必须区分 delayed cycle 与 instantaneous SCC。

## 9. SCC 视角下的统一处理

任意有限 directed graph 都可以分解为 strongly connected components。把每个 SCC 收缩为一个节点后得到 condensation DAG。

对 Tide，同一个 logical rank 内的 SCC 可以分成：

1. singleton 且无 self-loop：普通 event。
2. cycle 中至少有一条显式 delay / state-version edge：给 delay 增加 rank 后，dynamic unfolding 成为 DAG。
3. 真正的 zero-delay SCC：不存在 topological schedule，必须拒绝或封装为 simultaneous / fixed-point kernel。

若引入显式 `FixedPointKernel`，其 reference contract 至少应写成：

$$
z^*=F(z^*;u)
$$

$$
y=G(z^*,u)
$$

并声明 fixed-point selection rule。若实际 runtime 只运行固定 $K$ 次 iteration：

$$
z^{(j+1)}=F(z^{(j)};u),
\quad j=0,\ldots,K-1
$$

那么工程实现的精确 reference semantics 是 $K$-step iteration，而不是理想 fixed point。此时给 internal iteration 增加 $j$ 后，计算再次成为有限 DAG。

## 10. 对 Tide Runtime 的直接约束建议

### 10.1 Strict core

1. Tide static graph 可以有环。
2. 每条 cycle 必须跨越显式 token、round、phase、state commit 或 delay boundary。
3. 每个 dynamic event 必须有 logical id 和 rank。
4. runtime 创建 dependency 时必须验证 rank 单调增加。
5. dynamic selector 可以决定 event 是否存在，但不能创建同 rank 的未声明 cycle。
6. kernel packing 可以改变 layout，不得丢失 logical partition、visibility 与 commit provenance。
7. strict core 拒绝 zero-delay SCC。

### 10.2 Optional implicit family

若未来任务确实需要 equilibrium、implicit layer 或 DAE-like computation，再单独加入：

```text
FixedPointKernel
RootSolveKernel
ImplicitStateKernel
```

这类 kernel 必须有独立的 existence、uniqueness、selection、termination、cost 与 differentiation contract。它们不应成为普通空间节点计算与消息传递 runtime 的默认逃生口。

### 10.3 Static-first prototype

早期先实现 static graph execution 是合理的，但 event contract 应与未来 dynamic runtime 一致：

```text
EventId
LogicalRank
ReadSet / WriteSet
StateVersion
VisibilityScope
CommitEvent
```

这样 static executor 只是预先知道 event generation policy；dynamic executor 则在线生成相同类型的 event。prefill correctness theorem 不需要因为路径动态化而彻底重写。

## 11. 建议的数学推进顺序

### 11.1 Finite Logical Event DAG Representation Lemma

证明：若一次 Tide execution 产生有限 event，且每条 dependency 严格增加良基 logical rank，则 dynamic event graph 是有限 DAG。

### 11.2 Local Refinement Sufficiency Theorem

证明：若 reference logical event DAG dependency-complete，implementation 对每个 event / sub-DAG 给出局部模拟或 semantics-preserving quotient，所有 reference edges 被保留为 path、内部顺序或已证明安全地消除，且 extraction commute，则 chunk implementation 与 reference fold 等价。

### 11.3 Zero-Delay Cycle Dichotomy

证明：同一 logical rank 的 dependency cycle 不存在 topological evaluation。要获得确定 semantics，必须至少选择以下一种：

1. 加入 delay / state boundary。
2. 把 SCC 定义为具有独立语义的 simultaneous / fixed-point kernel。
3. 判定 program 非法。

### 11.4 Engineering Witness

在 correctness 之外继续要求：

- uniform primitive family。
- no-oracle / no hidden reconstruction。
- work / span / memory / communication ledger。
- 与 sequential decode baseline 的实际或渐近比较。

这四层比直接追求无约束的全局充分必要条件更可用，也更接近 ISA、compiler scheduling、SSA/MemorySSA 与 dataflow runtime 的成熟实践。

## References

- Ron Cytron et al., "Efficiently Computing Static Single Assignment Form and the Control Dependence Graph", ACM TOPLAS 1991. https://doi.org/10.1145/115372.115320
- LLVM MemorySSA documentation. https://llvm.org/docs/MemorySSA.html
- Robert M. Tomasulo, "An Efficient Algorithm for Exploiting Multiple Arithmetic Units", 1967. https://doi.org/10.1147/rd.111.0025
- B. R. Rau, "Iterative Modulo Scheduling", MICRO 1994. https://doi.org/10.1145/192724.192731
- Edward A. Lee and David G. Messerschmitt, "Synchronous Data Flow", Proceedings of the IEEE 1987. https://doi.org/10.1109/PROC.1987.13876
- MathWorks, "Algebraic Loop Concepts". https://www.mathworks.com/help/simulink/ug/algebraic-loops.html
- Shaojie Bai, J. Zico Kolter, Vladlen Koltun, "Deep Equilibrium Models", NeurIPS 2019. https://arxiv.org/abs/1909.01377
