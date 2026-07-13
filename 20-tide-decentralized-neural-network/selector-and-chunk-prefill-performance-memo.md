---
type: memo
status: draft
tags:
  - tide
  - prefill-decode
  - selector
  - dynamic-routing
  - sequence-parallel
---

# Selector And Chunk Prefill Performance Memo

## Position

本文记录 selector 对 Tide chunk prefill correctness 与高性能 sequence parallelism 的不同影响。它是研究备忘，不是当前数学规范或已经实现的优化方案。

其中“任意自适应 routing 为什么不存在通用 exact、work-efficient、次线性 adaptive-depth prefill”的正式定义与证明，已经独立写入 [[adaptive-routing-prefill-impossibility]]；本页继续保留架构分层、capability contraction 与候选推进路线。

基于每条 edge 延迟为 1 的进一步正向候选，包括一般空间 DAG、owner/frontier-labelled signal、显式 node context、三种同刻/融合语义和 prefill-compatible selector，见 [[token-owned-general-dag-routing]]。

核心判断是：

> aggregation 是 provenance correctness 的主要风险；stateful selector 是高性能 sequence-parallel 的主要风险。selector 本身不破坏有限 logical event DAG 的存在，但可能使该 DAG 的 critical path 接近逐 token / round 串行链。

## 1. DAG Correctness 与 DAG Performance

对有限 chunk，若 reference execution 能展开为 dependency-complete logical event DAG，且 chunk implementation 保持：

- 相同的 local event equations。
- 相同的 boundary inputs。
- 相同的 state visibility 与 commit order。
- 相同的 output / final-state extraction。

则 DAG topological evaluation 给出 chunk correctness 的充分条件。

但 DAG 存在不意味着高性能。一个 DAG 可以几乎退化为 chain：

$$
e_0\to e_1\to\cdots\to e_K
$$

此时 correctness 清楚，但 span 仍为 $\Theta(K)$。

## 2. 当前 LH / Tide Selector 的状态语义

把第 $j$ 次 selector 调用写成：

$$
(A_j,Q_{j+1})=\sigma(C_j,Q_j)
$$

其中：

- $C_j$ 是本次调用的 candidate activations。
- $Q_j$ 是 selector persistent state。
- $A_j$ 是被保留的 active set。
- $Q_{j+1}$ 是更新后的 selector state。

当前 LH / Tide 的 $Q_j$ 至少包含：

```text
affectcount[base, sample, local_point]
selectcount[base, sample, local_point]
```

选择优先级是：

1. `selectcount` 较少者优先。
2. `affectcount` 较多者优先。
3. candidate signal norm 较高者优先。
4. column / local index 较小者优先。

因此，它不是 stateless current-step top-k。第 $j$ 次选择需要精确的 $Q_j$，而 $Q_j$ 依赖此前所有 selector calls。

当前代码位置：

- LH selector：`~/llm/lh/Connectome/cpp/src/Selector.cpp`。
- Tide selector state：`~/llm/tide/include/tide/role_aware_lh.h`。
- Tide selector implementation：`~/llm/tide/src/role_aware_lh.cpp`。

## 3. 三层耦合

selector 的困难不只来自 `selectcount / affectcount`。

### 3.1 Stateful selector

selector state 形成显式顺序链：

$$
Q_0\to Q_1\to\cdots\to Q_K
$$

若没有可紧凑表示的 associative composition，多个 token / round 的精确选择不能直接通过普通 scan 并行得到。

### 3.2 Active-set-dependent future computation

被选中的 $A_j$ 会成为后续 graph propagation 的 source activations，因此下一批 candidates 依赖本次选择：

$$
C_{j+1}=F_j(A_j,H_j,X_j)
$$

这意味着 candidates 不是预先给定的外部序列。它们本身由此前 routing 和 node state 动态生成。

组合后得到：

$$
(A_j,Q_{j+1})=\sigma(C_j,Q_j)
$$

$$
C_{j+1}=F_j(A_j,H_j,X_j)
$$

因此，既不能先独立算完所有 $C_j$ 再统一 select，也不能只对已知 selector transition 做简单 prefix composition。

### 3.3 Conditional memory side effects

当前 LH-like runtime 中最直接的 selector-conditioned memory side effect 是：

```text
if clear_after_activation:
    clear hidden / local KV memory for selected samples
```

也就是说，同一个 node/sample 的 memory 是否清空取决于 selector mask。

还有一层间接影响：active set 决定后续哪些节点被影响，进而决定未来哪些 node-local memories 会执行 append、decay、update 或 read。

这类机制不是 Tide 总目标的必要组成。可以考虑：

- 固定 decay，不做 selector-conditioned clear。
- 使用 affine / scan-friendly state update。
- 使用 Mamba / SSM 风格 recurrent state。
- 使用 linear-attention accumulator。
- 把 reset mask 作为显式 segmented-scan boundary，但仍需先得到 selector mask。

因此，conditional clear 可以简化或替代；真正更核心的是 selector state 与 active-set-dependent future computation 的闭环。

## 4. Pack 不等于 Sequence Parallel

把多个 tick 的 selector inputs pack 进一个 kernel，可以：

- 减少 kernel launch。
- 并行处理 batch samples。
- 并行处理不同 base groups。
- 改善 gather / scatter 与内存布局。

但如果 kernel 内仍按 logical tick 顺序更新 $Q_j$，它只是在做 fused sequential evaluation：

```text
pack many selector calls
-> one kernel
-> sequential state updates inside kernel
```

这可能带来实际加速，但不会消除 sequence critical path。真正的 parallel-prefill witness 仍需要：

- compact associative transition summary；或
- 可并行求解的 routing formulation；或
- speculation + validation + replay；或
- 修改 reference selector semantics。

## 5. 其他 LH / Tide 机制的相对风险

| 机制 | Correctness 风险 | 高性能风险 |
| --- | --- | --- |
| 同一 logical event 内聚合 | 低；reference 本来执行相同聚合即可 | 通常可 pack / fuse |
| 跨 token / round 聚合 | 高；必须保留 provenance 或证明 quotient | ragged packing 与 mask |
| Bridge / fixed phase | read/write/commit 显式后较低 | barrier 与跨 phase scheduling |
| Local causal attention / KV append | 已有标准 chunk correctness 路线 | variable-length packed attention |
| Add / affine decay hidden | 通常可表示为 recurrence | associative 时可 scan |
| Selector-conditioned clear | correctness 可定义 | 依赖 selector mask，形成 reset scan |
| Token-local readout cache | 生命周期显式后较低 | internal tick packing |
| Pronounce memory | 取决于具体 recurrent kernel | 可能需要 causal attention / scan |
| Dynamic active graph | 可在线生成 finite event DAG | 稀疏 compaction、负载均衡与调度 |
| Stateful selector | 可顺序复现 | 主要 sequence critical-path 候选 |

## 6. 一个两 Token、两路径例子

考虑节点：

```text
input -> router
router -> left -> output
router -> right -> output
```

selector 每次只允许 `left/right` 中一个节点激活，并维护历史计数 $Q$。

对 token A：

1. A 到达 `router`。
2. 根据 A 的 candidate scores 与旧 $Q_A$，selector 选择 `left`。
3. 更新 selector state 得到 $Q_A'$。
4. A 经 `left` 更新相应 node memory，并传播到 output。

对 token B：

1. B 到达 `router` 时，选择依赖 $Q_A'$。
2. 如果 A 选择过 `left`，公平性计数可能让 B 更倾向 `right`。
3. B 在 `left/right` 上的后续 candidates 还依赖 A 是否激活、清空或更新过对应 node memory。

因此，在保持当前 exact semantics 时，B 的完整路径通常不能在 A 的 selector decision 与相关 state commits 之前确定。

但“B 完全不知道什么时候会被影响”需要更精确地说：

- runtime 知道合法的 logical rank、phase 与最大 round 结构。
- B 不一定知道自己会经过哪些 dynamic nodes，也不知道会读取哪个 path-specific state version。
- 若 A 尚未完成所有可能影响 B routing/state 的 commits，B 可以做与这些 commits 独立的前置计算，但不能安全提交依赖它们的 route-specific events。

这与 out-of-order CPU 类似：可以提前执行独立工作，也可以推测执行，但最终必须验证 dependency 和 commit order。

## 7. 可选推进路线

### Selector ablation ladder

1. `all-active`：先建立无 selector 的 graph chunk prefill 基线。
2. `stateless top-k`：只按当前 candidate score 选择。
3. `token-local selector`：每个 external token 重置 selector history。
4. `persistent LH selector`：保留跨 token / round 的 `affectcount / selectcount`。

这个梯度可区分：

- 稀疏动态路径本身的成本。
- persistent fairness history 的额外串行成本。
- conditional state reset 的额外成本。

### Long-term alternatives

- 保留当前语义，做 packed sequential selector，接受其 critical path。
- 设计 scan-friendly / token-local controller state。
- 预先生成或近似预测 route，再做 exact validation。
- 使用 speculation + replay。
- 定义新的 chunk-level balanced routing contract，而不再要求完整 LH selector parity。

## 8. 对研究价值的初步判断

DAG topological evaluation、SSA-style explicit dependency、simulation 与 quotient 本身大多来自成熟理论。若只证明“同一个 deterministic DAG 的任意 topological order结果相同”，理论新颖性有限。

但它仍有三种直接价值：

1. **规范价值**：为 Tide 划清 correctness 边界，避免 dynamic graph、pack、fusion 与 selector 混在一起。
2. **系统价值**：把有限 token、internal round、phase、state version、dynamic routing 与 sparse kernel lowering 放进同一个可验证 IR。
3. **研究定位价值**：把真正困难的问题暴露为 critical-path reduction，而不是继续争论泛化的 `prefill = decode` 是否成立。

潜在创新点因此从“DAG evaluation theorem”转移到：

- dynamic sparse event DAG 的可验证生成。
- stateful routing 的高性能等价实现或可接受替代语义。
- selector speculation / validation / replay。
- 保持局部通信与超稀疏的同时降低 sequence span。
- correctness certificate 与实际 work/span/memory/communication witness 的结合。

更准确的主张应是：

> DAG 不是 Tide 最可能的新数学发现，而是把 correctness 固定下来、使高性能瓶颈可见和可裁决的核心规范形。

## 9. Tide 的进一步设计目标

前面的讨论可以收敛为一个比“让一般 Graph 支持 prefill”更严格的目标：

> 给定有限 chunk，先生成语义完整的 reference event DAG；再把其中满足特定代数或依赖性质的区域，替换为经过等价性证明的并行 chunk operator，使最终 execution DAG 同时保持局部通信、超稀疏、correctness 和较低 span。

这里不要求整个 Graph 都能 scan。不同 node 或 subgraph 可以依靠不同理由获得并行性；无法并行化的区域仍可顺序执行，但必须显式暴露其 span 成本。

### 9.1 Reference event DAG

给定长度为 $L$ 的输入 chunk：

$$
X_{0:L}=(x_0,x_1,\ldots,x_{L-1}),
$$

reference decode semantics 写成：

$$
(y_t,S_{t+1})=\operatorname{Step}(x_t,S_t),
\qquad 0\leq t<L.
$$

把这段有限执行展开为 reference event DAG：

$$
\mathcal D_{\mathrm{ref}}(L)
=
(E_{\mathrm{ref}},\prec_{\mathrm{ref}}).
$$

其中，一个 logical event 可以带有坐标：

$$
e=(t,r,p,v,\nu),
$$

这里：

- $t$ 是 external token index。
- $r$ 是 internal round index。
- $p$ 是 phase。
- $v$ 是 graph node 或 subgraph role。
- $\nu$ 是被读取或写入的 state version。
- $\prec_{\mathrm{ref}}$ 包含 data、state、control、visibility 与 commit dependencies。

Graph schema 本身可以有环，只要对任意有限 $L$ 和有限 internal rounds，实际执行可以展开成有限、dependency-complete 的 event DAG。所有 feedback edge 必须推进 token、round、phase 或其他明确的 logical rank；未定义的 zero-delay algebraic loop 不进入这一执行模型。

### 9.2 Certified contraction 与 execution DAG

把 reference DAG 划分为若干互不重叠的 event regions：

$$
\mathcal R=\{R_1,R_2,\ldots,R_m\}.
$$

对任意 region $R_i$，定义它的 boundary inputs、boundary outputs、entry state 和 exit state。若存在 chunk implementation $K_i$，对所有合法边界输入都满足：

$$
\operatorname{Transfer}_{K_i}
=
\operatorname{Transfer}_{R_i},
$$

则 $K_i$ 可以作为 $R_i$ 的等价 lowering。这里的等号要求：

- boundary outputs 相同。
- exit state 相同。
- 对 region 外部可见的 commit order 与 visibility 相同。
- 被删除的信息只经过 semantics-preserving quotient 删除。

把每个已认证 region 收缩为 macro-event，得到 execution DAG：

$$
\mathcal D_{\mathrm{ref}}(L)
\xRightarrow{\text{certified contraction}}
\mathcal D_{\mathrm{exec}}(L).
$$

这一区分很重要。Mamba 的细粒度 reference recurrence 可以是长度为 $L$ 的 chain，但 scan certificate 允许把它替换成对数深度的 scan network。类似地，causal attention 的细粒度依赖很多，但可以由经过证明的 causal bulk kernel 承载。

因此，Tide 真正追求的不是“原始 reference DAG 看起来没有链”，而是：

> reference DAG 能否被划分成具有局部等价证书的 regions，并使收缩后的 execution DAG 具有较低 span。

## 10. 五类 Execution Capability

这些 capability 是 sub-DAG 的 lowering contract，不是没有验证义务的提示标签。

| Capability | 语义条件 | 主要并行方式 | 典型例子 |
| --- | --- | --- | --- |
| `token-local` | token 之间没有 mutable temporal dependency | batch / map | FFN、Norm、projection、token-local router |
| `scan-composable` | transition 有紧凑且封闭的 associative summary | parallel prefix scan | Mamba/SSM、affine recurrence |
| `causal-bulk` | 存在已证明等价的 causal chunk operator | attention/conv 等专用 bulk kernel | causal attention、causal convolution |
| `frontier-local` | 同一 ready frontier 内没有相互依赖或可见写冲突 | wavefront packing | message-passing round、MoE routing |
| `sequential-fallback` | 尚无可用的并行等价 lowering | exact sequential execution | 当前 LH persistent selector |

### 10.1 Token-local

若对所有 token $t$：

$$
z_t=f(x_t;\theta),
$$

并且 $f$ 不读取由其他 token 在本 region 内更新的 mutable state，则所有 $z_t$ 可以并行计算。

`token-local` 不要求所有 token 采用同一路径。MoE router 可以根据每个 token 的 hidden state 动态选择不同 expert，只要同层 token 的 routing decisions 不通过 mutable selector state 相互影响。

### 10.2 Scan-composable

考虑 recurrence：

$$
s_{t+1}=F_t(s_t).
$$

若每个 $F_t$ 都有固定或紧凑大小的 summary $m_t$，并存在 associative operator $\otimes$，使区间 transition 满足：

$$
m_{[a,c)}=m_{[b,c)}\otimes m_{[a,b)},
\qquad a<b<c,
$$

则可以使用 parallel scan 计算全部 prefix states。

关键不是“函数复合在数学上总是 associative”。工程有用的 scan 还要求：

- summary 大小不会随 chunk 增长。
- summary family 在组合后保持封闭。
- 组合成本足够低。
- sparse transition 组合后不会产生不可接受的 densification。

Scan 最常用于 node/kernel 内部，但也可以用于 subgraph。若一个 subgraph 具有固定边界状态，并且它的整体 boundary transition 满足上述条件，那么整个 subgraph 可以声明 `scan-composable`。一般动态 Graph 通常没有这一性质，Tide 不应假设 whole-graph scan 自动成立。

### 10.3 Causal-bulk

有些 causal operator 没有适合的有限维 associative summary，但已有高性能 chunk algorithm。若 reference operator 为：

$$
y_t=G_t(x_0,\ldots,x_t;S_0),
$$

定义 reference decode fold：

$$
\operatorname{DecodeFold}_L(X_{0:L},S_0)
=
((y_0,y_1,\ldots,y_{L-1}),S_L),
$$

其中每个 $(y_t,S_{t+1})$ 都由第 9.1 节定义的
$\operatorname{Step}(x_t,S_t)$ 依次产生。若 chunk kernel $K_L$ 对所有合法输入满足：

$$
K_L(X_{0:L},S_0)
=\operatorname{DecodeFold}_L(X_{0:L},S_0),
$$

则它可以声明 `causal-bulk`。GPT causal attention 是主要例子；它不需要被强行解释为 Mamba 风格的 scan。

### 10.4 Frontier-local

在 event DAG 中，定义 frontier $F_k$ 为一组前驱均已完成、当前可以执行的 events。若 $F_k$ 中任意两个 events：

- 不读取对方尚未提交的 state。
- 不通过 mutable control state 改变对方的 routing decision。
- 不发生未定义顺序的 conflicting writes。

则该 frontier 可以并行执行并按 kernel role 打包。

`layer-local` 是 `frontier-local` 在规则 Transformer chain 中的特殊情况。一般 Tide Graph 未必具有 layer；它可能按 graph distance、internal round，或者 $(t,r)$ 的 anti-diagonal 形成 wavefront。

Phase 与 frontier 也不相同。Phase 定义大范围的 barrier、visibility 与 commit order；frontier 是满足这些约束后，由实际 event dependencies 产生的更细粒度 ready set。

### 10.5 Sequential fallback

任意无法归入前述类别的 reference region，仍可以由 exact interpreter 或 fused sequential kernel 执行。这保证了 Tide 表达能力，但不能把 kernel fusion 误报成 sequence parallelism。

若一个 fallback region 的 span 随 chunk 长度 $L$ 线性增长，并且位于全局 critical path 上，它就可能决定整个模型的 prefill 上限。当前 persistent LH selector 是主要候选。

## 11. Capability Contract

Node 或 subgraph 的 capability declaration 至少应包含：

```text
reference_step
boundary_inputs / boundary_outputs
state_reads / state_writes
visibility / commit contract
chunk_lowering
correctness obligation
work / span / communication model
supported backend implementations
```

同一个 primitive 可以有多个 lowering。例如，一个 recurrence 可以同时提供：

- 用于 correctness oracle 的 sequential implementation。
- CPU parallel scan。
- Ascend 专用 scan kernel。
- 不满足规模阈值时的 sequential fallback。

Capability 也允许层级化。多个普通 nodes 组成的 subgraph，可以在证明整体 boundary transfer 后注册为一个更强的 macro-kernel。这样无需为了适配 LH 的每个实现细节而把所有机制都固定在最底层 node abstraction 中。

## 12. 适合 Tide 的 Graph 约束

一个有希望成为 `prefill-native` 的局部通信、超稀疏 Graph，应优先满足以下设计约束。

### 12.1 Sparse work

令 $A_{t,r}$ 是 token $t$、round $r$ 的 active event set。总 work 应主要与：

$$
\sum_{t=0}^{L-1}\sum_{r=0}^{R-1}|A_{t,r}|
$$

及实际 active edges 数量相关，而不是与 $L\,R\,|V|$ 相关。运行时不能通过“执行全部 node 再 mask”隐藏地失去超稀疏性，除非它作为明确的小规模 fallback。

### 12.2 Explicit state ownership

多个 events 对同一 state location 的写入只允许几种可判定形式：

- single-writer / exclusive ownership。
- associative reduction。
- 显式 versioned ordered writes。
- 进入 sequential fallback。

否则，Graph 虽然可以动态执行，但 chunk lowering 无法确定 visibility 与 commit semantics。

### 12.3 Prefill-capable temporal state

跨 token state 应尽量由 `scan-composable` 或 `causal-bulk` kernel 承载。对于只在部分 token 激活的 node，可以把该 node 的事件压成按 logical time 排序的稀疏 event stream，再执行 segmented scan 或 packed causal kernel。

如果 state transition 包含时间间隔，kernel 需要显式接收 token id、round id 或 gap $\Delta t$。例如固定 decay 可以把未激活区间折叠为 $A^{\Delta t}$，而不是逐 token 执行空操作。

### 12.4 Frontier-local routing

Router 应优先读取当前 event input 和已提交 predecessor state。它不应在同一 frontier 内用一个全局 mutable counter 逐个更新其他 token 的选择优先级。

可接受的 routing 形式包括：

- token-local top-k。
- 基于上一 frontier snapshot 的 routing。
- scan-composable controller state。
- speculation + validation + replay。

当前 LH selector 可以保留为机制样本和 correctness fallback，但不应默认成为 Tide 高性能 profile 的必要组成。

### 12.5 Explicit fallback tax

每个 sequential fallback 都要进入 span report。若 runtime 只是把多个逻辑 tick pack 到一个 kernel 内顺序执行，work 和 launch overhead 可能改善，但 logical span 没有被消除。

## 13. Work、Span 与通信的联合目标

令：

- $W$ 是 execution DAG 的总 work。
- $D$ 是 execution DAG 的 critical-path span。
- $C$ 是跨 node、device 或 memory region 的通信量。
- $P$ 是可用 parallel workers 数量。

理想调度下，并行时间受以下形式约束：

$$
T_P\lesssim \frac{W}{P}+D,
$$

同时还受通信、内存带宽和 kernel efficiency 影响。

“局部通信 + 超稀疏”主要降低 $W$ 与 $C$；`token-local / scan-composable / causal-bulk / frontier-local` 主要降低 $D$。只满足前者还不够：一条极稀疏但跨全部 token 的自适应链，work 很小，却无法获得高吞吐 prefill。

可以据此定义三个运行等级：

| 等级 | 定义 |
| --- | --- |
| `prefill-native` | 所有随 $L$ 增长的主要依赖链都能由 batch、scan、bulk 或 wavefront contraction 处理 |
| `prefill-compatible` | chunk correctness 成立，但仍残留少量随 $L$ 增长的 sequential span |
| `decode-only` | 关键路径基本随 token 数线性增长，chunk 主要只是 fused sequential execution |

## 14. 三类模型如何落入该设计

### 14.1 GPT-style Transformer

- Norm、projection、FFN 和 residual arithmetic 是 `token-local`。
- causal self-attention 是 `causal-bulk`。
- block chain 仍按深度顺序执行，但它的 token-axis 不需要退回逐 token loop。

因此，模型 span 主要随 block depth 增长，而不是随 `block depth × token count` 增长。

### 14.2 Mamba/SSM

- input projection、gate 和多数 pointwise operator 是 `token-local`。
- selective recurrent state 是 `scan-composable`。
- local convolution 可以是 `causal-bulk` 或专门的 scan/bulk lowering。

### 14.3 Dynamic sparse Tide Graph

考虑每个 round：

$$
M_{t,r}=\operatorname{EdgeKernel}(A_{t,r-1}),
$$

$$
H_{t,r}=\operatorname{NodeKernel}(M_{t,r},S_{t,r}),
$$

$$
A_{t,r}=\operatorname{Router}(H_{t,r}).
$$

如果：

- `NodeKernel` 可由 token-local、scan 或 causal-bulk lowering 承载。
- `Router` 是 token-local 或 frontier-local。
- inbox aggregation 是 associative reduction，或有显式 ordered semantics。
- node state 不与 routing 构成跨 token 的不可组合串行闭环。

那么每个 round 可以把所有 token、active nodes 按 role 和 kernel type 打包。Graph 路径仍然可以是动态的，但 execution span 主要随 internal rounds 与 graph dependency depth 增长，而不是直接退化为 $\Theta(LR)$。

当前 LH selector 的困难正是它同时引入 persistent selector state、active-set-dependent future computation 和 conditional memory side effects。它可以被 Tide 正确表达，却暂时只能声明 `sequential-fallback`，直到找到等价的 composable lowering、可验证 speculation，或者重新定义 selector semantics。

## 15. 推荐的架构分层

Tide 可以据此划分为六层：

1. **Reference semantics**：定义 `Step(input_token, State)`、phase、visibility 和 commit order。
2. **Logical Event IR**：展开有限 chunk 的 token/round/phase/node/state-version dependencies。
3. **Capability registry**：登记 node/subgraph 的 reference operator、chunk lowering 与证明义务。
4. **Region partition and lowering**：识别 token-local、scan、causal-bulk、frontier-local regions，并生成 execution DAG。
5. **Sparse scheduler and backend**：active event compaction、role-aware packing、CPU/Ascend lowering、barrier 与 state commit。
6. **Verification and cost witness**：验证 output/final-state equality，并报告 work、span、communication、memory 和 fallback critical path。

这个分层不要求 Tide 一开始解决任意动态 Graph。它允许从 GPT/Mamba 已知可行的 chain baseline 出发，逐步加入：

1. 固定稀疏 topology 与 all-active message passing。
2. Token-local dynamic routing。
3. Frontier-local sparse activation。
4. Node-local segmented scan 或 causal-bulk state。
5. 最后再研究 persistent/stateful selector、speculation 与 replay。

因此，当前设计目标可以最终概括为：

> “局部通信 + 超稀疏”负责降低 work 和 communication；`token-local / scan-composable / causal-bulk / frontier-local` 负责降低 span；reference event DAG、capability contract 与局部等价证明负责确保这些优化没有改变 decode semantics。
