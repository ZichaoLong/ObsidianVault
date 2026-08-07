---
type: background-and-references
status: reference
tags:
  - tide
  - compiler-semantics
  - dataflow
  - neuroscience
  - references
---

# Tide 背景、历史谱系与参考资料

> [!summary] 本页定位
> 本页只提供研究谱系、工程类比、设计启发和外部参考，不承担 Tide 数学定义或证明。正式对象必须在 [[tide-mathematical-foundations]] 或 [[adaptive-routing-prefill-lower-bound]] 中重新声明，不能从本页隐式导入。

> [!warning] 类比边界
> ISA、编译器、SSA、MemorySSA、dataflow 与人脑网络都能提供有价值的结构性启发，但它们不是 Tide 正确性或可训练性的证据。特别是，脑科学调查描述真实生物网络，并不要求数字模型直接复制反馈环、皮质柱或脑区连接。

## 第一部分：ISA、编译器与 dataflow 理论谱系



### Position

> [!summary] 本页定位
> 本部分是 [[tide-mathematical-foundations]] 的外部理论与工程谱系参考。读者不需要预先掌握 CPU ISA、编译器、SSA 或分布式数据流；每节只提炼对 Tide 有用的最小概念、适用边界与原始参考。类比本身不构成 Tide 定理的证明。dynamic event DAG 与 zero-delay 的 Tide-specific 规则见 [[tide-mathematical-foundations#第四部分：有限事件展开与 zero-delay 边界|有限事件与 zero-delay 边界]]。

`Logical Event DAG Theorem` is not meant to be a mathematically novel theorem. Its core is a specialization of several mature ideas:

- deterministic evaluation of a DAG is independent of the chosen topological order;
- logical time matters more than physical arrival time;
- deterministic dataflow systems can be scheduled asynchronously when their semantic dependencies are preserved;
- high-performance prefill requires additional kernel algebra, such as batched maps, masked matmul, or associative scan.

The value in Tide is the specialization:

```text
autoregressive model / graph neural runtime
+ external input position and boundary contract
+ internal round tick
+ phase
+ spatial graph + dynamic event/message instances
+ chunk prefill correctness
```

The theorem separates two questions:

- Correctness: does chunk execution compute the same logical event graph as decode fold?
- Performance: do the kernels in that graph admit known high-throughput implementations?

### Theory Map

| Theory | Core idea | Relation to Tide | Boundary |
| --- | --- | --- | --- |
| ISA contract and out-of-order execution | Hardware may execute instructions out of program order, but must retire results as if the ISA program order had been respected. | Strong analogy for separating reference semantic contract from physical execution schedule. Tide's decode fold / logical event DAG plays the role of architectural semantics; chunk runtime is the optimized micro-execution. | CPU instructions have a mature fixed ISA and precise exception model; Tide kernels, state, provenance, and quotient boundaries are still research objects. |
| Compiler IR and SSA | Make data dependencies, definitions, and control/dataflow easier to analyze and transform. | Suggests that Tide needs an explicit IR: logical event ids, state namespaces, read/write sets, phase barriers, and provenance tags. | SSA makes analysis tractable; it does not solve aliasing, memory ordering, floating point, or arbitrary semantic equivalence. |
| Static cyclic IR and dynamic unrolling | CFG loops, SSA phi nodes, and loop-carried dependencies can be cyclic statically while each finite dynamic execution advances iteration/time. | Supports allowing cyclic Tide topology while requiring a finite dependency-complete logical event DAG for each terminating execution over a finite chunk. | Finite input does not imply termination; event generation still needs a bound or well-founded rank. |
| Abstract interpretation | Replace concrete semantics with a sound abstract semantics through abstraction maps. | Direct analogy for `alpha`, semantic quotient, sufficient statistics, and safe aggregation. | Usually gives useful sufficient conditions, not complete conditions for all optimizations. |
| Translation validation | Validate a specific optimized program against a source program instead of proving the whole optimizer correct. | Practical route for Tide lowerings: fusion, packed/crossbatch layout, backend-specific kernels, and phase rewrites. | The validator needs a precise IR semantics; hard cases remain floats, memory/state effects, undefined behavior, and solver scalability. |
| Verified compiler | Mechanically prove that a compiler preserves source semantics. | Long-term analogy for a verified Tide core subset. | High assurance but expensive; probably realistic only for a small core, not the whole experimental runtime at first. |
| Memory models and alias analysis | Define which reads/writes may be reordered or optimized without changing observable behavior. | Maps to Tide state namespaces, mailbox lifetime, commit order, selector side effects, and provenance-sensitive aggregation. | Memory models are notoriously subtle even in mature systems; Tide should avoid implicit state semantics. |
| DAG topological evaluation | A deterministic DAG can be evaluated in any topological order with the same result. | This is the proof core of `C_L = Fold_T^L` when chunk execution preserves the same logical event DAG. | It proves correctness only, not high performance. |
| Causality analysis and algebraic loops | Instantaneous dependency cycles have no ordinary topological schedule and need delay, rejection, or fixed-point semantics. | Gives a verifier rule for same-rank SCCs and separates ordinary recurrence from optional implicit kernels. | Fixed-point existence, uniqueness, convergence, cost, and differentiation are separate obligations. |
| Lamport logical time | Logical ordering of events is more fundamental than wall-clock completion order. | `message_id / owner / absolute_round / phase / spatial_node` must remain separate metadata; only the declared timestamp/order fields determine logical time. | Logical clocks do not by themselves define model kernels or state semantics. |
| Kahn process networks | Deterministic processes communicate over channels; results can be independent of scheduling. | Supports the intuition that asynchronous graph execution can be deterministic if communication semantics are disciplined. | KPN assumes specific blocking stream semantics; LH/Tide message aggregation may not satisfy them. |
| Synchronous dataflow | A static graph can be scheduled predictably when production/consumption rates are known. | Useful for fixed internal rounds, phases, and graph schedules. | Tide may have selectors, sparse event instantiation, or data-dependent routing beyond static SDF. |
| Timely dataflow / Naiad | Messages carry logical timestamps; operators reason over partially ordered logical time. | Very close to separating message identity, owner labels, profile-specific timestamps, and spatial location. | It is a distributed dataflow execution model, not an autoregressive-model proof by itself. |
| Parallel prefix / scan | Sequential recurrences can be parallelized when updates compose associatively. | This is the high-performance proof path for Mamba / SSM / linear attention accumulators. | It applies only to recurrences with suitable algebraic structure. |
| Database provenance | Query results can carry provenance explaining which inputs contributed. | Closest analogy for why untagged aggregation can destroy message-instance and input influence relations. | Provenance frameworks are usually for databases, not neural runtime kernels. |
| CALM / confluence | Order-independent distributed results require monotonic or coordination-safe structure. | Supports the distinction between safe aggregation and arrival-order-dependent kernels. | CALM is about distributed consistency, not chunk prefill directly. |
| Differential Dataflow | Collections carry timestamps and differences; incremental operators preserve logical time. | Strong analogy for timestamped collections and trace/arrangement maintenance. | It assumes dataflow collection semantics, not arbitrary neural state mutation. |

### 0. Architecture And Compiler Semantics Lineage

The closest analogy is not that Tide is a CPU or a compiler. The useful analogy is the mature discipline around:

```text
reference semantics
high-performance implementation
semantic preservation proof or validation
```

This lineage is valuable because it shows a pattern that appears repeatedly:

```text
do not optimize against intuition;
optimize against an explicit semantic contract.
```

#### 0.1 ISA Contract And Out-Of-Order Execution

For a CPU, the architectural contract is the ISA-level program behavior. A high-performance implementation may pipeline, speculate, rename registers, reorder instructions, and execute many operations in parallel. Correctness means the committed architectural state is the same as if the program had executed according to the ISA's reference order.

For Tide, the corresponding separation is:

```text
reference semantic contract = transition / decode fold / logical event DAG
physical execution = chunk runtime / packed layout / parallel kernels / out-of-order messages
```

The same deep issue appears in a different concrete form:

```text
Can the implementation change physical order
without changing the reference-visible state and output?
```

In CPU terms, this is handled by architectural state, dependency tracking, reorder buffers, commit order, and precise exceptions. In Tide terms, the corresponding tools are logical event ids, profile-specific timestamps, separate `owner/frontier` labels, explicit message production/consumption relations, semantic quotients, output / final-state extraction, and step simulation.

This analogy clarifies why the reference semantic contract matters. If the architectural contract only observes a coarse state, then the implementation only needs to reproduce that coarse state. If the contract exposes fine-grained provenance, then an implementation cannot freely erase it.

Relevant sources:

- Robert M. Tomasulo, "An Efficient Algorithm for Exploiting Multiple Arithmetic Units", IBM Journal of Research and Development, 1967. DOI: https://doi.org/10.1147/rd.111.0025
- John L. Hennessy and David A. Patterson, "Computer Architecture: A Quantitative Approach".

#### 0.2 Compiler Optimization As Semantics-Preserving Translation

A compiler optimization pass usually does not preserve every internal detail of the source program. It preserves the source language or IR's observable behavior:

```text
source program
  -> optimization / lowering
target program
```

Correctness is judged against the chosen semantics:

```text
same observable output
same required memory/state behavior
same permitted nondeterminism / undefined behavior boundary
```

This is directly useful for Tide. A Tide lowering pass may fuse kernels, pack sparse rows, batch tokens, reorder graph evaluation, or lower to a device backend. It does not need to preserve every temporary mailbox or workspace representation. It must preserve the reference semantic contract: outputs and persistent state, up to explicitly declared abstraction maps and numeric tolerances.

The warning is also direct. If the contract is vague, optimization becomes ungrounded. In C/LLVM, undefined behavior, poison values, aliasing, and floating-point flags shape which transformations are legal. In Tide, the analogous danger points are provenance loss, selector side effects, phase visibility, state namespace aliasing, commit order, and floating-point reordering.

Relevant sources:

- LLVM Language Reference Manual: https://llvm.org/docs/LangRef.html
- LLVM MemorySSA documentation: https://llvm.org/docs/MemorySSA.html

#### 0.3 IR, SSA, And Explicit Def-Use Structure

Static Single Assignment form makes each variable definition syntactically unique and exposes def-use structure. Its value is not that hardware works this way. Its value is that optimization and analysis become tractable.

The Tide analogue is a disciplined IR:

```text
logical event id
state namespace
read set / write set
phase barrier
message production / consumption relation
declared provenance fields
value type / quotient boundary
```

SSA suggests a design principle:

```text
make dependencies explicit before optimizing them.
```

For Tide, this means a chunk runtime should not rely on implicit physical arrival order or hidden mutation if we later want to prove prefill/decode equivalence. Values that matter for future kernels should have explicit names, timestamps, or state slots. If a value is intentionally compressed, the compression should be represented as a quotient, not as an accidental implementation detail.

MemorySSA is especially relevant because ordinary SSA handles scalar values more cleanly than mutable memory. Tide has the same issue: numerical node activation values are comparatively easy; persistent state, mailbox mutation, selector counters, caches, and readout memory need a separate read/write model.

SSA does not make an entire program statically acyclic. CFG loop back edges remain, and a loop-header phi may select a value produced by the previous dynamic iteration. MemorySSA likewise uses `MemoryPhi` at control-flow joins and loops. Once a finite execution is indexed by dynamic iteration or memory version, those dependencies point from an earlier instance to a later instance and can be represented as a finite logical event DAG. This static/dynamic distinction is the relevant lesson for Tide.

Relevant sources:

- Ron Cytron et al., "Efficiently Computing Static Single Assignment Form and the Control Dependence Graph", ACM TOPLAS 1991. DOI: https://doi.org/10.1145/115372.115320
- LLVM MemorySSA documentation: https://llvm.org/docs/MemorySSA.html

#### 0.4 Abstract Interpretation And Semantic Quotients

Abstract interpretation gives a disciplined way to reason about abstraction:

```text
concrete semantics
  -- alpha -->
abstract semantics
```

The abstract semantics does not recover concrete details. It is useful only if it soundly preserves the properties being asked.

This is the closest mature theory to Tide's `alpha` / quotient idea. If a runtime aggregates several messages into a summary, correctness is not obtained by reconstructing the lost provenance. Correctness is obtained only when the summary is a sufficient abstract value for every downstream kernel and final-state extraction required by the reference contract.

This also explains why a universal necessary-and-sufficient condition is unlikely to be the first practical target. Mature abstract interpretation often builds useful abstract domains that give sound sufficient conditions. Completeness is domain-specific and usually expensive.

Relevant source:

- Patrick Cousot and Radhia Cousot, "Abstract Interpretation: A Unified Lattice Model for Static Analysis of Programs by Construction or Approximation of Fixpoints", POPL 1977. Paper page: https://www.di.ens.fr/~cousot/COUSOTpapers/POPL77.shtml

#### 0.5 Translation Validation And Alive2

Verified compilers try to prove the optimizer correct once and for all. Translation validation takes a more local route:

```text
given source IR and optimized IR,
check this transformation instance is semantics-preserving.
```

This is probably the most practical near-term analogy for Tide. Instead of trying to prove every future Tide optimizer correct, we can define a small IR and validate each transformation class:

- topological reorder of a logical event DAG;
- token-wise map fusion;
- associative scan lowering;
- packed / crossbatch layout change;
- backend kernel replacement;
- phase rewrite or barrier movement;
- semantics-preserving aggregation quotient.

For a Tide implementation, this maps to:

```text
reference artifacts
optimized artifacts
state equivalence relation
step simulation
random differential tests
SMT / Lean / specialized checker where feasible
```

Alive2 is a useful modern example because it checks LLVM optimizations against LLVM IR semantics. It also demonstrates the hard parts: precise IR semantics, memory model details, poison/undef behavior, floating-point flags, and solver bounds.

Relevant sources:

- Amir Pnueli, Michael Siegel, Eli Singerman, "Translation Validation", TACAS 1998. DOI: https://doi.org/10.1007/BFb0054170
- Alive2 online checker: https://alive2.llvm.org/ce/
- Nuno P. Lopes et al., "Alive2: Bounded Translation Validation for LLVM", PLDI 2021. DOI: https://doi.org/10.1145/3453483.3454030

#### 0.6 Verified Compiler As A Long-Term Upper Bar

CompCert shows that a realistic compiler can be mechanically verified to preserve semantics for a substantial C subset. This is the high-assurance end of the spectrum.

For Tide, this suggests a realistic long-term split:

```text
small verified core
larger experimentally validated runtime
backend-specific differential tests
```

The verified core might include:

- transition / fold semantics;
- logical event DAG evaluation;
- topological-order independence;
- semantic quotient conditions;
- step simulation;
- a few kernel families such as token-wise maps and affine scan.

The full Tide runtime, including selectors, sparse routing, device lowering, and mixed-precision kernels, is unlikely to be fully verified early. A smaller verified core plus validation tools is more realistic.

Relevant sources:

- CompCert project: https://compcert.org/
- Xavier Leroy, "Formal Verification of a Realistic Compiler", CACM 2009. PDF: https://xavierleroy.org/publi/compcert-CACM.pdf

#### 0.7 Memory Models, Alias Analysis, And Floating-Point Boundaries

Memory models show how hard it is to specify what reorderings are allowed. Even mature CPU and language ecosystems still need careful definitions for relaxed memory, data races, atomics, undefined behavior, and floating-point transformations.

The Tide equivalent is not one single memory model yet, but a cluster of semantic questions:

- Which state namespace does a kernel read?
- Which state namespace does it write?
- Is a mailbox step-local, round-local, or persistent across input positions?
- Can two writes commute?
- Does a selector update affect future routing?
- Is provenance observable by later kernels?
- Are floating-point reorderings allowed, and under what tolerance?

This suggests a strong design rule:

```text
state and visibility rules must be explicit before optimization.
```

Otherwise, a packed or parallel implementation may appear correct on final logits while silently changing selector state, cache state, provenance, or future behavior.

Relevant sources:

- Peter Sewell et al., "x86-TSO: A Rigorous and Usable Programmer's Model for x86 Multiprocessors", CACM 2010. DOI: https://doi.org/10.1145/1785414.1785443
- LLVM Language Reference Manual: https://llvm.org/docs/LangRef.html

#### 0.8 Practical Lessons For Tide

The mature lesson is not "find one perfect theorem and finish the problem." The practical pattern is:

1. Define a precise semantic contract.
2. Design an IR that exposes the dependencies needed for optimization.
3. Prove reusable sufficient conditions for important transformation families.
4. Validate concrete transformations when global proof is too expensive.
5. Keep backend implementation below the semantic layer.

For Tide, the corresponding stack should be:

```text
reference semantic contract
-> logical event DAG / B-family IR
-> sufficient transformation rules
-> validation / simulation layer
-> CPU / Ascend / packed backend
```

This is why a useful theory does not need to solve all necessary-and-sufficient conditions. Compiler and architecture history suggests that a well-chosen IR plus sound sufficient rules plus validation tools can be both scientifically meaningful and practically useful.

### 1. DAG Evaluation And Topological Order

The minimal mathematical fact is simple: if every event-vertex value in a deterministic logical event DAG is a function of its predecessor event values, then any topological order computes the same event-vertex values. This use of “vertex” is distinct from a reusable spatial node in the Tide graph.

For Tide, a step-complete decode fold gives one legal order:

```text
for input position t:
  for logical event e in the declared step-local reference order:
    compute e
```

Chunk prefill may use another order:

```text
batch many token-wise maps
run masked attention
run scan
fuse kernels
pack sparse rows
```

Correctness follows only if both procedures compute the same logical event DAG with the same equations and same final-state extraction.

This is why preserving logical dependency matters more than preserving physical execution order.

Relevant source:

- A. B. Kahn, "Topological sorting of large networks", Communications of the ACM, 1962. DOI: https://doi.org/10.1145/368996.369025

### Static Cycles, Dynamic Unrolling, And Zero-Delay SCCs

#### Static loop is not an instantaneous algebraic loop

A compiler CFG may contain a back edge, and a scheduling representation for a loop may contain recurrence edges. These edges normally carry an iteration distance: an operation in iteration $i+1$ depends on a value from iteration $i$. Adding the dynamic iteration index turns the finite execution into an acyclic event relation.

This is also how Tide should interpret ordinary recurrence:

```text
static graph cycle
+ token / round / iteration delay
-> finite dynamic logical event DAG
```

The same idea appears in modulo scheduling. The static loop dependence graph may be cyclic, but recurrence distance constrains the legal initiation interval; it does not mean that two operations in the same dynamic instant recursively require each other's result.

#### Zero-delay algebraic loop

A zero-delay loop has dependencies in the same logical instant:

```text
x = F(y, u)
y = G(x, u)
```

There is no topological order unless the strongly connected component is given additional simultaneous-equation or fixed-point semantics. Related systems handle this in different ways:

- hardware synthesis usually rejects unintended combinational loops;
- synchronous languages perform causality or constructiveness checks and use explicit delay operators for stateful feedback;
- synchronous dataflow cycles need initial tokens/delays to fire productively;
- Simulink / Modelica identify algebraic loops and invoke equation solvers;
- deep equilibrium models deliberately define an implicit fixed point and pay the solver/training cost.

For Tide, the near-term rule should be conservative: strict event execution rejects same-rank SCCs. A future implicit family may collapse such an SCC into an explicit `FixedPointKernel`, but then existence, uniqueness, fixed-point selection, finite execution, cost, and differentiation become part of that kernel's contract.

#### SCC condensation

Every finite directed graph can be condensed by strongly connected components into a DAG. This does not solve the semantics of a nontrivial SCC; it only localizes the problem. A Tide verifier can classify each SCC as:

1. ordinary acyclic event;
2. delayed recurrence whose edges advance logical rank;
3. same-rank zero-delay SCC requiring rejection or an explicit implicit-kernel contract.

Relevant sources:

- B. R. Rau, "Iterative Modulo Scheduling", MICRO 1994. DOI: https://doi.org/10.1145/192724.192731
- LLVM MemorySSA documentation: https://llvm.org/docs/MemorySSA.html
- Edward A. Lee and David G. Messerschmitt, "Synchronous Data Flow", Proceedings of the IEEE, 1987. DOI: https://doi.org/10.1109/PROC.1987.13876
- MathWorks, "Algebraic Loop Concepts": https://www.mathworks.com/help/simulink/ug/algebraic-loops.html
- Shaojie Bai, J. Zico Kolter, Vladlen Koltun, "Deep Equilibrium Models", NeurIPS 2019: https://arxiv.org/abs/1909.01377

### 2. Lamport Logical Time

Lamport's key point is that distributed systems need an event ordering relation that is not merely physical clock time. If event `a` can causally affect event `b`, then `a` must be logically before `b`.

This maps directly to Tide:

```text
wall-clock completion order != logical dependency order
```

一个 `owner` 较大的消息可以在墙钟时间上先完成或先写入缓冲区，但它必须携带足够的逻辑元数据：

```text
(message_id, owner_index, absolute_round, phase_id, source_spatial_node)
```

接收空间节点随后按逻辑时间戳分桶、排序、掩码或缓冲。这里 `owner_index` 是归属字段，`absolute_round + phase_id` 才构成逻辑时间；二者不能合并。

This is the conceptual basis for allowing out-of-order packed / parallel execution while still proving `C_L = Fold_T^L`.

Relevant source:

- Leslie Lamport, "Time, Clocks, and the Ordering of Events in a Distributed System", 1978. PDF: https://lamport.azurewebsites.net/pubs/time-clocks.pdf

### 3. Kahn Process Networks And Deterministic Dataflow

Kahn process networks show that a network of deterministic processes communicating through channels can have deterministic semantics even when execution scheduling is asynchronous.

The connection to Tide is useful but not exact:

- Similarity: asynchronous physical execution can still produce deterministic semantic results.
- Similarity: communication structure matters.
- Difference: KPN channels preserve stream order; LH-like aggregation may merge many messages into one value.
- Difference: Tide has token ticks, internal rounds, phases, state commits, and model-specific kernels.

This highlights the main risk for LH-like runtime:

```text
if messages are irreversibly aggregated without provenance,
the logical event relation may no longer be reconstructible.
```

Relevant source:

- Gilles Kahn, "The semantics of a simple language for parallel programming", IFIP Congress, 1974.

### 4. Synchronous Dataflow

Synchronous Dataflow studies graphs whose nodes consume and produce fixed numbers of data items. This enables static scheduling and predictable execution.

The connection to Tide is strongest when the runtime has:

- fixed external input boundaries;
- fixed internal round count;
- fixed phase order;
- fixed graph topology;
- fixed mailbox lifecycle.

This resembles the cleanest version of B0/B2:

```text
for external input step:
  for internal round:
    for phase:
      compute fixed graph operations
```

The limitation is that Tide/LH may introduce selectors, sparse event instantiation, and data-dependent routing. Once routing changes dynamically, SDF is no longer enough; logical event DAG semantics still apply, but static scheduling may not.

Relevant source:

- Edward A. Lee and David G. Messerschmitt, "Synchronous Data Flow", Proceedings of the IEEE, 1987. DOI: https://doi.org/10.1109/PROC.1987.13876

### 5. Timely Dataflow / Naiad

Naiad is especially relevant because messages carry logical timestamps, and computation proceeds over a partially ordered logical time domain.

This is close to what Tide needs for LH-like chunk prefill:

```text
message = message_id + value + owner + logical_timestamp + spatial_location
logical_timestamp = profile-specific rank fields
```

其中 `owner` 不是时间戳，空间位置也不是时间字段。保留这些相互独立的元数据后，物理交付可以乱序，而逻辑可见性仍可保持。

This is the closest existing system-level analogy to `Logical Event DAG Theorem`.

Relevant sources:

- Derek G. Murray et al., "Naiad: A Timely Dataflow System", SOSP 2013. PDF: https://www.cs.princeton.edu/courses/archive/fall22/cos418/papers/naiad.pdf
- Microsoft Research page: https://www.microsoft.com/en-us/research/publication/naiad-a-timely-dataflow-system/

### 6. Parallel Prefix / Scan

The logical event DAG theorem proves correctness if the chunk execution computes the same graph. It does not explain why chunk execution is faster.

The performance side comes from specific kernel families.

For recurrence:

```text
h_{t+1} = A_t h_t + b_t
```

we can represent the update as an affine map:

```text
g_t(h) = A_t h + b_t
```

and use associative composition:

```text
g_2 . g_1
```

This gives parallel prefix / scan, which is the core reason Mamba / SSM / linear attention accumulators can have high-performance prefill.

Relevant sources:

- Guy E. Blelloch, "Prefix Sums and Their Applications", 1990/1993. PDF: https://www.cs.cmu.edu/~guyb/papers/Ble93.pdf
- Mark Harris et al., "Parallel Prefix Sum (Scan) with CUDA", GPU Gems 3. NVIDIA: https://developer.nvidia.com/gpugems/gpugems3/part-vi-gpu-computing/chapter-39-parallel-prefix-sum-scan-cuda

### 7. Provenance And Safe Aggregation

The aggregation issue in Tide is close to database provenance.

If several logical events contribute to one aggregate, then later kernels may need to know:

```text
which token?
which round?
which phase?
which source node?
```

Tagged aggregation keeps that information. Untagged aggregation discards it.

This does not mean untagged aggregation is always invalid. It is valid if the aggregate is a sufficient statistic for all downstream kernels and final extraction. In mathematical terms, the runtime must provide a semantics-preserving quotient:

```text
reference event values -> aggregate value
```

and every downstream kernel must factor through that quotient.

Examples:

- Safe: summing same-event messages when the reference kernel only uses the sum.
- Safe: max aggregation when downstream only uses the max.
- Safe: histogram aggregation when downstream only uses bucket counts.
- Unsafe: merging token `t` and token `t+1` into one untagged vector when later output/state needs token-specific effects.
- Unsafe: physical first-arrival aggregation when reference semantics depends on logical order.

This maps to the database-provenance intuition: once provenance is dropped, some downstream questions become unanswerable unless the query is invariant to the dropped information.

Relevant sources:

- Todd J. Green, Gregory Karvounarakis, Val Tannen, "Provenance Semirings", PODS 2007. DOI: https://doi.org/10.1145/1265530.1265535
- Peter Buneman, Sanjeev Khanna, Wang-Chiew Tan, "Why and Where: A Characterization of Data Provenance", ICDT 2001. DOI: https://doi.org/10.1007/3-540-44503-X_20

### 8. CALM, Confluence, And Coordination

The CALM theorem says, roughly, that monotonic programs can be eventually consistent without coordination. The analogy to Tide is not exact, but it is useful.

Tide's equivalent question is:

```text
Can physical execution order vary without changing the logical result?
```

If aggregation is associative / commutative / idempotent and downstream kernels only depend on that aggregate, then reordering or batching may be safe.

If a kernel depends on:

```text
first arrived message
arrival order
unlabeled mix of different logical times
```

then physical schedule can affect semantics, and chunk prefill correctness is not generally provable.

Relevant source:

- Neil Conway et al., "Logic and Lattices for Distributed Programming", SoCC 2012. DOI: https://doi.org/10.1145/2391229.2391230
- Technical report PDF: https://db.cs.berkeley.edu/papers/UCB-lattice-tr.pdf
- Joe Hellerstein, "The CALM Theorem and Program Analysis for Distributed Consistency", CACM article: https://cacm.acm.org/research/keeping-calm/

### 9. Differential Dataflow

Differential Dataflow maintains collections indexed by logical time and differences. Its relevance is the same design pressure:

```text
keep timestamped structure long enough
to support correct incremental / out-of-order computation
```

For Tide, this suggests:

- message collections should preserve message identity, owner labels, logical timestamps, and required source relations;
- arrangements / indexes can be derived views, not semantic replacements;
- aggregation is safe only when it is a semantics-preserving quotient;
- physical compaction must preserve the queries future kernels need.

Relevant source:

- Frank McSherry et al., "Differential Dataflow", CIDR 2013. PDF: https://www.cidrdb.org/cidr2013/Papers/CIDR13_Paper111.pdf

### Implications For Tide

The current theoretical stack should be read as:

1. `Unified Contract-DAG-Quotient Theorem` composes transition-level semantic abstraction, logical event evaluation, and event-level quotient into one correctness gate.
2. `Non-Degenerate Chunk Certificate` prevents a vacuous one-node `RunFold` proof by requiring uniform primitives, explicit lowering, and a complete cost ledger.
3. Transformer / Mamba prove that important standard kernels can instantiate the correctness gate.
4. Their high performance comes from known kernel structures: matmul, causal masked attention, fused attention, prefix scan.
5. Compiler / architecture history suggests the right engineering shape: semantic contract, explicit IR, sufficient transformation rules, validation, then backend lowering.
6. General graph support requires preserving logical event provenance, or proving the lost information is a semantics-preserving quotient.
7. LH is a mechanism pool and golden reference, not a mandatory final contract. Mechanisms that block strict prefill may be modified, isolated, or replaced while retaining the local-communication and ultra-sparsity goals.
8. Static Tide topology may be cyclic, but each terminating strict execution over a finite chunk should admit a dependency-complete logical event DAG indexed by a profile-specific well-founded rank such as external step/internal round/phase/microstep or absolute round/phase/semantic tie.
9. Same-rank zero-delay SCCs are not ordinary scheduling problems; they require delay, rejection, or an explicit fixed-point contract.

The design pressure for Tide is therefore:

```text
reference semantic contract
+ explicit Tide IR
+ logical event metadata
+ deterministic visibility / commit order
+ tagged or provably safe aggregation
+ non-degenerate lowering certificate
+ work / span / memory / communication ledger
+ transformation validation
+ kernel-family-specific high-performance implementations
```

### Boundary Statement

The theorem does not say:

```text
any graph runtime has efficient prefill
```

The unified theorem says:

```text
if contract abstraction, logical event evaluation,
and event quotient all commute,
then chunk correctness holds for the chosen contract.
```

The compiler/architecture analogy adds:

```text
if a lowering changes representation or execution schedule,
it must either preserve the reference IR semantics directly
or pass through an explicitly declared semantic quotient.
```

Efficiency is a second proof obligation. It must be supplied by a non-degenerate certificate and the actual kernel family, not inferred from correctness alone.

Likewise, finite logical event DAG representability is a proposed Tide design gate, not yet a global theorem about all computation. It becomes useful only together with a declared event granularity, admissible primitive family, complete dependency relation, termination condition, and cost model.

---

## 第二部分：人脑信号传播调查


### 从感觉输入到思考、记忆、情绪与运动的调查报告

- **报告日期**：2026-07-22
- **范围**：正常成人脑的一般组织原则；重点讨论新皮层六层结构、皮质柱、丘脑-皮层与皮层下环路，以及视觉、听觉、躯体感觉、思考、电脑工作和体育运动。
- **证据口径**：以神经解剖学、神经生理学和综述文献为主。人脑无法进行许多动物实验中的侵入式记录，因此微回路细节有相当一部分来自啮齿类和非人灵长类；报告会标出重要的外推和争议。
- **非临床用途**：本文解释一般机制，不用于诊断具体神经系统疾病。

---

### 摘要：先直接回答核心问题

1. **“大脑皮层总共六层”只对典型新皮层大体成立。** 人类大部分大脑半球表面的新皮层通常分为 I 到 VI 层；但海马所属的古皮层、梨状嗅皮层以及小脑皮层并不是六层。运动皮层的 IV 层很不明显，初级视觉皮层的 IV 层则异常发达。

2. **感觉信号会跨皮层层次，但通常不会机械地依次走完 I→II→III→IV→V→VI。** 在初级感觉区，丘脑输入常偏向 IV 层，随后强烈影响 II/III 层，再影响 V、VI 层；但实际上存在大量跨层直达、同层、反馈和抑制连接。所谓“IV→II/III→V→VI”是有用的入门骨架，不是固定流水线。[2-4]

3. **皮质柱不是一个个相互串联的独立计算芯片。** 柱状组织在初级视觉皮层、啮齿类桶状皮层等处很清楚，但“整片新皮层由相同、边界清楚、功能统一的标准柱重复构成”并不是公认事实。柱的尺寸、边界和功能定义会随脑区、物种和实验方法改变。[5-7]

4. **真实传播是并行、分叉、汇聚和循环的。** 同一感官输入会同时进入多个皮层与皮层下通路；一个长程轴突也可能分叉到多个靶点。高级脑区不断把注意、预测、目标和情境反馈到较早脑区，因此不是“感官区处理完，再交给思考区”的单向接力。

5. **跨脑区主要依靠长程轴突，而不是信号沿皮层表面逐柱爬行。** 邻近区域之间有皮层内水平轴突和短 U 形纤维；远距离区域通过白质联络纤维、胼胝体等连合纤维及皮层-丘脑、皮层-脑干、皮层-脊髓等投射纤维连接。

6. **丘脑不只是“感觉中继站”。** 除嗅觉的初级皮层通路外，多数感觉信息在到达新皮层前经过丘脑；丘脑还参与注意、工作记忆、皮层区间协调和状态控制。大量皮层-皮层通信也可能经过“皮层→高阶丘脑→另一皮层”的路线。[12-14]

7. **“思考”没有唯一中心或固定路径。** 前额叶更像目标、规则、选择与控制网络的重要节点；思考的具体内容常分布在视觉、听觉、语言、顶叶、颞叶和记忆相关区域。工作记忆也不是只存放在前额叶，而是前额叶-顶叶控制与内容相关感觉皮层共同维持的动态状态。[27-30]

8. **产生动作依赖闭环，而不是一条运动指令。** 顶叶和前额叶形成目标，前运动区和辅助运动区组织动作，基底节参与选择和启动，小脑进行预测、时序和误差校正，初级运动皮层及脑干下行束驱动脊髓回路；视觉、前庭、本体感觉和触觉持续返回并修正动作。[38-46]

9. **海马、杏仁核和小脑都不是孤立模块。** 海马参与快速关系/情景记忆和皮层记忆重建；杏仁核参与生物学相关性、价值、威胁与学习；小脑参与运动和部分认知过程中的预测与校准。它们通过多级闭环反复影响皮层。

10. **最准确的总体图景是“动态网络”。** 结构连接决定可走的路，瞬时脑状态、注意、任务、学习史、神经调质和振荡相位决定某一时刻哪条路真正有效。连接图并不能单独推出思想或行为。

---

### 1. 先统一几个概念

| 概念 | 本文含义 | 容易混淆之处 |
|---|---|---|
| 大脑皮层 | 覆盖大脑半球的灰质，包括新皮层和较古老的皮层类型 | 不等同于整个大脑，也不包括所有皮层下核团 |
| 新皮层 | 人类大脑皮层的大部分，典型为六层 | 各脑区六层厚度和细胞组成差异很大 |
| 皮层层次 | 从软脑膜向白质方向排列的 I-VI 层 | “层”是组织学和连接学分类，不是六个串行处理阶段 |
| 皮质柱 | 大致垂直于皮层表面的细胞与连接组织单位或功能模块 | 没有适用于所有脑区的统一尺寸、边界和功能定义 |
| 脑区 | 依据细胞结构、连接、功能或地图划分的区域，如 V1、A1、M1 | 边界和命名依赖采用的图谱 |
| 前馈 | 相对由较早/较低层级区域指向较晚/较高层级区域的连接 | 不等于永远自下而上，也不一定只传“感觉数据” |
| 反馈 | 相对由较高层级返回较低层级的连接 | 可以传注意、预测、任务规则、记忆情境等多种影响 |
| 功能连接 | 两处活动在统计上协同变化 | 不必然代表直接轴突连接，也不能单独说明因果方向 |
| 再入/循环 | 信息经过多个区域后返回先前区域并继续改变处理 | 是正常脑功能的核心，不是多余“回路” |

---

### 2. 神经信号究竟是什么，怎样传播

#### 2.1 一个典型神经元链条

神经信号不是类似网线中的连续数字包，而是电活动、化学突触传递和群体状态的结合：

1. 上游神经元释放递质，改变下游神经元树突或胞体膜上的离子电导。
2. 兴奋性和抑制性突触后电位在空间和时间上整合。
3. 当轴丘附近达到放电条件，神经元产生动作电位。
4. 动作电位沿轴突传播；髓鞘和郎飞结使许多长程轴突能够快速跳跃式传导。
5. 动作电位到达轴突末梢，引发递质释放，再影响下一组细胞。

皮层长程投射神经元绝大多数是谷氨酸能兴奋性锥体细胞；GABA 能中间神经元多数在局部调节时序、增益、竞争和稳定性，但也存在少量长程抑制投射。化学突触占主导，电突触主要见于某些细胞之间的缝隙连接。

#### 2.2 信息不只由“是否放电”表示

神经系统可能同时利用：

- 一段时间内的平均放电率；
- 精确或相对放电时序；
- 哪些细胞共同活动形成的群体模式；
- 感受野、身体部位或空间位置形成的拓扑地图；
- 不同群体之间的相关性、低维群体轨迹和可通信子空间；
- 脑振荡相位所形成的兴奋性窗口。

“通信子空间”和“通过同步实现通信”分别有实验和理论支持，但它们不是已经穷尽脑通信机制的唯一答案。[48,49]

#### 2.3 发散、汇聚和递归

- **发散**：一个视网膜事件可同时影响外侧膝状体、上丘、顶盖前区和视交叉上核；一个皮层神经元的轴突也可出现侧支。
- **汇聚**：一个皮层锥体细胞整合来自局部细胞、丘脑、其他皮层区和神经调质系统的大量输入。
- **递归**：同一区域内部有大量复发连接；区域 A→B 后，B 常经直接或间接路径反馈 A。
- **选择性路由**：解剖连接长期存在，但其有效影响随注意、任务、抑制状态和神经调质改变。

因此，一个感觉事件没有唯一的“数据包路径”；更像同时激活一组相互耦合、不断回看和校正的网络。

#### 2.4 时间尺度

| 过程 | 典型量级 | 说明 |
|---|---:|---|
| 化学突触延迟 | 约亚毫秒至数毫秒 | 受突触类型和温度等因素影响 |
| 单条轴突传导 | 数毫秒至数十毫秒 | 取决于距离、直径和髓鞘化 |
| 最早皮层感觉响应 | 刺激后数十毫秒 | 听觉、躯体感觉、视觉及测量位置不同 |
| 跨区循环、识别和选择 | 数十至数百毫秒 | 不是严格分阶段，早期已存在反馈 |
| 有意识报告、复杂决定 | 数百毫秒至数秒以上 | 强烈依赖任务难度和准备状态 |
| 突触与系统学习 | 秒、分钟、天到多年 | 包括短时可塑性、长期可塑性和系统巩固 |

这些量级用于建立直觉，不应当被理解为每次任务都有相同的固定时间表。fMRI 的血氧信号通常在秒尺度变化，不能直接显示毫秒级神经传播顺序。

#### 2.5 神经调质：改变“网络工作模式”

多巴胺、去甲肾上腺素、乙酰胆碱和血清素等系统往往不是逐像素传递感觉内容，而是改变神经元增益、可塑性、探索/利用权衡、警觉、睡眠-清醒状态及奖励学习。它们可让同一套结构连接在不同状态下产生不同的信息流。[47]

---

### 3. 新皮层六层怎样工作

#### 3.1 六层不是六级流水线

新皮层从表面软脑膜到深部白质通常分为：

| 层 | 主要组织和常见连接倾向 | 在简化模型中的角色 |
|---|---|---|
| I 分子层 | 细胞体较少，含大量水平轴突、树突末梢和深层锥体细胞的顶树突；接受不少反馈及部分丘脑输入 | 整合远端反馈、情境和调节信号 |
| II/III 上颗粒层 | 多种锥体细胞和中间神经元；广泛连接局部、邻近/远端皮层及对侧半球 | 皮层-皮层前馈、侧向和连合通信的重要来源 |
| IV 内颗粒层 | 感觉皮层中富含颗粒/星形及小锥体细胞；初级感觉丘脑输入常较强 | 将丘脑感觉输入分配给局部回路，尤其 II/III 层 |
| V 内锥体层 | 大型锥体细胞；向纹状体、丘脑、上丘、脑干和脊髓等投射，也有皮层投射 | 皮层下输出、动作和状态影响 |
| VI 多形层 | 皮层-丘脑细胞和多种局部投射细胞；能影响 IV 层和丘脑 | 调节丘脑输入、形成皮层-丘脑闭环 |

这个表描述的是**连接偏好**，不是排他规则。丘脑可以直接影响 I、III、V、VI 层；II/III 层也能投射纹状体；V 层也可投射其他皮层；同层和跨层复发连接遍布各层。[2-4,12]

#### 3.2 一个有用但必须加警告的“典型微回路”

~~~mermaid
flowchart TB
    TH[感觉丘脑] --> L4[IV 层：主要感觉输入之一]
    L4 --> L23[II/III 层：局部整合与皮层间输出]
    L23 --> L5[V 层：皮层下及部分皮层输出]
    L5 --> L6[VI 层：皮层-丘脑调节]
    L6 --> TH
    L23 --> NEXT[其他皮层区]
    NEXT -. 反馈偏向 I 层及深层 .-> L1[I 层：顶树突与反馈整合]
    L1 --> L23
    L1 --> L5
    L5 --> SUB[纹状体、上丘、脑干、脊髓等]
~~~

这张图遗漏了大量真实连接。更准确的说法是：经典顺序给出了初级感觉皮层中较显著的一组连接倾向，但每一步都处在复发兴奋、局部抑制和长程反馈之中。[2,3]

#### 3.3 抑制性微回路为什么重要

皮层不是只有兴奋信号逐级放大。三类常用的中间神经元概括是：

- **PV 类**：常快速抑制胞体或近端树突，影响放电时间、竞争和网络增益。
- **SST 类**：常作用于远端树突，调节长程或顶树突输入的整合。
- **VIP 类**：常抑制其他抑制细胞，形成任务或状态依赖的去抑制。

这是功能倾向而非严格的一一对应；真实细胞类型远多于三类，人和鼠的细胞类型、形态及基因表达也不完全相同。[15]

#### 3.4 不同脑区的六层差别很大

- **V1 初级视觉皮层**：IV 层非常发达，并进一步细分；适合接收密集的外侧膝状体输入。
- **初级运动皮层 M1**：传统上称“无颗粒皮层”，IV 层较弱，V 层大型输出神经元突出。
- **前额叶**：不同亚区从颗粒型到无颗粒型连续变化，不能用一个统一微回路概括。
- **人类联合皮层**：树突、细胞类型和长程连接比入门示意图复杂，不能把鼠的桶状皮层原样当成人类前额叶。

---

### 4. 皮质柱到底是什么

#### 4.1 这个概念为什么出现

皮质柱通常指垂直贯穿多层、具有共同输入或相似反应特征的一组神经元。经典例子包括：

- 猫和灵长类 V1 的眼优势柱、方向选择性柱及超柱组织；
- 啮齿类躯体感觉皮层对应单根胡须的桶状结构；
- 躯体感觉皮层中与相近身体部位有关的垂直组织。

Mountcastle 将柱状组织推广为新皮层的一般原则，产生了深远影响。[5]

#### 4.2 为什么“标准皮质柱”有争议

研究者所说的柱可能分别指几十微米尺度的微柱、几百微米尺度的功能柱、超柱或解剖模块。它们的边界常不清晰，功能属性可重叠，也并非每个脑区都显示同样的周期性柱状图案。[6,7]

较稳妥的结论是：

| 判断 | 证据强度 |
|---|---|
| 皮层有明显的层状组织和大量径向/垂直连接 | 强 |
| 某些感觉皮层有清楚的柱状或斑块状功能地图 | 强 |
| 局部微回路存在可复用的连接主题 | 较强 |
| 所有新皮层由相同尺寸、相同算法的标准柱平铺组成 | 证据不足且有争议 |
| 信号必须先在一根柱内走完六层，再跳到下一根柱 | 不正确 |

#### 4.3 信号怎样离开“柱”

局部锥体细胞和中间神经元可在数百微米至毫米范围内水平连接；II/III、V、VI 层的锥体细胞还可通过白质投向远处。功能活动因此会：

- 在同一局部地图内横向扩散和竞争；
- 跳到同一脑区内较远位置；
- 投向另一个皮层区；
- 经胼胝体到对侧半球；
- 经丘脑或其他皮层下结构形成闭环。

所谓“柱内”和“柱间”并非两个互斥阶段，而是同时发生的局部与长程计算。

---

### 5. 跨脑区传播的总体架构

#### 5.1 三类长程白质连接

1. **联络纤维**：连接同一半球不同皮层区。短 U 形纤维连接相邻脑回，长束连接额、顶、颞、枕叶。
2. **连合纤维**：以胼胝体为主，连接左右半球相关或互补区域。
3. **投射纤维**：连接皮层与丘脑、纹状体、脑干、脊髓等，许多纤维通过内囊。

#### 5.2 前馈与反馈有统计性的层分布

灵长类皮层解剖显示：

- 相对前馈连接更常起源于上层，终止于下一脑区的 IV 层附近；
- 相对反馈连接更常包含深层起源，并避开 IV 层，偏向 I 层和 VI 层；
- 两者不是二元标签，而是随两个区域的层级距离连续变化；
- 同一对区域往往双向连接，且还有平行支路。[8-11]

反馈落到 I 层时，可接触深层锥体细胞长达皮层表面的顶树突，因此“高层情境”可以直接改变较低区神经元如何响应当前输入，而不必等它重新走完六层。

#### 5.3 丘脑参与区间通信

丘脑核团大致可区分为：

- **第一阶核团**：主要接收外周或皮层下驱动输入，例如视觉外侧膝状体、听觉内侧膝状体、躯体感觉腹后核。
- **高阶核团**：大量驱动输入来自皮层 V 层，再投向其他皮层区，例如枕核和部分背内侧丘脑通路。
- **调节性皮层反馈**：皮层 VI 层广泛返回丘脑，改变丘脑增益、时序和状态。

因此，皮层 A 到皮层 B 既可走直接皮层-皮层轴突，也可走 A→丘脑→B 的“跨丘脑”路线。[12-14]

#### 5.4 一个通用但非唯一的任务模板

~~~mermaid
flowchart LR
    S[外界刺激或内部目标] --> R[感受器/内部状态表征]
    R --> BS[脊髓与脑干早期处理]
    BS --> T[丘脑]
    T <--> P[初级感觉皮层]
    P <--> A[高级感觉与联合皮层]
    A <--> C[前额叶-顶叶/语言/记忆网络]
    C <--> BG[基底节-丘脑环路]
    C --> PM[前运动区/SMA/M1]
    PM --> DESC[皮质脊髓与脑干下行系统]
    DESC --> MUS[脊髓回路与肌肉]
    MUS --> R
    A <--> LIM[海马、杏仁核及内侧颞叶]
    PM <--> CB[小脑]
    BS <--> CB
    T <--> C
~~~

图中每个双向箭头实际上代表许多并行纤维和中间站。脊髓反射、脑干定向反应、上丘眼动等可以在完整皮层识别前启动；嗅觉也不遵循“必须先经过丘脑再到初级皮层”的模板。

---

### 6. 视觉：从眼睛到视觉皮层、识别与动作

#### 6.1 视网膜已经在做计算

光线经过角膜、晶状体后落到视网膜：

1. 视杆和视锥细胞进行光电转换。与很多神经元不同，光感受器对光的典型响应是超极化。
2. 双极细胞、水平细胞和无长突细胞形成中心-周边、明暗、颜色、时间变化和运动相关预处理。
3. 视网膜神经节细胞产生动作电位，其轴突组成视神经。

因此，传入大脑的不是逐像素复制的照片，而是已经被分成多种并行特征通道的活动模式。[1,16]

#### 6.2 主要解剖路线

**视网膜→视神经→视交叉→视束→外侧膝状体 LGN→视辐射→V1。**

- 鼻侧视网膜纤维在视交叉交叉，颞侧纤维不交叉，使左视野主要进入右半球、右视野主要进入左半球。
- LGN 保留视网膜拓扑，并维持若干并行通道；它受到来自 V1、脑干和注意网络的大量调节，不是被动中继。
- 灵长类 LGN 的主要驱动输入在 V1 偏向 IV 层，尤其 IV-C；随后影响 II/III、IV-B、V、VI 等局部回路。
- V1 的 II/III 等层向 V2 及其他视觉区前馈；VI 层大量反馈 LGN；高阶视觉区又反馈 V1 的浅层和深层。

#### 6.3 同时存在的皮层下分支

- **上丘**：快速定向、眼跳和头眼协调。
- **顶盖前区**：瞳孔光反射。
- **视交叉上核**：昼夜节律校时。
- **上丘-枕核-皮层通路**：可支持注意和部分无意识视觉功能；V1 损伤后的“盲视”提示视觉并非只有 LGN→V1 一条路。

#### 6.4 V1 之后不是一条直线

视觉皮层由许多相互连接的区域组成，常用的宏观概括是：

- **腹侧流：枕叶→下颞叶。** 偏重物体、面孔、文字、颜色和类别识别，即“是什么”。
- **背侧流：枕叶→顶叶及额叶眼动/运动网络。** 偏重空间、运动、视觉引导动作，即“在哪里/怎样行动”。

两条流不是完全分离的管道，会相互交换信息，也都接受注意、目标和记忆反馈。[17-19]

#### 6.5 看见杯子并伸手拿起的整合过程

1. 视网膜和 LGN/V1 建立位置、边缘、对比、颜色和时间变化的早期表征。
2. 腹侧视觉系统帮助识别“这是杯子”及其类别和意义。
3. 背侧视觉系统与后顶叶估计杯子相对身体、眼睛和手的位置，计算抓取相关形状。
4. 海马/内侧颞叶可提供情境记忆，前额叶维持“我要喝水”的目标。
5. 基底节-丘脑环路参与选择“伸手拿杯”而不是其他动作。
6. 前运动区形成抓取构型，M1 和脑干下行系统驱动脊髓与肌肉。
7. 小脑利用动作副本、视觉和本体感觉预测误差，快速校正轨迹。
8. 手指触觉和本体感觉持续返回 S1、顶叶和小脑，更新抓握力。

这里没有一个时刻是“视觉完全结束、思考才开始”。识别、注意、动作准备和反馈在数十到数百毫秒内重叠进行。

---

### 7. 听觉：从声波到声音、语言和定向

#### 7.1 外周与脑干

**声波→鼓膜/听小骨→耳蜗基底膜→毛细胞→螺旋神经节→耳蜗神经核。**

- 耳蜗按频率进行机械分解，形成音调拓扑。
- 毛细胞把机械位移转换成突触信号，螺旋神经节轴突产生动作电位。
- 从耳蜗神经核开始，信息通过双侧脑干网络进入上橄榄复合体、外侧丘系和下丘。
- 上橄榄等结构较早比较双耳时间差和强度差，是声源定位的重要基础。

由于脑干以上听觉通路高度双侧化，单侧中央通路损伤通常不像单侧耳蜗/听神经损伤那样造成同侧耳完全失聪。

#### 7.2 丘脑与听觉皮层

**下丘→内侧膝状体 MGN→听辐射→初级听觉皮层 A1。**

- MGN 到 A1 的驱动输入偏向 IV 层和邻近层。
- A1 保留音调拓扑，对频率、时间包络、起止和组合特征进行群体编码。
- A1 与听觉带区、旁带区和上颞叶双向连接，深层又返回 MGN 和下丘。

听觉皮层同样存在多条并行流，而不是 A1 完成后才把成品交给语言区。[20,21]

#### 7.3 听到有人叫自己的名字

1. 脑干和 A1 提取频谱、起止、时间结构和声源方向。
2. 上颞叶网络形成语音/声音类别表征。
3. 腹侧听觉-语言网络将声音映射到词和意义；背侧网络更偏向声音-发音动作、序列和空间映射。[22]
4. 与自我相关的记忆和当前情境使“自己的名字”具有高显著性。
5. 顶叶-额叶注意网络转移注意；上丘和额叶眼区可驱动转头或眼跳。
6. 杏仁核、岛叶或自主神经网络会按说话者语气和情境调整警觉。
7. 若要回答，语言计划、前运动区、M1、基底节、小脑和脑干发音运动核共同驱动呼吸、喉和口面肌肉。

---

### 8. 触觉、本体感觉、痛温觉和内感受

#### 8.1 精细触觉与有意识本体感觉

身体机械感受器→背根神经节→同侧脊髓后索→延髓薄束核/楔束核→延髓交叉→内侧丘系→丘脑 VPL→S1。

- 面部感觉主要经三叉神经系统到丘脑 VPM，再到 S1。
- S1 包含 3a、3b、1、2 等区，分别偏重本体、皮肤触觉、纹理、形状及多种整合，但并非绝对分工。
- 信息继续进入 S2、后顶叶、运动区、岛叶等，并有大量下行反馈。
- 身体地图是“躯体拓扑”而不是按真实身体尺寸排列；手、口等精细区域占据较多皮层。

[23,24]

#### 8.2 痛温觉与粗触觉

伤害感受器/温度感受器→背根神经节→脊髓背角→多在入髓后较早交叉→前外侧系统→丘脑及脑干多个靶点→S1/S2、岛叶、扣带、前额叶等。

同时还有到网状结构、臂旁核、杏仁核、下丘脑和导水管周围灰质等路线，分别影响唤醒、情绪、自主反应和下行镇痛。所谓“疼痛矩阵”中的许多区域也会响应非疼痛但显著的事件，因此疼痛不是由一个固定中心或一个专属矩阵简单读出。[25]

#### 8.3 为什么手碰到烫物会先缩回

1. 脊髓背角局部回路可在信号到达大脑前激活屈肌撤退反射，并抑制对侧或拮抗肌群。
2. 上行痛温通路随后支持对位置、强度、厌恶和情境的较完整体验。
3. 杏仁核、海马和前额叶参与威胁学习与“以后避开”的记忆。
4. 运动皮层和脑干系统随后产生更有目的的动作，如放下物体、检查皮肤或呼救。

反射不是“脑没有参与”，而是脊髓先完成一部分时间紧迫的控制，脑随后接管更复杂的评估和行为。

#### 8.4 本体感觉和小脑

肌梭、腱器官和关节/皮肤感受器的信息一部分进入有意识的后索-丘脑-皮层通路，另一部分经脊髓小脑束、楔小脑束等更直接地进入小脑。后者为姿势、时序和在线误差校正提供高速状态信息，不必先形成有意识感觉。

#### 8.5 其他刺激的主要路线

| 模态 | 主要路线概要 | 特点 |
|---|---|---|
| 嗅觉 | 嗅受体神经元→嗅球→梨状皮层、杏仁核、内嗅皮层；随后经多条路影响眶额皮层 | 初级皮层前没有必经的丘脑中继，是常见例外 |
| 味觉 | 面/舌咽/迷走神经→孤束核→丘脑味觉相关区→岛叶与额盖 | 与嗅觉、内脏状态、奖赏和厌恶高度整合 |
| 前庭 | 内耳毛细胞→前庭神经核与小脑→眼动核、脊髓、丘脑和分布式皮层网络 | 同时服务眼反射、平衡、自身运动感和空间定向 |
| 内感受 | 迷走和脊髓内脏传入→孤束核/臂旁核/丘脑→岛叶、扣带、下丘脑 | 表示心肺、胃肠、体温和能量状态，影响情绪与决策 |

---

### 9. “思考一个问题”时信息怎样传播

#### 9.1 思考不是从一个起点沿固定线路前进

“思考”至少可分为维持目标、注意选择、工作记忆、语义检索、情景回忆、心理模拟、价值比较、错误监控和动作选择。不同问题调用不同网络。例如：

- 心算更依赖顶内沟、前额叶和多需求网络；
- 回忆昨天的事件更依赖海马-内侧颞叶与分布式皮层重建；
- 想象一幅图像会自上而下重激活视觉联合皮层；
- 默读和内部语言会调用语言网络与听觉/运动表征；
- 开放式自我思考常更多涉及默认网络，但仍会与控制网络交互。

#### 9.2 前额叶的真实角色

前额叶不是存放全部思想的“CPU”。较可靠的概括是：

- 维持或重建当前任务规则和目标；
- 偏置其他脑区，使相关表征胜出；
- 结合价值、情境和未来后果进行选择；
- 与顶叶、前扣带、岛叶及丘脑构成灵活控制网络。

具体内容可以主要存在于后部感觉和联合皮层。例如记住一个方向时，视觉/顶叶区域仍可携带方向信息；前额叶更多表示规则、优先级和控制状态。[27-30]

#### 9.3 一个问题从读入到回答的可能流程

以“读到一道需要回忆和推理的问题”为例：

1. 视觉系统识别字形、词序和版面，腹侧枕颞皮层形成熟练文字表征。
2. 语言网络把文字映射为句法、语义和任务要求。
3. 多需求额顶网络将目标分解为子问题，并选择当前关注的信息。
4. 海马和内侧颞叶按线索重建相关事件或关系；语义知识则广泛分布在颞叶、顶叶和其他联合皮层。
5. 工作记忆由前额叶、顶叶和内容相关皮层的持续/间歇活动及短时突触状态共同支持。
6. 基底节-丘脑环路帮助门控当前更新什么、保留什么及选择哪个候选答案。
7. 背内侧丘脑、枕核等帮助维持和协调跨区交互。
8. 前扣带和相关网络监控冲突、错误和努力成本。
9. 形成回答后，语言运动网络或手部运动网络把选择转成说话、打字或点击。
10. 感觉反馈再次进入系统，确认结果是否符合目标。

这个顺序只是一种任务分解。真实活动会反复返回先前步骤，多个步骤也会同时进行。

#### 9.4 意识问题仍未解决

再入处理、丘脑-皮层循环、额顶“全局广播”、感觉皮层局部复发处理等理论都得到部分证据，但“某一神经活动为何及何时成为主观体验”没有公认的完整机制。报告可以描述信息可用性、报告和行为控制的神经通路，不能把它们直接等同于已经解释了意识本身。

---

### 10. 海马：从当前经历到记忆重建

#### 10.1 海马不是六层新皮层

海马属于古皮层/海马结构，其主细胞层组织与六层新皮层不同。它通过内嗅皮层、海马旁皮层和广泛联合皮层交换信息。

#### 10.2 常用的海马回路骨架

~~~mermaid
flowchart LR
    NC[分布式新皮层表征] <--> EC[内嗅皮层]
    EC --> DG[齿状回]
    DG --> CA3[CA3]
    CA3 --> CA1[CA1]
    EC --> CA1
    CA1 --> SUB[下托]
    SUB --> EC
    EC --> NC
~~~

- 内嗅皮层→齿状回→CA3→CA1→下托/内嗅皮层常称三突触回路。
- 还存在内嗅皮层直达 CA1/下托、CA3 复发连接及多条旁路。
- 齿状回常被认为有助于区分相似经历；CA3 复发网络常与模式补全联系；CA1 比较和整合多路输入。这些是有支持的功能概括，不是每个细胞的唯一职责。[31,32]

#### 10.3 编码、检索和巩固

- **编码**：海马快速绑定“人物-地点-时间-事件”等分布式皮层信息。
- **检索**：部分线索触发海马活动，再在原有感觉和联合皮层中重建较完整模式。
- **系统巩固**：睡眠和离线重放有助于海马-新皮层重新组织，使部分记忆逐渐更能由皮层网络支持。
- **长期依赖**：远期情景记忆是否以及多大程度仍依赖海马，取决于记忆细节、重建要求和理论框架，不能简单说“记忆最终全部搬出海马”。[33,34]

---

### 11. 情绪和杏仁核：不是单一“恐惧中心”

杏仁核是多个核团的集合：

- 基底外侧复合体接收来自感觉丘脑、感觉/联合皮层、海马和前额叶的多模态输入，参与价值、相关性和联结学习。
- 中央核及相关输出影响下丘脑、脑干、导水管周围灰质和自主神经/防御反应。
- 海马提供场景和时间情境，前额叶参与重评、消退和行动控制。

传统教材常把威胁路线分为“丘脑直达杏仁核的快而粗低路”和“经皮层的慢而精细高路”。现代证据更支持多条并行路线；是否存在足以支持复杂人类恐惧判断的统一“低路”不能一概而论。[35-37]

听到巨响时，脑干惊跳和定向、听觉皮层识别、杏仁核相关性评估、海马情境判断、下丘脑自主反应以及前额叶控制可以并行展开。杏仁核也响应奖励、新奇、社会信息和不确定性，不能仅等同于恐惧。

---

### 12. 从决定到运动：皮层、基底节、小脑、脑干和脊髓

#### 12.1 动作形成是多层闭环

~~~mermaid
flowchart LR
    GOAL[目标与情境：前额叶/顶叶] --> PLAN[前运动区与 SMA]
    GOAL <--> BG[皮层-基底节-丘脑环路]
    PLAN --> M1[M1 及其他下行皮层]
    M1 --> CST[皮质脊髓束]
    M1 --> BST[脑干下行系统]
    CST --> SP[脊髓中间神经元与运动神经元]
    BST --> SP
    SP --> MUS[肌肉]
    MUS --> FB[触觉/本体/视觉反馈]
    FB --> SENS[S1、顶叶、小脑]
    SENS --> PLAN
    PLAN <--> CB[小脑]
    CB --> TH[丘脑/脑干]
    TH --> PLAN
    TH --> M1
~~~

#### 12.2 皮层运动系统

- 后顶叶把视觉、触觉、本体和身体坐标转换为行动相关状态。
- 前运动区更受外界线索和动作目标影响，SMA 更常参与内部序列、双侧协调和动作组织，但二者高度重叠。
- M1 V 层神经元形成皮质脊髓、皮质延髓及其他下行投射；皮质脊髓纤维还来自前运动区、SMA 和部分躯体感觉区。
- 下行轴突经内囊、脑脚、脑桥和延髓锥体，多数在锥体交叉后控制对侧肢体。
- 脑干网状脊髓、前庭脊髓等系统对姿势、平衡、近端肢体和整体协同非常重要。
- 脊髓中间神经元整合下行、感觉反馈和局部反射；α 运动神经元是到骨骼肌的“最终共同通路”。[38,39]

M1 神经元通常不是一根神经元对应一块肌肉或一个简单方向。动作由神经群体的动态轨迹和与脊髓/肌肉系统的共同状态产生。[40]

#### 12.3 基底节：选择、门控和学习

皮层→纹状体→苍白球/黑质→丘脑→皮层形成多条运动、认知和边缘环路。直接、间接和超直接通路有助于解释促进、抑制和快速停止，但“直接通路是油门、间接通路是刹车”过于简单：两类纹状体群体可共同活动，作用取决于具体动作、时间和回路。[41]

多巴胺信号参与奖励预测误差、行动价值和可塑性；基底节也参与习惯、工作记忆更新和认知选择，不只控制肢体运动。

#### 12.4 小脑：预测、时序、校准和学习

小脑皮层只有三层：分子层、浦肯野细胞层和颗粒层。

- 苔藓纤维把来自脑桥、脊髓、前庭等的广泛信息送给颗粒细胞；平行纤维影响浦肯野细胞。
- 攀缘纤维来自下橄榄核，对浦肯野细胞产生强输入，参与误差、事件和学习信号。
- 浦肯野细胞是小脑皮层的主要输出，抑制深部小脑核。
- 深部核再投向丘脑和脑干，影响运动与认知皮层及下行控制。

小脑可比较动作预测与感觉结果，调整时序、增益和内部模型。通过皮层→脑桥→小脑及小脑→丘脑→皮层闭环，它也参与语言、工作记忆、注意和社会认知等非运动任务，但其贡献不是把所有任务都变成同一种简单运算。[42-46]

---

### 13. 人在电脑前工作时，全脑怎样协作

以“阅读屏幕上的代码，找出错误并修改”为例：

| 阶段 | 主要神经过程 | 典型参与结构 |
|---|---|---|
| 注视和扫描 | 选择注视点、眼跳、抑制无关刺激 | 视网膜、V1、上丘、枕核、额叶眼区、顶叶注意网络 |
| 识别字符和布局 | 字形、颜色、缩进、空间结构和物体识别 | V1/V2、腹侧枕颞皮层、背侧视觉-顶叶系统 |
| 语言/符号理解 | 词法、句法、语义和程序符号规则 | 语言网络、颞叶、额下回及任务相关联合区 |
| 保持任务状态 | 记住目标、变量关系、当前假设和下一步 | 多需求额顶网络、内容相关感觉/语义区、丘脑 |
| 检索经验 | 回忆 API、错误模式或之前改动 | 海马-内侧颞叶、分布式语义皮层 |
| 推理和候选比较 | 模拟执行结果、检测冲突、比较代价 | 前额叶、顶叶、前扣带、基底节环路 |
| 打字和鼠标 | 选择动作、手指序列、精细力量与轨迹 | 前运动/SMA、M1、基底节、小脑、脑干、脊髓 |
| 反馈与纠错 | 视觉确认、触觉反馈、错误/奖励更新 | 视觉皮层、S1、顶叶、小脑、前扣带、多巴胺系统 |

几个重要点：

- 熟练阅读和打字会把部分处理变得自动化，减少逐步有意识控制，但不会绕开感觉和运动回路。
- 屏幕上的视觉信息、内部规则和记忆检索会反复互相改变；不是“先看完，再想完，再动手”。
- 长时间工作时，警觉、疲劳、动机和压力通过脑干神经调质、下丘脑和自主系统改变同一任务网络的增益。
- 多任务切换通常需要重新配置目标和工作记忆，存在可测的切换成本；它不是两套复杂思考真正完全并行。

---

### 14. 体育运动时，全脑怎样协作

以“接高速来球并回击”为例：

1. 视网膜、V1 和运动敏感视觉区提取来球方向、速度、旋转线索和背景参照。
2. 背侧视觉流和后顶叶把视觉坐标转换成相对于头、躯干和手臂的行动坐标。
3. 前庭系统、本体感觉、足底触觉和视觉共同估计身体姿势；小脑整合这些信息并预测短期状态。
4. 前额叶按比赛策略、比分和对手习惯设定目标；熟练动作中，逐步意识控制通常减少。
5. 基底节帮助从多个动作方案中选择并启动当前方案。
6. 前运动区/SMA 组织握拍、步法和躯干-上肢序列；M1、脑干和脊髓产生下行驱动。
7. 在感觉反馈尚未完整返回前，前馈预测已经启动动作；随后视觉、本体和触觉误差在线修正。
8. 小脑根据预测误差更新时序和力量，基底节依据结果和奖赏更新选择策略，皮层可塑性稳定技能。
9. 下丘脑、脑干和自主神经系统调节心率、呼吸、体温和能量供给。

体育运动说明了为何脑控制必须同时使用**预测控制和反馈控制**：如果只等感觉结果再反应，长神经传导和肌肉动力学延迟会使高速动作来不及；如果只依靠预先程序，环境变化又无法纠正。[39,42-46]

从初学到熟练，依赖关系会变化：

- 初期更多使用前额叶、海马和显性规则；
- 练习中小脑误差学习、纹状体强化/习惯学习和感觉运动皮层可塑性逐步增强；
- 熟练并不表示“只用小脑或肌肉记忆”，而是控制分布和网络效率改变。

---

### 15. 各主要脑区在信息流中的位置

| 结构 | 主要贡献 | 不是 |
|---|---|---|
| 丘脑 | 感觉驱动、皮层状态、注意、区间协调、皮层-丘脑闭环 | 被动交换机 |
| 枕叶视觉区 | 从局部视觉特征到物体、空间和动作相关表征 | 一台逐像素相机 |
| 颞叶 | 物体/声音/语言语义、人物和长期知识的重要分布区 | 单一“记忆仓库” |
| 顶叶 | 空间、身体状态、感觉整合、数量、注意和行动坐标 | 只有触觉 |
| 前额叶 | 目标、规则、选择、控制、价值与未来行为 | 唯一思考中心或 CPU |
| 海马 | 快速关系/情景学习、空间与事件结构、线索性重建 | 所有长期记忆的永久存储盘 |
| 杏仁核 | 相关性、价值、威胁/奖赏学习及自主行为耦合 | 只负责恐惧 |
| 基底节 | 行动与认知选择、门控、强化学习、习惯 | 简单油门/刹车 |
| 小脑 | 预测、时序、误差校准、运动和部分认知闭环 | 只负责平衡 |
| 岛叶/扣带 | 内感受、显著性、痛觉情感、冲突和自主整合 | 单一“痛觉中心” |
| 下丘脑 | 体温、饥渴、内分泌、自主反应和动机状态 | 纯粹情绪核团 |
| 脑干 | 感觉/运动核、定向、唤醒、自主控制和神经调质 | 只是一根连接线 |
| 脊髓 | 感觉初步处理、反射、节律和运动输出整合 | 被动电缆 |

---

### 16. 为什么同一刺激在不同情境会走出不同结果

解剖线路相对稳定，功能线路却随状态变化。决定实际传播的因素包括：

1. **注意**：额顶网络、枕核和局部抑制/去抑制可提高相关通路增益。
2. **预测与任务**：高级区域的反馈改变早期感觉区对相同输入的响应。
3. **情绪和价值**：杏仁核、眶额皮层、纹状体和神经调质改变优先级。
4. **记忆情境**：海马重建使同一声音或场景获得不同意义。
5. **身体状态**：疲劳、疼痛、饥饿和警觉经下丘脑、岛叶、脑干影响处理。
6. **学习和可塑性**：突触强度、髓鞘、网络策略和感受野会随经验改变。
7. **振荡和瞬时网络状态**：连接两端是否处于合适的兴奋性相位，会影响有效通信。

“预测编码”把前馈活动解释为偏向传递预测误差、反馈活动解释为偏向传递预测或先验，这是有影响力的统一模型，并与部分层间和频率现象相符；但它不是所有皮层连接已经被证明采用的唯一代码。[50,51]

---

### 17. 常见但误导性的说法

#### 17.1 “感觉先传到一个中心，处理完再去下一个中心”

不准确。存在并行支路、早期皮层下行为、双向皮层连接和持续反馈。

#### 17.2 “每个信号都从 IV 层依次走到 II/III、V、VI 层”

这是经典微回路简图，不是必经顺序。直达、跨层、同层和回返连接都很常见。

#### 17.3 “每根皮质柱执行同一个标准算法”

存在重复主题，但通用标准柱的边界、尺寸和统一算法没有定论。

#### 17.4 “前额叶产生思想，后部脑区只是输入设备”

思想内容和计算广泛分布；前额叶是控制与选择的重要节点，不是全部内容所在地。

#### 17.5 “海马存储记忆，杏仁核产生恐惧，小脑负责平衡”

这三个说法都把网络功能压缩成单标签。三者均参与多种行为，并通过闭环与皮层协作。

#### 17.6 “看到某区在 fMRI 亮起，就说明信号先后走到那里”

血氧信号是间接、缓慢的群体代谢指标。确定方向和因果需要结合解剖示踪、电生理、刺激、病损和具有时间分辨率的方法。

#### 17.7 “左脑逻辑、右脑创造”

两半球确有统计性偏侧化，例如多数人的语言网络偏左，但复杂任务通常需要双侧和跨胼胝体网络，不能按人格二分。

---

### 18. 目前较确定、较可能和仍不确定的内容

#### 较确定

- 动作电位、化学突触、兴奋/抑制和髓鞘轴突是快速神经通信的物质基础。
- 新皮层一般具有六层及明显的层特异连接倾向。
- 感觉、运动、丘脑、基底节、小脑、海马和杏仁核形成并行、双向和闭环网络。
- 视觉、听觉、躯体感觉等有明确的外周-脑干/丘脑-皮层主干通路。
- 皮层之间存在统计性的前馈/反馈层分布。

#### 较可能但不能过度统一

- 某些局部连接主题可作为“典型皮层微回路”复用。
- 振荡同步、通信子空间和增益控制是选择性脑区通信的重要机制。
- 小脑在不同任务中可能重复使用某些预测/校准计算。
- 海马通过索引和重放帮助分布式皮层记忆形成与检索。

#### 仍有重要争议或空白

- 是否存在适用于所有新皮层的统一皮质柱和统一算法。
- 不同脑区、物种和发育阶段是否共享同一“典型微回路”。
- 工作记忆中持续放电、短时突触状态和间歇活动各占多大作用。
- 预测编码是否是皮层的普遍计算原则。
- 振荡同步究竟是通信原因、结果还是两者兼有。
- 主观意识如何从这些活动中产生。
- 人类自然行为中，毫米和毫秒尺度的全脑因果信息流如何完整重建。

---

### 19. 最简洁的统一模型

对一个外界刺激，可以用下面的循环理解：

**刺激转导 → 外周/脊髓/脑干并行预处理 → 丘脑及皮层下分支 → 初级感觉皮层的层间复发处理 → 高级感觉与联合区 → 记忆、情绪、目标和注意网络反复反馈 → 基底节/小脑/丘脑参与选择与预测 → 运动皮层和脑干/脊髓输出 → 新的感觉反馈。**

对一个没有明显外界输入的思想，可以用下面的循环理解：

**当前脑状态和目标 → 前额叶-顶叶控制配置 → 海马/语义网络/感觉联合皮层重建内容 → 多个候选状态竞争与评估 → 更新工作记忆或形成动作 → 结果反馈并继续循环。**

两者的共同点是：**局部层间回路负责变换和整合，长程轴突负责跨区通信，丘脑和皮层下环路负责协调、选择、预测与状态控制；全程是并行且递归的。**

---

### 20. 参考文献与延伸阅读

以下优先列综述、经典解剖研究和开放教材；序号与正文引用对应。

1. Purves D, et al. **Neuroscience, 2nd edition.** Sinauer, 2001. [NCBI Bookshelf](https://www.ncbi.nlm.nih.gov/books/NBK10799/)
2. Douglas RJ, Martin KAC. **Neuronal Circuits of the Neocortex.** Annual Review of Neuroscience, 2004. [DOI](https://doi.org/10.1146/annurev.neuro.27.070203.144152)
3. Harris KD, Shepherd GMG. **The Neocortical Circuit: Themes and Variations.** Nature Neuroscience, 2015. [DOI](https://doi.org/10.1038/nn.3917)
4. Rockland KS. **What Do We Know About Laminar Connectivity?** NeuroImage, 2019. [DOI](https://doi.org/10.1016/j.neuroimage.2017.07.032)
5. Mountcastle VB. **The Columnar Organization of the Neocortex.** Brain, 1997. [DOI](https://doi.org/10.1093/brain/120.4.701)
6. Horton JC, Adams DL. **The Cortical Column: A Structure Without a Function.** Philosophical Transactions B, 2005. [DOI](https://doi.org/10.1098/rstb.2005.1623)
7. da Costa NM, Martin KAC. **Whose Cortical Column Would That Be?** Frontiers in Neuroanatomy, 2010. [DOI](https://doi.org/10.3389/fnana.2010.00016)
8. Felleman DJ, Van Essen DC. **Distributed Hierarchical Processing in the Primate Cerebral Cortex.** Cerebral Cortex, 1991. [DOI](https://doi.org/10.1093/cercor/1.1.1-a)
9. Markov NT, et al. **A Weighted and Directed Interareal Connectivity Matrix for Macaque Cerebral Cortex.** Cerebral Cortex, 2014. [DOI](https://doi.org/10.1093/cercor/bhs270)
10. Markov NT, et al. **Anatomy of Hierarchy: Feedforward and Feedback Pathways in Macaque Visual Cortex.** Journal of Comparative Neurology, 2014. [DOI](https://doi.org/10.1002/cne.23458)
11. Vezoli J, et al. **Cortical Hierarchy, Dual Counterstream Architecture and the Importance of Top-Down Generative Networks.** NeuroImage, 2021. [DOI](https://doi.org/10.1016/j.neuroimage.2020.117479)
12. Sherman SM. **Thalamus Plays a Central Role in Ongoing Cortical Functioning.** Nature Neuroscience, 2016. [DOI](https://doi.org/10.1038/nn.4269)
13. Halassa MM, Kastner S. **Thalamic Functions in Distributed Cognitive Control.** Nature Neuroscience, 2017. [DOI](https://doi.org/10.1038/s41593-017-0020-1)
14. Theyel BB, Llano DA, Sherman SM. **The Corticothalamocortical Circuit Drives Higher-Order Cortex in the Mouse.** Nature Neuroscience, 2010. [DOI](https://doi.org/10.1038/nn.2449)
15. Tremblay R, Lee S, Rudy B. **GABAergic Interneurons in the Neocortex: From Cellular Properties to Circuits.** Neuron, 2016. [DOI](https://doi.org/10.1016/j.neuron.2016.06.033)
16. Nassi JJ, Callaway EM. **Parallel Processing Strategies of the Primate Visual System.** Nature Reviews Neuroscience, 2009. [DOI](https://doi.org/10.1038/nrn2619)
17. Goodale MA, Milner AD. **Separate Visual Pathways for Perception and Action.** Trends in Neurosciences, 1992. [DOI](https://doi.org/10.1016/0166-2236%2892%2990344-8)
18. Kravitz DJ, et al. **A New Neural Framework for Visuospatial Processing.** Nature Reviews Neuroscience, 2011. [DOI](https://doi.org/10.1038/nrn3008)
19. Grill-Spector K, Weiner KS. **The Functional Architecture of the Ventral Temporal Cortex and Its Role in Categorization.** Nature Reviews Neuroscience, 2014. [DOI](https://doi.org/10.1038/nrn3747)
20. Hackett TA. **Information Flow in the Auditory Cortical Network.** Hearing Research, 2011. [DOI](https://doi.org/10.1016/j.heares.2010.01.011)
21. Rauschecker JP, Scott SK. **Maps and Streams in the Auditory Cortex.** Nature Neuroscience, 2009. [DOI](https://doi.org/10.1038/nn.2331)
22. Hickok G, Poeppel D. **The Cortical Organization of Speech Processing.** Nature Reviews Neuroscience, 2007. [DOI](https://doi.org/10.1038/nrn2113)
23. Abraira VE, Ginty DD. **The Sensory Neurons of Touch.** Neuron, 2013. [DOI](https://doi.org/10.1016/j.neuron.2013.07.051)
24. Delhaye BP, Long KH, Bensmaia SJ. **Neural Basis of Touch and Proprioception in Primate Cortex.** Comprehensive Physiology, 2018. [DOI](https://doi.org/10.1002/cphy.c170033)
25. Iannetti GD, Mouraux A. **The Pain Matrix Reloaded: A Salience Detection System for the Body.** Progress in Neurobiology, 2011. [DOI](https://doi.org/10.1016/j.pneurobio.2010.10.005)
26. Corbetta M, Shulman GL. **Control of Goal-Directed and Stimulus-Driven Attention in the Brain.** Nature Reviews Neuroscience, 2002. [DOI](https://doi.org/10.1038/nrn755)
27. Miller EK, Cohen JD. **An Integrative Theory of Prefrontal Cortex Function.** Annual Review of Neuroscience, 2001. [DOI](https://doi.org/10.1146/annurev.neuro.24.1.167)
28. Duncan J. **The Multiple-Demand System of the Primate Brain.** Trends in Cognitive Sciences, 2010. [DOI](https://doi.org/10.1016/j.tics.2010.01.004)
29. Christophel TB, et al. **The Distributed Nature of Working Memory.** Trends in Cognitive Sciences, 2017. [DOI](https://doi.org/10.1016/j.tics.2016.12.007)
30. Petersen SE, Sporns O. **Brain Networks and Cognitive Architectures.** Neuron, 2015. [DOI](https://doi.org/10.1016/j.neuron.2015.09.027)
31. Lisman J, et al. **Viewpoints: How the Hippocampus Contributes to Memory, Navigation and Cognition.** Nature Neuroscience, 2017. [DOI](https://doi.org/10.1038/nn.4661)
32. Amaral DG, Witter MP. **The Three-Dimensional Organization of the Hippocampal Formation.** Neuroscience, 1989. [DOI](https://doi.org/10.1016/0306-4522%2889%2990424-7)
33. Squire LR, et al. **Memory Consolidation.** Cold Spring Harbor Perspectives in Biology, 2015. [DOI](https://doi.org/10.1101/cshperspect.a021766)
34. McClelland JL, McNaughton BL, O'Reilly RC. **Why There Are Complementary Learning Systems in the Hippocampus and Neocortex.** Psychological Review, 1995. [DOI](https://doi.org/10.1037/0033-295X.102.3.419)
35. Janak PH, Tye KM. **From Circuits to Behaviour in the Amygdala.** Nature, 2015. [DOI](https://doi.org/10.1038/nature14188)
36. Pessoa L, Adolphs R. **Emotion Processing and the Amygdala: From a Low Road to Many Roads.** Nature Reviews Neuroscience, 2010. [DOI](https://doi.org/10.1038/nrn2920)
37. Phelps EA, LeDoux JE. **Contributions of the Amygdala to Emotion Processing.** Neuron, 2005. [DOI](https://doi.org/10.1016/j.neuron.2005.09.025)
38. Lemon RN. **Descending Pathways in Motor Control.** Annual Review of Neuroscience, 2008. [DOI](https://doi.org/10.1146/annurev.neuro.31.060407.125547)
39. Svoboda K, Li N. **Neural Mechanisms of Movement Planning: Motor Cortex and Beyond.** Current Opinion in Neurobiology, 2018. [DOI](https://doi.org/10.1016/j.conb.2017.10.023)
40. Churchland MM, et al. **Neural Population Dynamics During Reaching.** Nature, 2012. [DOI](https://doi.org/10.1038/nature11129)
41. Nelson AB, Kreitzer AC. **Reassessing Models of Basal Ganglia Function and Dysfunction.** Annual Review of Neuroscience, 2014. [DOI](https://doi.org/10.1146/annurev-neuro-071013-013916)
42. Shadmehr R, Krakauer JW. **A Computational Neuroanatomy for Motor Control.** Experimental Brain Research, 2008. [DOI](https://doi.org/10.1007/s00221-008-1280-5)
43. Apps R, Garwicz M. **Anatomical and Physiological Foundations of Cerebellar Information Processing.** Nature Reviews Neuroscience, 2005. [DOI](https://doi.org/10.1038/nrn1646)
44. Strick PL, Dum RP, Fiez JA. **Cerebellum and Nonmotor Function.** Annual Review of Neuroscience, 2009. [DOI](https://doi.org/10.1146/annurev.neuro.31.060407.125606)
45. Diedrichsen J, et al. **Universal Transform or Multiple Functionality? Understanding the Human Cerebellum Across Task Domains.** Neuron, 2019. [DOI](https://doi.org/10.1016/j.neuron.2019.04.021)
46. Wagner MJ, Luo L. **Neocortex-Cerebellum Circuits for Cognitive Processing.** Trends in Neurosciences, 2020. [DOI](https://doi.org/10.1016/j.tins.2019.11.002)
47. Shine JM. **Neuromodulatory Influences on Integration and Segregation in the Brain.** Trends in Cognitive Sciences, 2019. [DOI](https://doi.org/10.1016/j.tics.2019.04.002)
48. Semedo JD, et al. **Cortical Areas Interact Through a Communication Subspace.** Neuron, 2019. [DOI](https://doi.org/10.1016/j.neuron.2019.01.026)
49. Fries P. **Rhythms for Cognition: Communication Through Coherence.** Neuron, 2015. [DOI](https://doi.org/10.1016/j.neuron.2015.09.034)
50. Bastos AM, et al. **Canonical Microcircuits for Predictive Coding.** Neuron, 2012. [DOI](https://doi.org/10.1016/j.neuron.2012.10.038)
51. Keller GB, Mrsic-Flogel TD. **Predictive Processing: A Canonical Cortical Computation.** Neuron, 2018. [DOI](https://doi.org/10.1016/j.neuron.2018.10.003)

---

### 21. 阅读这份报告时最重要的一句话

**脑信号不是沿一串皮质柱或六层皮层单向传递，而是在层间局部微回路、跨区白质连接、丘脑-皮层回路和多个皮层下闭环中并行、递归、按任务状态动态路由；感觉、思考、记忆、情绪和运动是这些网络在不同时间尺度上的共同结果。**
