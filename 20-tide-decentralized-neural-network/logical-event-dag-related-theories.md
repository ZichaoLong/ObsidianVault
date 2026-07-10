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

`Logical Event DAG Theorem` is not meant to be a mathematically novel theorem. Its core is a specialization of several mature ideas:

- deterministic evaluation of a DAG is independent of the chosen topological order;
- logical time matters more than physical arrival time;
- deterministic dataflow systems can be scheduled asynchronously when their semantic dependencies are preserved;
- high-performance prefill requires additional kernel algebra, such as batched maps, masked matmul, or associative scan.

The value in Tide is the specialization:

```text
autoregressive model / graph neural runtime
+ external token tick
+ internal round tick
+ phase
+ node / edge event
+ chunk prefill correctness
```

The theorem separates two questions:

- Correctness: does chunk execution compute the same logical event graph as decode fold?
- Performance: do the kernels in that graph admit known high-throughput implementations?

## Theory Map

| Theory | Core idea | Relation to Tide | Boundary |
| --- | --- | --- | --- |
| DAG topological evaluation | A deterministic DAG can be evaluated in any topological order with the same result. | This is the proof core of `C_L = Fold_T^L` when chunk execution preserves the same logical event DAG. | It proves correctness only, not high performance. |
| Lamport logical time | Logical ordering of events is more fundamental than wall-clock arrival order. | `token_id / round_id / phase_id / node_id` are logical event metadata; physical arrival order can differ. | Logical clocks do not by themselves define model kernels or state semantics. |
| Kahn process networks | Deterministic processes communicate over channels; results can be independent of scheduling. | Supports the intuition that asynchronous graph execution can be deterministic if communication semantics are disciplined. | KPN assumes specific blocking stream semantics; LH/Tide message aggregation may not satisfy them. |
| Synchronous dataflow | A static graph can be scheduled predictably when production/consumption rates are known. | Useful for fixed internal rounds, phases, and graph schedules. | Tide may have selectors, sparse activation, or data-dependent routing beyond static SDF. |
| Timely dataflow / Naiad | Messages carry logical timestamps; operators reason over partially ordered logical time. | Very close to tagged messages and `(token, round, phase, node)` event IDs. | It is a distributed dataflow execution model, not an autoregressive-model proof by itself. |
| Parallel prefix / scan | Sequential recurrences can be parallelized when updates compose associatively. | This is the high-performance proof path for Mamba / SSM / linear attention accumulators. | It applies only to recurrences with suitable algebraic structure. |
| Database provenance | Query results can carry provenance explaining which inputs contributed. | Closest analogy for why untagged aggregation can destroy token / round influence relation. | Provenance frameworks are usually for databases, not neural runtime kernels. |
| CALM / confluence | Order-independent distributed results require monotonic or coordination-safe structure. | Supports the distinction between safe aggregation and arrival-order-dependent kernels. | CALM is about distributed consistency, not chunk prefill directly. |
| Differential Dataflow | Collections carry timestamps and differences; incremental operators preserve logical time. | Strong analogy for timestamped collections and trace/arrangement maintenance. | It assumes dataflow collection semantics, not arbitrary neural state mutation. |

## 1. DAG Evaluation And Topological Order

The minimal mathematical fact is simple: if every value in a deterministic DAG is a function of its predecessors, then any topological order computes the same node values.

For Tide, decode fold gives one legal order:

```text
for token t:
  for logical event e in token-local order:
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

## 2. Lamport Logical Time

Lamport's key point is that distributed systems need an event ordering relation that is not merely physical clock time. If event `a` can causally affect event `b`, then `a` must be logically before `b`.

This maps directly to Tide:

```text
physical arrival order != logical dependency order
```

A late-token signal may physically arrive before an early-token signal, but it must carry enough metadata:

```text
(token_id, internal_round_id, phase_id, source_node_id)
```

Then the receiving node can bucket, sort, mask, or buffer messages according to logical time.

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

- fixed external token ticks;
- fixed internal round count;
- fixed phase order;
- fixed graph topology;
- fixed mailbox lifecycle.

This resembles the cleanest version of B0/B2:

```text
for external token:
  for internal round:
    for phase:
      compute fixed graph operations
```

The limitation is that Tide/LH may introduce selectors, sparse activation, and data-dependent routing. Once routing changes dynamically, SDF is no longer enough; logical event DAG semantics still apply, but static scheduling may not.

Relevant source:

- Edward A. Lee and David G. Messerschmitt, "Synchronous Data Flow", Proceedings of the IEEE, 1987. DOI: https://doi.org/10.1109/PROC.1987.13876

## 5. Timely Dataflow / Naiad

Naiad is especially relevant because messages carry logical timestamps, and computation proceeds over a partially ordered logical time domain.

This is close to what Tide needs for LH-like chunk prefill:

```text
message = value + logical timestamp
logical timestamp = (token, round, phase, node/edge)
```

With such metadata, physical delivery can be out of order while logical visibility is preserved.

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

- message collections should preserve token / round / phase timestamps;
- arrangements / indexes can be derived views, not semantic replacements;
- aggregation is safe only when it is a semantics-preserving quotient;
- physical compaction must preserve the queries future kernels need.

Relevant source:

- Frank McSherry et al., "Differential Dataflow", CIDR 2013. PDF: https://www.cidrdb.org/cidr2013/Papers/CIDR13_Paper111.pdf

## Implications For Tide

The current theoretical stack should be read as:

1. `Logical Event DAG Theorem` gives a correctness gate.
2. Transformer / Mamba prove they satisfy the gate for standard kernels.
3. Their high performance comes from known kernel structures: matmul, causal masked attention, fused attention, prefix scan.
4. General graph support requires preserving logical event provenance.
5. Existing LH cannot be assumed chunk-prefill-correct if it performs irreversible aggregation that loses token / round / phase provenance.

The design pressure for Tide is therefore:

```text
general graph execution
+ logical event metadata
+ deterministic visibility / commit order
+ tagged or provably safe aggregation
+ kernel-family-specific high-performance implementations
```

## Boundary Statement

The theorem does not say:

```text
any graph runtime has efficient prefill
```

It says:

```text
if the chunk runtime computes the same logical event DAG as decode fold,
then correctness holds.
```

Efficiency is a second proof obligation. It must be supplied by the actual kernel family.
