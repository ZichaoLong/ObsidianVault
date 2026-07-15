---
type: note
status: active
tags:
  - tide
  - prefill-decode
  - logical-event-dag
  - related-work
---

# Logical Event DAG Related Theories

## Position

> [!summary] 本页定位
> 本页是 [[step-transition-mathematical-specification]] 的外部理论与工程谱系参考。读者不需要预先掌握 CPU ISA、编译器、SSA 或分布式数据流；每节只提炼对 Tide 有用的最小概念、适用边界与原始参考。类比本身不构成 Tide 定理的证明。dynamic event DAG 与 zero-delay 的 Tide-specific 推演见 [[finite-event-dag-and-zero-delay-loops-memo]]。

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

## Theory Map

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

## 0. Architecture And Compiler Semantics Lineage

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

### 0.1 ISA Contract And Out-Of-Order Execution

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

### 0.2 Compiler Optimization As Semantics-Preserving Translation

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

### 0.3 IR, SSA, And Explicit Def-Use Structure

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

### 0.4 Abstract Interpretation And Semantic Quotients

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

### 0.5 Translation Validation And Alive2

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

### 0.6 Verified Compiler As A Long-Term Upper Bar

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

### 0.7 Memory Models, Alias Analysis, And Floating-Point Boundaries

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

### 0.8 Practical Lessons For Tide

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

## 1. DAG Evaluation And Topological Order

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

## Static Cycles, Dynamic Unrolling, And Zero-Delay SCCs

### Static loop is not an instantaneous algebraic loop

A compiler CFG may contain a back edge, and a scheduling representation for a loop may contain recurrence edges. These edges normally carry an iteration distance: an operation in iteration $i+1$ depends on a value from iteration $i$. Adding the dynamic iteration index turns the finite execution into an acyclic event relation.

This is also how Tide should interpret ordinary recurrence:

```text
static graph cycle
+ token / round / iteration delay
-> finite dynamic logical event DAG
```

The same idea appears in modulo scheduling. The static loop dependence graph may be cyclic, but recurrence distance constrains the legal initiation interval; it does not mean that two operations in the same dynamic instant recursively require each other's result.

### Zero-delay algebraic loop

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

### SCC condensation

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

## 2. Lamport Logical Time

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

## 3. Kahn Process Networks And Deterministic Dataflow

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

## 4. Synchronous Dataflow

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

## 5. Timely Dataflow / Naiad

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

## 6. Parallel Prefix / Scan

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

## 7. Provenance And Safe Aggregation

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

## 8. CALM, Confluence, And Coordination

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

## 9. Differential Dataflow

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

## Implications For Tide

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

## Boundary Statement

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
