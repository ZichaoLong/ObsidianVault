---
type: architecture-and-training
status: active-candidate
tags:
  - tide
  - hierarchical-backbone
  - sparse-routing
  - training-stability
  - prefill-decode
---

# Tide 模型架构与训练

> [!summary] 本页定位
> 本页统一记录 Tide 当前的正向模型候选、selector/allocator 能力契约、训练风险和实验顺序。第一部分的 HB-Lattice-v0 是可运行但尚未证明可训练的候选实例；第二、三部分是设计与验证约束，不是数学定理。一般空间 DAG 的正式定义见 [[tide-mathematical-foundations]]，自适应控制下界见 [[adaptive-routing-prefill-lower-bound]]。

> [!important] 语义边界
> `prefill`、`decode`、batch 组合和物理调度不得改变单序列 reference semantics。CPU selector、加速卡 packing、设备放置和通信流水只属于实现；若历史负载进入语义，它必须是逐序列隔离、可延续且可重放的正式状态。

## 第一部分：HB-Lattice-v0 候选架构



> [!summary] 本页定位
> 本页给出一个可以直接讨论、实现和否定的具体 Tide Graph 候选。它不是最终架构，也不是已经证明可训练的模型。它把层级 backbone、pre-norm residual、快慢路径、格子级专门化、节点级负载均衡、收到即更新、激活才发送以及 16 张 Ascend 卡映射，收缩成一个可重复的八平面 superblock。

> [!important] 与其他文档的关系
> 数学上，一般空间 DAG、显式 allocator、不等长路径和窗口拓扑序执行以 [[tide-mathematical-foundations#第二部分：显式 allocator 的一般空间 DAG|显式 allocator 的一般空间 DAG]] 为准。训练风险和 MoE 参考已整合到本页第二部分。本部分只实例化一个正向架构，不替代数学定义。

### 一页版

HB-Lattice-v0 使用四级嵌套结构：

~~~text
Level-0：1 个 Global Hub
    -> Level-1：4 个 Region Hubs
        -> Level-2：16 个 Cell Backbones
            -> Level-3：每个 cell 16 个 Leaf Sites，共 256 个
~~~

一个 superblock 有八个宏平面：

~~~text
P0  Cell/Hub Entry
P1  常亮 PreNorm Attention
P2  Attention Residual Merge
P3  常亮 PreNorm FFN
P4  FFN Residual Merge，形成快路径结果并 fork
P5  第一级稀疏 leaf 计算
P6  第二级稀疏、局部跨 cell 传播
P7  固定 deadline merge，写回下一 superblock backbone
~~~

P0-P4 是 GPT-like 快路径；P4-P7 是可被 selector 真正短路的慢路径。第一版物理执行仍严格按 P0 到 P7 推进，所以快路径暂时不提前输出，但 P5/P6 未激活 kernel 可以不执行。

![[assets/hb-lattice-v0-superblock.svg]]

### 代码导读：从 GPT block 到 HB-Lattice

本节只把后文的数学对象改写成连续程序，不增加新的模型语义。先看一个标准的 pre-norm GPT block：

~~~python
def pre_norm_gpt_block(x, state):
    # Attention 分支：读取并更新本 block 的因果状态。
    attention_delta, state.attention = causal_attention(
        norm(x),
        state.attention,
    )
    u = x + attention_delta

    # FFN 分支：没有跨 token 持久状态。
    ffn_delta = ffn(norm(u))
    y = u + ffn_delta
    return y, state
~~~

这里的 `x -> u -> y` 是常亮 backbone；Attention 和 FFN 都只产生 residual delta。若两个 delta 都为零，则 `y == x`。

HB-Lattice-v0 保留这个 block 作为 P0-P4 快路径，再从快路径结果 `fast[cell]` fork 出有界的 P5-P6 稀疏慢路径：

~~~python
def hb_lattice_superblock(token_chunk, state):
    # P0：一个 token chunk 扩展成 16 个 cell carrier。
    cell_input = inject_hub_and_cell_context(token_chunk, state)

    # P1-P4：每个 cell 都执行同一种 pre-norm GPT-like 快路径。
    fast = {}
    score_view = {}
    for cell in CELLS:
        fast[cell], score_view[cell], state.cell[cell] = pre_norm_gpt_block_chunk(
            cell_input[cell],
            state.cell[cell],
        )

    # P4：score_view[t] 只含位置 t 当时可见的因果状态，不能读取
    #     整个 chunk 提交后的最终 state.cell。
    cell_score = score_cells(fast, score_view)
    selected_cells, state.region_load = region_allocator.scan(
        cell_score,
        state.region_load,
    )

    # P5：被选中 cell 的全部 leaf 收到消息并更新状态；
    #     只有每个 cell 中被选中的 leaf 执行重 kernel。
    p5_inbox = send_fast_carrier_to_all_leaves(fast, selected_cells)
    p5_emit, state.p5 = run_sparse_leaf_plane(
        inbox=p5_inbox,
        state=state.p5,
        budget_per_cell=2,
    )

    # P6：P5 active leaf 只沿固定局部边发送；收件者仍是收到即更新。
    p6_inbox = fixed_local_fanout(p5_emit)
    slow_delta, state.p6 = run_sparse_leaf_plane(
        inbox=p6_inbox,
        state=state.p6,
        budget_per_cell=2,
    )

    # P7：按固定 source slot 合并；没有慢路径输出时 slow_delta 为零。
    output = deadline_residual_merge(fast, slow_delta)
    return output, state
~~~

稀疏平面的关键不是一个不透明的“路由算子”，而是下面五个可分别观测的步骤：

~~~python
def run_sparse_leaf_plane(inbox, state, budget_per_cell):
    payload = merge_each_inbox_in_fixed_source_order(inbox)

    # 只要收到消息就执行，不能被 hard selector 跳过。
    for leaf in payload:
        state[leaf].observer = update_observer(
            state[leaf].observer,
            payload[leaf],
        )

    score = cheap_score(payload, state)
    active, state.load = allocator_scan(score, state.load, budget_per_cell)

    # 未激活 leaf 到此结束；它已经提交 observer/load 状态。
    output = {}
    for leaf in active:
        output[leaf] = heavy_leaf_kernel(payload[leaf], state[leaf])
    return output, state
~~~

因此，程序中的对象可以直接对应到八个平面：

| 程序变量或调用 | 平面 | 含义 |
| --- | --- | --- |
| `cell_input` | P0 | 注入 Global/Region context 后的 cell carrier |
| `causal_attention` | P1 | 常亮 Attention residual delta |
| `u = x + attention_delta` | P2 | Attention 固定双槽 merge |
| `ffn` | P3 | 常亮 FFN residual delta |
| `fast`、`region_allocator.scan` | P4 | 快路径结果与第一级 cell 选择 |
| 第一次 `run_sparse_leaf_plane` | P5 | cell 内稀疏 leaf 计算 |
| 第二次 `run_sparse_leaf_plane` | P6 | 局部跨 cell 稀疏传播 |
| `deadline_residual_merge` | P7 | 固定截止点写回 cell backbone |

可运行的结构 reference 见 [hb_lattice_v0_reference.py](examples/hb_lattice_v0_reference.py)。它仅使用 Python 标准库，以小向量 toy kernels 展示 P0-P7、状态生命周期、route artifact 和 `chunk == repeated decode`；它不实现真实 Attention、训练或设备并行。

在 Vault 根目录可直接运行：

~~~bash
python 20-tide-decentralized-neural-network/examples/hb_lattice_v0_reference.py
~~~

> [!important] reference 中的两个显式状态约束
> 1. P1 为每个位置返回当时可见的 `score_view`；P4 selector 不得让早期位置读取处理完整个 chunk 后的 Attention/KV/SSM 最终状态。
> 2. P5 与 P6 使用两个 stage-local 的 observer/load state namespace。即使它们物理上位于同一 leaf site 或同一张卡，也不能默认共享可变状态。若未来要求共享，必须另行证明两个平面的状态更新可交换、可 scan，或改变执行 schedule；否则 `P5(all tokens) -> P6(all tokens)` 与逐 token 的 `P5(t) -> P6(t)` 一般不等价。

### 1. 固定实例参数

下表不是永久约束，而是为了让第一次实现和实验有唯一对象。

| 参数 | v0 取值 | 含义 |
| --- | ---: | --- |
| $R_x\times R_y$ | $1\times4$ | 4 个 region，每个覆盖一行 cell |
| $C_x\times C_y$ | $4\times4$ | 每个稀疏平面有 16 个 cell |
| $N_x\times N_y$ | $4\times4$ | 每个 cell 有 16 个 leaf site |
| Leaf 总数 | 256 | 一个 P5 或 P6 平面的叶节点槽位数 |
| Superblock 平面数 | 8 | P0-P7 |
| Region 慢路径预算 | 2 cells/region | 一个 token 在一个 region 中最多选择 2 个 cell 进入慢路径 |
| P5 叶节点预算 | 2 leaves/selected cell | 每个选中 cell 最多激活 2 个 leaf |
| P6 叶节点预算 | 2 leaves/destination cell | 收到候选消息后，每个目标 cell 最多继续激活 2 个 leaf |
| Leaf 固定消息度数 | 不超过 9 | 同点、cell 内四邻接及相邻 cell 对应点 |
| 慢路径最长寿命 | 3 宏平面 | 从 P4 fork 到 P7 merge |
| Ascend 映射 | 1 cell/card | 16 个 cell 静态映射到 16 张卡 |

Superblock 数量记为 $S$，由 scaling experiment 决定。v0 不预设必须像 GPT 一样使用 96 个 block。

### 2. 三个互不等同的坐标

#### 2.1 拓扑平面

P0-P7 只表示一个 superblock 内的执行先后。平面不是神经生物学层，也不是语义专门化等级。

#### 2.2 层级

Global、Region、Cell、Leaf 表示状态与路由的包含关系。一个 Leaf 慢路径可以跨 P5 和 P6 两个平面；同一 P4 平面同时包含 Cell backbone、Region selector 和 Global/Region carrier。

#### 2.3 几何位置

每个 cell 有二维坐标 $(i,j)$，每个 leaf 有 cell 内坐标 $(u,v)$。几何位置决定固定邻接和设备放置，不自动决定语义专门化。

因此，`plane`、`hierarchy level` 和 `spatial coordinate` 必须在代码中使用不同字段。

### 3. 平面不要求同构

八个平面使用同一个 4x4 cell 坐标模板，便于静态设备放置，但实际节点角色不同：

| 平面 | 主要角色 | 逻辑宽度 |
| --- | --- | ---: |
| P0 | Global/Region/Cell Carrier | 1 + 4 + 16 |
| P1 | Cell Attention Compute | 16 |
| P2 | Cell Residual Merge-A | 16 |
| P3 | Cell FFN Compute | 16 |
| P4 | Cell Residual Merge-F、Region/Cell Selector | 16 + selector state |
| P5 | Leaf StateUpdate/Compute | 256 候选，少量激活 |
| P6 | Leaf StateUpdate/Compute | 256 候选，少量激活 |
| P7 | Cell Deadline Merge、Region/Global Summary | 16 + 4 + 1 |

数学图不要求这些平面同构。实现可以为每个 cell 保留统一静态槽位，再使用 `role mask` 指示本平面哪些槽位承担何种角色。

### 4. Node role 与 kernel kind

外层空间图只使用少量稳定角色。

| Node role | 状态 | 输入 | 输出 |
| --- | --- | --- | --- |
| `Carrier` | Global/Region/Cell 神经状态 | 固定父级 context、上一个 superblock 状态 | 下一 carrier 或 branch 输入 |
| `Compute` | 可有 KV/SSM/observer state | 固定输入槽或带时间的消息集合 | residual delta 或传播消息 |
| `Merge` | 通常无长期状态 | 固定来源槽位 | 单一 carrier state |
| `Allocator` | 单序列负载和 quota 状态 | 语义 score、静态候选和历史负载 | activation mask/weight |
| `DelayBuffer` | 在途消息 | 固定时延输入 | 指定逻辑时间的输出 |
| `Input/Output` | 输入/读出状态 | token 或最终 carrier | embedding 或 logits |

具体算子由独立的 `KernelKind` 指定，例如 Attention、FFN、SSM、Linear、Adapter、Add、WeightedSum。

Identity 默认用直接边或 tensor alias 表达，不建立独立空间节点。只有需要固定时延、跨设备缓存或 artifact 观测时，才使用 `DelayBuffer`。

#### 4.1 Merge 不等于任意 Aggregate

v0 优先使用固定来源槽位：

~~~text
Residual Merge-A:
    slot 0 = backbone bypass
    slot 1 = attention delta

Residual Merge-F:
    slot 0 = attention-merged carrier
    slot 1 = FFN delta

Deadline Merge:
    slot 0 = fast-path carrier
    slot 1..K = bounded sparse deltas ordered by source id
~~~

缺失稀疏 delta 以零元素填充。v0 不使用“物理到达多少条就临时聚合多少条”的无界 Aggregate。

### 5. 四级 backbone

#### 5.1 Global Hub

Global Hub 持有维度较小的全局 carrier $g_s$。v0 可先使用恒等或小型 SSM：

$$
g_s^{\mathrm{base}}=P_s^{G}(g_s).
$$

它不是完整 hidden tensor 的集中副本，而是低带宽全局 context。

#### 5.2 Region Hub

四个 Region Hub 分别覆盖一行四个 cell。region 状态记为 $r_{s,q}$，其中 $q\in\{0,1,2,3\}$。

$$
r_{s,q}^{\mathrm{base}}
=
P_{s,q}^{R}(r_{s,q})
+
W_{s,q}^{G\to R}g_s.
$$

#### 5.3 Cell Backbone

16 个 cell backbone 是 v0 的主要语义专门化尺度。cell $c$ 的输入 carrier 为：

$$
x_{s,c}
=
b_{s,c}
+
W_{s,c}^{R\to C}r_{s,\rho(c)}
+
W_{s,c}^{G\to C}g_s,
$$

其中 $\rho(c)$ 给出 cell 所属 region。

每个 cell 持有自己的共享神经状态 $Q_{s,c}$，第一版可以选择：

- cell-local KV cache；
- cell-local SSM state；
- linear-attention accumulator；
- 上述状态的一个明确组合。

#### 5.4 Leaf Site

每个 cell 有 16 个 leaf site。v0 中 leaf 主要承担稀疏 residual compute，不首先让每个 leaf 持有无界独立 KV。

每个 leaf 可持有：

- 有界 observer state；
- node-specific adapter 参数；
- 由所属 cell allocator 维护的激活计数；
- 可选的小型固定维度 SSM state。

昂贵 Attention 若需要长历史，优先读取 cell 共享状态 $Q_{s,c}$。这是为了让格子级专门化与格子内负载均衡可以同时成立。

### 6. 八个平面的逐步语义

#### P0：Entry 与层级 context 注入

输入为上一个 superblock 的 $g_s$、$r_{s,q}$、$b_{s,c}$，以及当前 token 在各层级的输入消息和左边界持久状态。

操作：

1. 更新 Global/Region cheap backbone。
2. 将 Global/Region context 投影到 16 个 cell carrier。
3. 得到每个 cell 的 $x_{s,c}$。

输出 P1 Attention 分支输入，以及到 P2 的 identity bypass。

#### P1：常亮 PreNorm Attention

每个 cell 执行：

$$
a_{s,c}
=
A_{s,c}
\left(
\operatorname{Norm}(x_{s,c}),
Q_{s,c}
\right).
$$

这是 GPT-like Level-1 分支，v0 中 gate 恒为 1。Attention 只读取本 cell 状态，不直接做全图 all-to-all。

若当前消息需要写入 cell KV/SSM，状态更新与 Attention readout 的先后关系必须由 kernel contract 明确声明。

#### P2：Attention residual merge

固定双槽 merge：

$$
u_{s,c}=x_{s,c}+a_{s,c}.
$$

P2 是 Attention branch 的 merge point。

#### P3：常亮 PreNorm FFN

$$
f_{s,c}^{\Delta}
=
F_{s,c}
\left(
\operatorname{Norm}(u_{s,c})
\right).
$$

#### P4：FFN merge、快路径完成与慢路径 fork

$$
f_{s,c}=u_{s,c}+f_{s,c}^{\Delta}.
$$

$f_{s,c}$ 是一个完整 GPT-like cell block 的输出。它通过 bypass 直接送往 P7，形成最短非平凡路径。

P4 同时产生慢路径 score：

$$
\sigma_{s,c}
=
\operatorname{CellScore}
\left(
f_{s,c},Q_{s,c},r_{s,\rho(c)}
\right).
$$

Region selector 在每个 region 的四个 cell 中最多选择两个进入 P5。

#### P5：第一级稀疏 leaf

选中 cell 的 16 个 leaf 候选收到来自 $f_{s,c}$ 的固定消息。所有收到消息的 leaf：

1. 更新有界 observer state。
2. 计算 cheap leaf score。
3. 把 score 与单序列历史负载交给 cell allocator。

每个选中 cell 最多激活两个 leaf。只有被激活 leaf 执行：

$$
m_{s,c,j}^{(2)}
=
L_{s,c,j}^{(2)}
\left(
f_{s,c},Q_{s,c},o_{s,c,j}
\right),
$$

并向 P6 的固定局部邻接发送消息。

#### P6：第二级稀疏与局部跨 cell 传播

P6 候选 leaf 根据 P5 实际激活消息到达。所有收到消息者更新状态；每个目标 cell 最多继续激活两个 leaf。

被激活 leaf 计算：

$$
m_{s,c,j}^{(3)}
=
L_{s,c,j}^{(3)}
\left(
I_{s,c,j}^{(3)},Q_{s,c},o_{s,c,j}
\right).
$$

输出被标记固定 `merge_cell`，表示它在 P7 写回哪个 cell backbone。

#### P7：固定 deadline merge

对 cell $c$，将所有合法且有界的慢路径 delta 按 source id 放入固定槽位：

$$
\delta_{s,c}^{\mathrm{slow}}
=
\operatorname{MergeSlow}_c
\left(
\{m_{s,\cdot,\cdot}^{(3)}\to c\}
\right).
$$

最终 cell carrier：

$$
b_{s+1,c}
=
f_{s,c}
+
\delta_{s,c}^{\mathrm{slow}}.
$$

若慢路径未激活，则 $\delta_{s,c}^{\mathrm{slow}}=0$，结果精确退化为 P4 快路径。

Region 和 Global summary 在 P7 更新：

$$
r_{s+1,q}
=
r_{s,q}^{\mathrm{base}}
+
\sum_{c:\rho(c)=q}
W_{s,c}^{C\to R}b_{s+1,c},
$$

$$
g_{s+1}
=
g_s^{\mathrm{base}}
+
\sum_q
W_{s,q}^{R\to G}r_{s+1,q}.
$$

为了控制通信量，$g$ 与 $r$ 的维度应明显小于 cell hidden width。

### 7. Branch 声明

#### 7.1 Attention branch

| 字段 | 值 |
| --- | --- |
| Parent | Cell backbone |
| Entry | P0 cell carrier |
| Compute | P1 |
| Merge | P2 Add-A |
| 最大寿命 | 2 宏平面 |
| Gate | v0 恒为 1 |
| 输出 | Attention residual delta |

#### 7.2 FFN branch

| 字段 | 值 |
| --- | --- |
| Parent | P2 cell carrier |
| Entry | P2 |
| Compute | P3 |
| Merge | P4 Add-F |
| 最大寿命 | 2 宏平面 |
| Gate | v0 恒为 1 |
| 输出 | FFN residual delta |

#### 7.3 Sparse spatial branch

| 字段 | 值 |
| --- | --- |
| Parent | P4 fast cell carrier |
| Entry/Fork | P4 |
| Compute | P5、P6 |
| Merge | P7 Deadline Merge |
| 最大寿命 | 3 宏平面 |
| Region active fan-out | 最多 2 cells/region |
| Cell active fan-out | 最多 2 leaves |
| Leaf child fan-out | 一个 P5 leaf 最多向 9 个固定邻接发送消息；实际 P6 激活由每个目标 cell 的预算 2 约束 |
| 输出 | 写回指定 cell 的 residual delta |

### 8. 稀疏平面固定邻接

一个 leaf 用四元组 $(i,j,u,v)$ 标识：

- $(i,j)$：4x4 cell 坐标；
- $(u,v)$：cell 内 4x4 leaf 坐标。

P5 到 P6 的固定候选后继包括：

1. 同一 cell 的同坐标 $(u,v)$。
2. 同一 cell 内按环状边界计算的上、下、左、右四邻接。
3. 上、下、左、右相邻 cell 中的对应坐标 $(u,v)$。

因此固定消息度数不超过 9。cell 和 cell 内坐标都可以采用环状边界，使多次局部传播后全平面任意位置之间存在路径。

固定邻接只决定谁可以收到消息。selector 另外决定谁真正执行昂贵计算并继续发送。

![[assets/hb-lattice-v0-plane.svg]]

### 9. 具体 selector

#### 9.1 Region selector

对 region $q$ 内四个 cell，计算：

$$
\pi_{s,c}
=
\sigma_{s,c}
-
\lambda_R
\left(
\ell_{s,c}^{R}
-
\bar\ell_{s,q}^{R}
\right).
$$

最多选择两个 cell。v0 建议先比较：

1. 纯语义 Top-2。
2. 语义 Top-3 后按负载选 2。
3. 联合 score Top-2。

#### 9.2 Cell leaf allocator

在选中 cell 内：

$$
\pi_{s,c,j}^{L}
=
\sigma_{s,c,j}^{L}
-
\lambda_L
\left(
\ell_{s,c,j}^{L}
-
\bar\ell_{s,c}^{L}
\right).
$$

最多选择两个 leaf。由于 v0 的长历史主要属于 cell shared state，leaf 更接近计算 shard，可以比独立有状态专家使用更强负载均衡。

#### 9.3 控制状态

所有 $\ell$ 都是单序列状态：

$$
\ell_{t+1}
=
\beta\ell_t
+
(1-\beta)\mathbf 1[\text{selected at }t].
$$

不同 batch 中的序列不能共享该状态。物理设备实时负载不得写入语义 selector。

### 10. 节点执行契约

![[assets/hb-lattice-v0-node-contract.svg]]

对收到消息的 leaf，执行顺序固定为：

~~~text
Receive
    -> UpdateState
    -> CheapScore
    -> Selector
        -> inactive: commit state, no heavy kernel, no emit
        -> active: ActiveCompute, commit output, emit
~~~

因此，hard route 的物理短路边界是：

- `UpdateState` 和 `CheapScore` 不短路；
- `ActiveCompute` 和 `Emit` 可真实跳过；
- 若某个 kernel 同时负责状态更新和昂贵输出，实现必须先拆分后才能短路。

### 11. 一个 token 的具体路径示例

设 token $t$ 到达 superblock $s$：

1. P0：Global/Region context 注入全部 16 个 cell carrier。
2. P1-P4：16 个 cell 都执行 cell-local Attention 和 FFN，得到快路径 $f_{s,c}$。
3. Region R1 的 selector 从 C10-C13 中选中 C11、C12。
4. C11 在 P5 激活 leaf $(1,1)$、$(2,2)$；C12 激活 leaf $(0,1)$、$(1,2)$。
5. 四个 P5 leaf 向 P6 固定局部邻接广播；所有实际收件 leaf 更新 observer state。
6. P6 每个目标 cell 最多选择两个 leaf 继续计算。
7. P6 delta 分别标记要写回 C11、C12 或邻接 cell。
8. P7 将这些 delta 与各 cell 的 $f_{s,c}$ 相加，产生 $b_{s+1,c}$。
9. 四个 Region Hub 和 Global Hub 更新小维度 summary。

未选中的 region/cell/leaf 不执行慢路径重 kernel，但其 cell GPT-like 快路径仍然存在。

### 12. 输入扩展与输出收拢

整个模型最外侧使用层级树：

~~~text
Input token
    -> Global Hub
        -> 4 Region Hubs
            -> 16 Cell Backbones
                -> S 个 HB-Lattice superblocks
            -> 4 Region readout summaries
        -> Global readout
    -> Final Norm + LM Head
~~~

输入扩展和输出收拢都使用固定槽位和固定投影，不使用无界动态 Aggregate。

若所有 Attention、FFN 和 sparse residual delta 都为零，并且 hub/cell cheap backbone 取 identity，则整个 hidden carrier 退化为层级直通。若 hub/cell 使用小型 SSM，则退化为一个廉价 always-on recurrent backbone。

### 13. Prefill / decode 执行

第一版不做异步 early exit。对一个 chunk，在每个 superblock 内执行：

~~~text
P0：批量 context inject
P1：16 cells × batch × tokens 的 packed Attention
P2：批量 fixed-slot Add
P3：16 cells × batch × tokens 的 packed FFN
P4：批量 score；CPU 按序列扫描 selector
P5：按 route list packed 执行选中 leaf
P6：按固定邻接构造 inbox；CPU 扫描；packed 执行
P7：批量 fixed-slot deadline merge
~~~

空间阶段数固定为 $8S$，不随 chunk 长度 $L$ 增长。节点内部是否能高效处理时间维度，仍分别取决于 Attention、SSM、selector scan 和 ragged state kernel。

要满足 `prefill = decode`，至少要求：

1. 所有 selector 状态按单序列隔离。
2. selector 不读取 chunk 长度、batch 同伴或设备实时负载。
3. 同一逻辑时间的消息采用固定 source order 或可交换 merge。
4. Attention 使用相同 causal mask、位置和 KV 可见性。
5. P7 是当前 token 的固定读出 deadline。
6. P5/P6 packing 只改变物理布局，不改变消息、选择、状态和 delta。
7. P4 对位置 $t$ 的 score 只读取位置 $t$ 可见的因果状态视图，不读取 chunk 末尾状态。
8. P5/P6 的可变状态要么使用不同 namespace，要么其跨平面更新已经证明对两种 schedule 等价。

### 14. 16 张 Ascend 卡映射

4x4 cell 与 16 张卡静态一一对应：

~~~text
A0  A1  A2  A3
A4  A5  A6  A7
A8  A9  A10 A11
A12 A13 A14 A15
~~~

每张卡持有对应 cell 在所有 superblock 中的：

- Cell Attention/FFN 参数与 cell shared state。
- 16 个 leaf site 的 adapter/observer state。
- P5/P6 packed workspace。
- 相邻 cell 的发送和接收 buffer。

Region Hub 可放在每行第一张卡，Global Hub 可放在 A0，或把小维度 hub state 复制到四个 region owner。该选择属于 backend placement，不改变语义图。

跨卡消息只沿上下左右相邻 cell 发送；Global/Region 小维度 summary 另走固定树形通信。

### 15. 为什么这是一个有用的第一版

它包含了当前讨论中的重要性质：

- pre-norm residual backbone。
- Global、Region、Cell、Leaf 四级层次。
- GPT-like 常亮 Attention/FFN 作为一级扩展。
- 真正可以不执行 kernel 的两级稀疏慢路径。
- 快路径和慢路径在固定 deadline merge。
- 分支 fan-out、最长寿命和 merge point 均有界且可记录。
- cell 级语义专门化与 leaf 级负载均衡可以分离。
- 收到消息即更新，激活才重计算和继续发送。
- 固定局部通信与 16 卡静态映射。
- chunk 物理 packing 不进入模型语义。

它也故意没有包含：

- 反馈环或 zero-delay loop。
- `late-context update`。
- 任意长度、没有 deadline 的游走信号。
- leaf-local 无界 KV。
- 依赖 batch 同伴的 expert-choice routing。
- 任意来源、任意数量、按物理到达顺序求值的 Aggregate。
- 真正提前返回的 wall-clock fast path。

### 16. 最需要审视的设计选择

1. 16 个 cell 全部运行 GPT-like Attention/FFN 是否仍然太昂贵？
2. Cell 是正确的专门化尺度，还是 Region/Leaf 更自然？
3. P5-P6 两级慢路径是否足够表达空间局部计算，还是需要更多级？
4. 每个 superblock 都更新 Global/Region summary 是否过强或带宽过高？
5. cell shared KV 是否损失了 leaf-local memory 的表达力？
6. 固定 P7 deadline 是否过度限制不同计算时延？
7. 慢路径最终 residual add 是否足以表达希望的复杂处理？
8. 环状几何邻接是否合理，还是应改为 Delaunay、learned static topology 或其他结构？
9. Region 先做语义选择、Cell 内做负载选择是否符合预期？
10. 第一版应使用 Attention、SSM，还是二者混合构成 cell backbone？

这些问题可以逐项改变，而不需要推翻本页的四层对象和八平面执行骨架。

---

## 第二部分：Selector 与训练稳定性



> [!summary] 本页定位
> 本页记录分层点阵 Tide 候选架构中，CPU 侧严格时间递推 selector、加速卡侧节点计算、稀疏路径和节点持久状态共同带来的训练问题，以及从公开 MoE 研究和先进开源模型技术报告中可借鉴的稳定化方法。本文是研究备忘，不是数学定理、最终架构规范或已经验证的训练方案。

> [!example] 具体架构实例
> 本部分讨论一般训练风险；把这些约束收缩成四级 backbone、八平面 superblock、16 卡映射和三张结构图的具体候选见本页第一部分。

### 1. 当前候选架构

当前讨论的平面点阵首先是一个最低复杂度实例，不应被理解为最终只能有“平面、格子、节点”三个固定层次。更一般的候选架构可概括为：

1. 空间图由有限个前向计算阶段组成；最简单实例是顺序堆叠 32 或 96 个平面。
2. 每个平面包含规则点阵；最低层计算单元暂称节点，若干节点组成格子。
3. 节点之上还可以有 hub、区域、格子组或更高层 backbone。后续实现不应把层次数写死，而应允许配置多个路由与聚合尺度。
4. 为了使第一版理论和实现可控，层级区域优先采用嵌套或互不相交的层次划分。任意重叠区域会使状态归属、selector 读写范围和负载统计明显复杂化，可后置研究。
5. 每个节点只连接拓扑后继中的少量节点，因而通信度数有界。最低复杂度实例只允许相邻平面连接；后续可加入只向前的跨平面 shortcut。
6. 上游已激活节点向所有邻接后继发送消息。收到消息的节点总是执行状态更新；是否执行昂贵计算并继续发送，由本节点所属层级的 selector 或其他激活机制决定。
7. selector 可以存在于节点、格子或更高区域层级。不同层级可以使用不同策略，例如高层 always-on、格子级语义选择、格子内节点级负载分配。
8. selector 预期主要在 CPU 上处理紧凑控制数据；节点的大批量数值计算预期由加速卡处理。
9. 4x4 个格子可以静态映射到本机 16 张加速卡；每张卡负责一个格子在多个平面中的节点，跨格子通信只发生在几何相邻设备之间。

这里需要区分三个相互独立的层次概念：

| 概念 | 作用 |
| --- | --- |
| 计算层级 | 哪些节点或区域执行神经计算、持有什么神经状态 |
| 路由层级 | selector 在什么范围读取摘要、维护负载状态并作出激活决定 |
| 设备层级 | 节点、格子或区域如何映射到 CPU 与加速卡 |

三者不必一一对应。一个格子可以是语义专门化单元，格子内多个节点则只是共享或近似共享参数的容量副本；同一个设备也可以承载多个计算层级。

这个候选架构的主要吸引力是：

- 空间计算图保持 DAG，可按平面推进。
- 空间局部性限制单次通信范围。
- 稀疏发送激活限制昂贵节点计算和后续传播规模。
- 一个平面内可以把多个 batch、多个 token 和多个节点的工作打包后交给加速卡。
- 小规模、顺序敏感的控制递推可以交给擅长复杂控制流的 CPU。

但计算放置本身不能解决训练问题。hard selector 是否稳定、节点是否获得充分梯度、路由变化是否改变未来状态分布，仍由模型语义和训练方法决定。

### 2. 核心判断

不能把训练难度简单写成：

$$
\text{Transformer}<\text{Mamba}<\text{MoE}.
$$

更准确的比较如下。

| 架构 | 计算图与梯度 | 主要风险 |
| --- | --- | --- |
| Dense Transformer | 固定计算图，所有激活参数连续参与前向和反向 | attention logit、低精度数值、优化器和大规模系统稳定性 |
| Mamba / SSM | 固定且连续可微的递推，通常可用 scan 并行 | 递推状态数值稳定性、长程梯度、稳定参数化和高性能 scan kernel |
| 标准 MoE | hard Top-K 改变每个 token 的计算子图，只有选中专家获得主要任务梯度 | 路由漂移、专家饥饿、负载不均衡、selected-only feedback 和分布式通信 |
| 分层点阵 Tide | hard routing 可改变后续多个平面的完整传播路径，并可与节点状态和历史负载状态耦合 | 标准 MoE 风险之外，还增加长路径信用分配、路径分布漂移和状态/路径耦合 |

因此，Mamba 不一定在优化意义上比 Transformer 更难，MoE 也不必然产生 loss spike。但 hard routing 确实引入了一组 dense Transformer 和连续 SSM 没有的训练风险。若 Tide 的一次选择会改变后续几十个平面的路径，其训练问题一般比单层 MoE 更强。

### 3. 公开研究对路由漂移的结论

#### 3.1 路由漂移真实存在

StableMoE 把 routing fluctuation 定义为：同一个验证输入在不同训练 checkpoint 被分配给不同目标专家。

其 BASE Layer 实验报告：

- 40.9% 的 token 在训练完成 20% 后仍改变目标专家。
- 29.1% 的 token 在训练完成一半后仍改变目标专家。
- 15.4% 的 token 在训练完成 80% 后仍改变目标专家。

StableMoE 的解释是：同一个输入先后更新不同专家，而最终推理只使用其中一个专家，因此梯度被分散，样本效率下降。其解决方案是先学习并蒸馏 router，然后冻结蒸馏后的 router。

“此前专家的训练结果完全失效”仍是过强表述。旧专家的参数不会消失，也可能继续服务相似输入；更准确的后果是：

1. 同一类输入的训练信用被分散到多个专家。
2. 新接手的专家需要适应新的输入分布。
3. router 决策边界附近的输入可能反复切换，产生额外梯度噪声。
4. 若大量输入同时迁移，某些专家会突然过载或突然失去数据，可能形成更明显的训练扰动。

#### 3.2 专家专门化不是必然结果

公开研究给出了相互补充、但并不完全一致的观察。

- ST-MoE 观察到部分 encoder 专家具有专门化，但 decoder 专家的清晰专门化弱得多。
- DeepSeekMoE 认为传统 MoE 容易发生知识混杂和知识冗余，并以细粒度专家和 shared expert 促进组合式专门化。
- DeepSeek-V3 报告，相比逐序列强制均衡，batch-wise、低干扰的负载平衡允许更明显的领域专门化。
- OLMoE 从头训练 64 个细粒度专家、每 token 激活 8 个，观察到领域和词表专门化；但同一研究发现 Mixtral 的领域专门化较弱。
- OLMoE 的小规模消融中，固定 shared expert 略差于全部 routed experts；Qwen3 也不使用 shared expert。
- 2026 年的 Less is MoE 给出另一种警告：某些能力分散在多个专家中，但集中在 routed FFN 的少量内部维度，不能把一个完整专家直接等同于一个稳定领域模块。

因此，Tide 不应把“每个节点形成清晰的人类可命名领域”作为必要成功条件。更稳妥的目标是：节点形成对任务有用的组合式计算子空间，路由具有可复现的统计偏好，同时整体质量和计算效率提高。

#### 3.3 MoE 不是 loss spike 的唯一来源

先进开源模型的公开报告表明，大规模 MoE 可以稳定训练，但需要同时控制路由、attention、优化器和低精度数值问题。

| 模型 | 公开的相关设计或观察 |
| --- | --- |
| DeepSeek-V3 | 1 个 shared expert、256 个 routed experts、每 token 激活 8 个；使用只影响 Top-K 选择、不改变专家输出权重的负载偏置；偏置更新速度在前 14.3T token 为 0.001，最后 500B token 为 0；报告没有不可恢复的 loss spike 或 rollback |
| GLM-4.5 | 使用 sigmoid gate、loss-free balance 和 QK-Norm；负载偏置在前 15T token 更新，之后冻结 |
| Kimi K2 | 384 个 routed experts、每 token 激活 8 个并保留 1 个 shared expert；15.5T token 训练中报告没有 loss spike；报告定位的主要不稳定来源是 attention-logit explosion，并用 QK-Clip 处理 |
| Qwen3 MoE | 128 个专家、每 token 激活 8 个，不使用 shared expert；使用 global-batch load balancing loss 促进专门化，并用 QK-Norm 控制 attention 稳定性 |
| OLMoE | 64 个专家、每 token 激活 8 个；使用 load balancing loss 和 router z-loss；5T token 训练曲线没有明显大 spike，并公开了训练日志 |

由此应区分：

- 路由漂移主要直接影响样本效率、专家输入分布和信用分配。
- 路由坍缩、容量溢出或大规模同步换路可能触发显著训练扰动。
- attention logit、状态数值、优化器、梯度尺度和低精度误差可以独立产生 spike。
- “MoE 训练发生 spike”不能自动推出“spike 来自 router”。

### 4. Tide 中应分别测量的三种路由变化

路由变化应在多个层级分别测量。节点级选择可以频繁变化，而格子级或更高区域级选择仍然稳定；这时专门化可能发生在格子或区域，而不是单个节点。后续指标和实现接口都不应预设“专家必然等于叶节点”。

#### 4.1 参数变化引起的 checkpoint 漂移

固定同一条验证序列和同一初始状态，在不同训练 checkpoint 上比较节点选择。变化来自 router、上游节点或节点表示参数的更新。

这是 StableMoE 主要讨论的 routing fluctuation。

#### 4.2 历史状态引起的序列内变化

即使所有参数冻结，相同内容出现在不同 token 位置或不同历史负载之后，也可能被送往不同节点。例如一个节点最近已被频繁激活，selector 会降低其优先级。

这是当前 Tide selector 有意引入的变化，用于序列时间维度的负载均衡。它不是训练漂移，也不一定破坏更高层级专门化。例如：

- 语义 router 可以稳定地选择某个格子。
- 格子内 allocator 可以根据历史激活次数，在多个节点之间轮换。
- 格子形成稳定计算专门化，格子内节点主要承担容量分片或近似同质副本。

但“近似同质副本”不能只看参数。若格子内节点共享 kernel 参数，却分别持有不同 KV cache、SSM state 或局部记忆，它们对同一输入仍可能产生不同输出，不能只按负载任意互换。纯负载轮换较安全的前提是：相关参数和语义状态都共享、同步、复制或能通过明确的状态分片规则访问。否则节点选择仍必须考虑其局部状态内容。

只有当节点拥有强烈不同的独立参数或状态，而负载控制又频繁压过语义分数时，节点级专门化才会明显被打散。因此应同时声明每个层级是“语义专家”“有状态分片”“无状态容量副本”“always-on backbone”还是混合角色。

#### 4.3 batch、chunk 或并发请求引起的变化

若同一序列的路由取决于：

- 同一 batch 中还有哪些序列；
- 当前 chunk 的长度或切分方式；
- 同一设备正在服务哪些其他请求；
- 跨请求共享的实时硬件负载；

则相同序列可能因执行方式不同而改变模型输出。这不仅是训练稳定问题，还会破坏 batch invariance、chunk composition 和 `prefill = decode` 语义。

Tide 应禁止第三类变化进入模型语义。这是硬约束，而不是一种训练偏好：

> 对固定参数、固定单序列输入和固定单序列左边界状态，逐 token `decode`、任意合法 chunk 切分的 `prefill`、不同 batch 组合以及不同物理调度必须产生相同的语义 artifact。

全局硬件负载只能影响节点放置、kernel 合并、执行先后、通信批次和物理并行方式，不能改变语义路由结果。若负载历史影响语义选择，它必须是单序列状态或正式声明且在一次语义执行中固定的模型参数。CPU 可以批量计算多个序列的 selector，但必须为每个序列维护彼此独立的控制状态。

### 5. Tide 特有的训练风险

#### 5.1 selected-only feedback

hard Top-K 的离散索引通常不直接求导。任务梯度主要经过被选中的节点和被选中 gate weight；未被选择的节点无法告诉 router：“选择我是否会更好”。

在标准 MoE 中，这已经会造成未选专家缺少任务反馈。在多平面 Tide 中，一个早期阶段的选择还会改变后续多个层级的输入，未选路径的反事实质量更难获得。

#### 5.2 路径级分布漂移

第 $p$ 个平面的路由变化会改变第 $p+1$ 个平面的输入分布；第 $p+1$ 个平面的 router 和节点参数随之变化，又会继续改变更深平面。若有 96 个平面，这种变化可以沿整条路径放大。

#### 5.3 长路径信用分配

若只在最终输出处计算损失，早期平面 selector 收到的学习信号要经过许多 hard choice、节点状态和局部 kernel。即使数值梯度仍能传播，信号也可能很弱且方差很大。

路径级分布漂移与长路径信用分配相互放大，但不是同一个问题：

| 问题 | 发生范围 | 即使另一问题不存在是否仍可发生 |
| --- | --- | --- |
| 路径级分布漂移 | 不同训练 checkpoint 或不同历史状态之间，下游输入分布不断变化 | 可以。一个很浅的 router 也可能频繁换路 |
| 长路径信用分配 | 一次固定前向/反向内部，最终损失必须穿过很长路径给早期计算分配信用 | 可以。完全固定的深网络也有长程梯度问题 |

层级化 backbone、短残差和周期性收拢可以同时缓解二者：公共路径缩短梯度距离，收拢点限制一次稀疏选择持续影响后续分布的长度。

#### 5.4 与本节点激活无关的状态更新

当前设想已经避开最强的条件状态副作用：

1. 上游已激活节点向全部邻接后继发送消息。
2. 后继节点只要收到消息，就更新自己的长期状态。
3. 本节点是否激活只决定是否执行昂贵计算和继续向下游发送。

因此，本节点的状态更新不依赖本节点当前是否被 selector 激活。但它仍然不是“与所有路由无关”：上游哪些节点被激活，仍决定本节点会收到哪些消息。剩余风险是路由改变节点的入站消息分布，而不是本节点 selector 直接决定状态是否更新。

还必须定义节点在某个逻辑时刻没有收到消息时，状态是保持不变、执行 decay、推进空步，还是进行其他确定转移。该规则会直接进入 `prefill = decode` 语义。

#### 5.5 激活饥饿、梯度饥饿与语义饥饿

激进的历史负载均衡，例如优先激活从未被激活的节点，可以消除“激活次数长期为零”，但不能自动消除以下问题：

| 类型 | 含义 | 激进负载均衡是否自动解决 |
| --- | --- | --- |
| 激活饥饿 | 节点很少被选中执行昂贵 kernel | 基本可以 |
| 梯度饥饿 | 节点虽然被选中，但输出权重很小、路径未影响损失或梯度被截断 | 不一定 |
| 语义饥饿 | 节点收到的样本不断变化，缺少重复、连贯的输入分布，无法形成有用计算 | 不能，甚至可能加重 |
| 优化器状态陈旧 | 参数长时间无有效梯度，动量和尺度统计失配 | 只能部分缓解 |

如果专门化预期发生在格子级，较安全的方案是：先按语义选择格子，再在格子内对真正可交换的节点做激进负载分配。这里的“可交换”至少要求相关参数和被读取状态等价。若格子内节点持有不同 KV/SSM 历史，即使参数共享，也不能只按“最少使用优先”任意选择。

#### 5.6 层级发散与收拢

标准 MoE 的稀疏分支通常在一个 block 内立即求和并返回共同 residual stream，因此一次路由决定的生命周期很短。Tide 若让分支连续穿过许多平面而长期不收拢，路径分布漂移和信用分配都会更强。

建议把层级化 backbone 设计为反复出现的有限生命周期结构：

~~~text
高激活率主干
    -> 小倍率一级分支
        -> 可选的更稀疏二级分支
        -> 一级收拢点
    -> 主干收拢点
    -> 下一段
~~~

每次只做有界倍率发散，例如逐级从 1 扩展到 4、再到 16 或 32，而不是一次从 1 扩展到 512；同时显式给出分支最大寿命、每个父区域的激活预算和收拢位置。仅限制单级 fan-out 仍不足够：若分支持续不收拢，可能路径数仍随层数快速增长。

### 6. 建议的 selector 分解

建议明确分离神经状态、语义评分、负载控制和 selector 策略接口。

#### 6.1 神经状态

记节点 $i$ 在 token 位置 $t$ 的神经状态为 $q_{i,t}$。它属于模型语义，可以参与连续可微的状态更新和节点计算。候选状态至少包括：

| 状态类型 | 典型内容 | 大小随历史增长 |
| --- | --- | --- |
| Attention memory | 本节点收到的消息对应的 K/V 记录、位置与 causal metadata | 通常增长，或受窗口/压缩策略限制 |
| SSM hidden state | Mamba/SSM 的固定维度递推张量 | 固定 |
| Linear-attention accumulator | 例如累计的 $\sum \phi(k)v^\top$ 与归一化统计 | 固定或低阶增长 |
| 有限窗口状态 | convolution buffer、最近消息环形缓冲、局部 delay line | 有界 |
| 可学习局部记忆 | 固定数量 memory slots、fast-weight 或其他局部存储 | 由设计决定 |

模型参数不属于这里的单序列神经状态；selector 的历史激活计数也应另列为控制负载状态。

#### 6.2 语义分数

由可学习函数计算内容与节点的匹配程度：

$$
s_{i,t}=g_{\theta}(h_{i,t},q_{i,t}).
$$

这里 $h_{i,t}$ 表示节点收到的当前输入摘要。语义分数最好在加速卡上批量计算，以保留正常的自动微分路径。

语义分数必须在 `ActiveCompute` 之前可得，否则会形成“必须先执行昂贵 Attention/FFN，才能决定是否执行它”的循环。它可以读取入站消息、更新后的轻量状态、低秩 probe 或上一时刻摘要，但第一版不应依赖本次尚未执行的完整 Attention/FFN 输出。

#### 6.3 控制负载状态

CPU 维护小型负载状态：

$$
c_{i,t+1}
=
\beta c_{i,t}
+
(1-\beta)\mathbf 1[i\in A_t].
$$

$c_{i,t}$ 只记录历史选择统计，不承载神经表示。建议对其停止梯度、限制数值范围并使用慢更新。

#### 6.4 Selector 策略接口

实现架构不应把 selector 固定为一种 hard Top-K。一个 selector 至少应显式声明：

1. 读取哪个层级的语义分数、控制状态和静态拓扑约束。
2. 输出 hard mask、soft weight、稀疏连续 weight，还是多者组合。
3. 如何更新下一时刻的控制状态。
4. hard 决策在反向中使用停止梯度、straight-through estimator、soft surrogate，还是额外蒸馏目标。
5. 输出哪些可重放 artifact，例如候选集、分数、负载偏置、激活集和权重。

可比较的策略包括固定/hash、纯语义 Top-K、纯 quota、联合打分、softmax、sparsemax/entmax、训练软推理硬、以及多层级混合策略。

#### 6.5 语义优先、负载优先与层级混合

原备忘给出的语义优先方案是：

先由语义分数产生较大的候选集合：

$$
C_t=\operatorname{TopM}(s_t).
$$

再只在语义候选内部做负载仲裁：

$$
A_t=
\operatorname{TopK}_{i\in C_t}
\left[
s_{i,t}-\lambda(c_{i,t}-\bar c_t)
\right],
\qquad K<M.
$$

其中 $\bar c_t$ 是当前候选区域的目标或平均负载。负载项只应在多个语义上可接受的节点之间调整，不应把一个 token 强行送给语义分数很低的节点。

不同顺序的权衡如下。

| 方案 | 形式 | 优点 | 风险 |
| --- | --- | --- | --- |
| 语义优先 | 先取语义 Top-M，再在其中均衡 | 保护任务质量和专门化 | 热门节点可能反复进入候选，负载自由度有限 |
| 负载优先 | 先取低负载候选，再按语义选择 | 最强地消除激活饥饿和设备偏斜 | 可能强迫语义不合适节点处理输入，增加漂移 |
| 联合打分 | 对 $s_{i,t}-\lambda c_{i,t}$ 直接 Top-K | 实现简单，平滑调节权衡 | $\lambda$ 难选；负载可能压过语义 |
| 容量约束 | 先排除超 quota 节点，再按语义选择 | 语义清晰、容量有硬上界 | 容量不足时需要确定 fallback |
| 层级混合 | 上层语义选择区域，下层在区域内负载分配 | 允许格子级专门化与节点级均衡并存 | 需要明确各层参数是否共享及各层状态归属 |

当前最值得优先实验的是层级混合：

~~~text
语义分数选择格子或高层分支
    -> 格子内 allocator 在少量节点间做负载分配
    -> 若叶节点是容量副本，则共享主体参数
    -> 若叶节点是独立专家，则保留较弱的节点语义分数
~~~

这样可以把“专门化发生在哪里”和“负载均衡发生在哪里”分开，而不是让一个 selector 同时解决两个相互冲突的目标。

格子级专门化可进一步采用两种状态组织：

| 组织方式 | 叶节点角色 | 负载均衡自由度 |
| --- | --- | --- |
| 格子共享语义状态 | KV/SSM/记忆属于格子，叶节点主要执行无状态或可复制 kernel | 较高，叶节点更接近容量副本 |
| 叶节点独立语义状态 | 每个叶节点持有自己的 KV/SSM/记忆 | 较低，selector 必须同时考虑状态相关性与负载 |

若首要目标是验证层级 routing 和训练稳定性，格子共享状态、节点执行 shard/replica kernel 是更容易的第一版。叶节点独立状态表达力更强，但会把节点重新变成有状态专家。

#### 6.6 负载偏置不进入专家输出权重

节点输出可写成：

$$
y_t
=
B(h_t)
+
\sum_{i\in A_t}
\operatorname{softmax}_{A_t}(s_{i,t})
\Delta_i(h_{i,t},q_{i,t}).
$$

$B$ 是 always-on backbone，$\Delta_i$ 是被选择节点的稀疏残差。负载修正只决定 Top-K 成员，不进入 softmax 权重。这借鉴了 DeepSeek 的 loss-free balancing：硬件均衡信号不直接扭曲专家输出幅度。

### 7. 节点内部建议拆分

每个节点建议至少区分三个逻辑步骤。

#### 7.1 `Observe / Update / Score`

所有收到上游消息的候选节点都执行廉价步骤：

- 聚合或读取当前入站消息。
- 更新有界、稳定的节点神经状态。
- 计算供 selector 使用的紧凑语义分数或摘要。

该步骤应能对一个 chunk 内的多个 token 做批量、scan 或 CPU 顺序处理，但不依赖本节点当前 token 的 hard activation 结果。

#### 7.2 `Select`

CPU 按 token 逻辑顺序更新负载状态并产生紧凑 route list。它只处理候选标识符、少量分数和计数，不读取完整 hidden tensor。

#### 7.3 `ActiveCompute / Emit`

加速卡根据 route list 对选中节点执行 packed Attention、FFN、SSM 或其他昂贵 kernel，并产生向下一平面的传播消息。

这种拆分的关键收益是：hard selector 主要控制昂贵残差和传播，而不是直接控制节点是否进行任何状态更新。收到消息并更新状态不等于一定获得有效任务梯度；只有该状态在当前或未来被读出并影响损失，梯度才会到达相应更新。

### 8. 稳定化原则

#### 8.1 层级化 always-on backbone

always-on backbone 不应只理解为“每个平面一个 shared expert”。它可以形成多个嵌套层级：

- 少量最短、最高激活率的核心路径。
- 从核心路径生长出的一级残差分支。
- 从一级分支继续生长出的更稀疏、更专门的二级分支。
- 各级分支在预定位置重新汇入本级或上一级 backbone。
- 类似 LH hub 的高层节点可以常态激活，并为低层稀疏节点提供信息与梯度通路。

每个层级应配置：

| 配置 | 含义 |
| --- | --- |
| 激活策略 | always-on、soft、hard、quota 或混合 |
| fan-out 上界 | 一个父区域最多扩展多少子区域或节点 |
| 分支寿命 | 分支最多跨越多少计算阶段后必须收拢 |
| merge 规则 | residual add、加权和、拼接投影、SSM 更新或其他明确算子 |
| 参数关系 | 共享、共享主体加 adapter、完全独立 |
| 状态归属 | 状态属于叶节点、格子、hub 还是 backbone |

一个不会被 selector 切断的基础路径可以是：

- 恒等或线性残差；
- 共享 SSM；
- 公共基础块；
- shared expert；
- 共享主干加 node-specific adapter。

shared expert 不是已被所有模型证明最优的固定答案。这里保留 always-on 路径的主要目的，是防止路由变化同时切断信息流和训练梯度，而不是预先规定知识必须存入某个共享专家。

##### 8.1.1 前向跨平面 shortcut 与不等长路径

若一条跨平面边始终从较早阶段指向较晚阶段，它仍属于空间 DAG，不会因为“跨越多个平面”自动破坏 `prefill`。固定非负整数时延可以：

- 直接写入消息的逻辑到达时间；
- 或展开成若干只做延迟的中间节点。

真正需要定义的是：不同长度路径在何种逻辑时刻汇聚、节点按什么顺序更新状态、哪些消息对当前读出可见。只要这些规则固定、因果且节点窗口转导器满足时间分块组合律，不等长前向路径本身是可处理的。

工程上，等长路径加 residual 更容易做规则张量计算；带时间桶的不等长路径表达力更强，但需要 ragged inbox、watermark 和更复杂的 packed kernel。两者应作为可对比方案，而不是预先断言只有等长路径正确。

##### 8.1.2 反馈回路的边界

[[tide-background-history-and-references#第二部分：人脑信号传播调查|人脑信号传播调查]] 强调，真实脑网络包含并行分支、跨区 shortcut、丘脑中继和大量前馈/反馈闭环。这为 Tide 的多尺度 backbone、hub、旁路和选择性增益提供设计联想，但不构成数字模型应直接复制脑连接的证据。

对 Tide：

- 同 token、同内部时刻的反向边会重新引入空间环和 zero-delay 求解问题，暂不进入高性能主线。
- 带正时延、从 token $t$ 的高层状态影响 token $t+1$ 或更晚低层状态的反馈，可以在有限 chunk 上展开成 event DAG，但会引入时间递推，需要单独证明是否 scan-composable。
- 若只需要“先高层处理，再回到低层细化”的效果，可以在更晚平面复制一个低层类型节点，用前向 DAG 表达 refinement，而不必首先引入真实空间环。

因此，第一版可保留接口上的反馈能力，但 reference 配置优先采用前向 shortcut、延迟状态和后置 refinement。

##### 8.1.3 快路径、慢路径与固定读出周期

Tide 的自回归接口仍需要在固定外部周期提取或输出 token。不同内部路径具有不同时延时，必须从以下两种语义中明确选择：

| 语义 | 当前 token 的读出 | 慢分支的作用 |
| --- | --- | --- |
| deadline merge | 当前 token 必须等待所有被声明为可见的活跃分支在读出截止点前汇入 | 直接影响当前输出；物理关键路径受最慢活跃分支约束 |
| late-context update | 当前 token 由快 backbone 在固定截止点读出 | 未赶上截止点的慢分支只能更新未来 token 可见的状态，不能追溯修改当前输出 |

第一种更接近 conditional depth；第二种更接近“快速反射/初步输出 + 较慢上下文更新”。两者都可以定义成因果模型，但训练目标、事件 DAG、边界状态和 `prefill` 调度不同，不能混为一个模糊的“快慢路径”概念。

若希望保持固定 decode 周期且避免每个 token 等待最深路径，late-context update 更自然；代价是复杂分支学习的是未来上下文贡献，而不是对当前 token 的迟到修正。

late-context update 也不自动得到高性能 `prefill`。若慢分支只通过可结合 scan、固定 SSM 更新或其他可组合状态影响未来，它仍可能批量执行；若慢分支不可预测地改变下一个 token 的 hard routing，则会重新形成跨 token 控制链。

##### 8.1.4 小词表与减少平面数

“用 byte 级词表让简单词主要由 backbone 学会，复杂长句扩散到更深分支”是有价值的研究假设，但当前没有理论保证。

byte tokenization 的收益包括更小 embedding/output vocabulary、无 OOV 和更细粒度组合；代价是序列显著变长，selector 递推次数、状态更新次数以及 Attention/SSM 的时间维度成本都会增加。简单词也需要多个 byte token 才能完成，因此“简单内容必然走短路径”需要由训练目标、路由代价或辅助监督主动促成。

可比较的方案至少包括：

1. 纯 byte token。
2. 常规 BPE/SentencePiece token。
3. byte 输入后先做局部 patch/compression，再进入层级 backbone。
4. 固定平面数但允许 conditional depth。
5. 减少平面数、提高每平面节点容量或状态表达力。

平面数不应直接类比 GPT block 数。若层级 backbone、局部状态和分支计算已经提供足够有效深度，减少平面数完全可能；但应由 scaling experiment 决定。

#### 8.2 长期状态采用与本节点激活无关的更新

原文的 `route-independent update` 容易误解。更准确的目标是：给定本节点已经收到的消息，其状态更新不再取决于本节点当前是否被激活。

记 $I_{i,t}$ 为节点 $i$ 在逻辑位置 $t$ 收到的消息集合，优先采用：

$$
q_{i,t+1}=U_i(q_{i,t},I_{i,t}),
$$

随后独立计算激活决定 $a_{i,t}$，并令：

$$
\operatorname{emit}_{i,t}
=
\begin{cases}
\operatorname{F}_i(q_{i,t+1},I_{i,t}), & a_{i,t}=1,\\
\varnothing, & a_{i,t}=0.
\end{cases}
$$

这正是当前设想：“收到即更新，激活才发送”。上游路由仍会改变 $I_{i,t}$，所以状态整体仍然是 path-dependent。

对不同状态，更新与激活计算可以进一步拆分：

| 状态 | 收到消息时执行 | 节点激活时执行 |
| --- | --- | --- |
| KV cache | 对消息做 K/V projection，附加逻辑位置并写入本节点 ragged cache | 计算 Q，读取本节点历史 K/V，执行 packed causal attention、输出投影和可选 FFN |
| SSM | 对收到消息执行输入投影和状态递推；若无消息则按定义保持或 decay | 从更新后的状态产生较昂贵输出、门控、FFN 和发送消息 |
| Linear attention | 更新固定维度 accumulator | 用 query 读取 accumulator 并产生输出 |

“收到即更新”把一部分成本从激活计算转移到了状态维护，并不等于免费。若每条收到消息都追加 K/V，则全图 cache 增长量近似为：

$$
N_{\mathrm{KV}}
\propto
\sum_{i,t}|I_{i,t}|.
$$

当每个已激活上游节点向 $d$ 个邻接后继发送时，单步新增记录量约与“激活发送数乘以 $d$”同阶。它仍受稀疏激活和有界度控制，但可能在长序列、多平面下成为主要内存成本。固定大小的 SSM 或 linear-attention state 在这一维度更容易控制。

对于 Attention，节点在一个 chunk 内收到的消息数一般不同，因此需要按 `(batch, node, logical time)` 整理 ragged KV。可先把所有 K/V projection 合并为大矩阵计算，再按节点写入 packed offset；被激活 query 再调用支持可变长度的 packed attention。

同一逻辑位置可能收到来自多个上游节点的多条消息。Attention 可以把它们作为带 source、logical time 和 message id 的多条 K/V 记录；SSM 等顺序敏感更新则必须规定先聚合、按固定来源次序更新，或使用可交换/可结合的联合更新。物理到达顺序不能决定语义结果。

训练时还需要区分：

- 当前训练 chunk 内 K/V 的正常反向图。
- 跨 chunk boundary state 是保留完整梯度、重计算，还是按 truncated BPTT detach。
- 一个节点虽然写入 K/V，但若在反向截断前从未被激活读取，这次写入可能没有任务梯度。
- 节点状态不能跨 optimizer step 直接复用旧权重生成的神经 activation，除非定义专门的 replay/recompute 语义。

若昂贵节点计算还要写长期状态，应先限制为有界、小幅、带衰减的状态增量，并单独验证其稳定性。

#### 8.3 从 dense / soft 逐步退火到 hard sparse

不建议让随机初始化的 router 和节点直接进入高度稀疏 Top-K。可按以下方向逐步推进：

1. 先训练 always-on backbone。
2. 加入共享初始化的节点 adapter，初期全部或大比例激活。
3. 使用 soft gate、大 $K$ 或大 fan-out，让多个候选获得反馈。
4. 逐渐减小 $K$ 和 fan-out，增加 hard routing 比例。
5. 最后再加入历史负载状态和较强的时间均衡。

这与 EvoMoE 的 dense-to-sparse 思路一致，但 Tide 还需要同时控制多平面路径和节点状态。

#### 8.4 降低 checkpoint 路由漂移

可选择或组合：

- router 使用小于节点 kernel 的学习率。
- 用 EMA teacher 或蒸馏 router 提供较稳定的选择目标。
- 训练后段冻结 router，或至少冻结负载偏置更新。
- 对 Top-K 边界加入 margin，减少接近并列时的频繁翻转。
- 使用 hysteresis：旧路径只在新路径明显更优时才切换。
- 初期使用 $K>1$，避免 Top-1 单次切换造成全部计算替换。

hysteresis 和 margin 都会减少探索，不能从训练开始就过强；应结合 route churn 和验证质量调整。

#### 8.5 给未选择节点提供受控反馈

候选方法包括：

- 训练期使用比推理期稍大的 $K$。
- 以较小概率计算一个未选择的 shadow route，但不改变主前向输出。
- 对节点加入局部预测或 representation distillation loss。
- 在训练早期保留最低探索配额。
- 由 dense teacher 或较软 router 给出候选质量监督。

这些方法增加训练计算量，但直接缓解“router 不知道未选路径是否更好”的 selected-only feedback。

#### 8.6 缩短长路径信用分配

可在少量中间平面加入训练期辅助读出或 teacher representation matching。辅助损失应在训练后期衰减，避免强行要求每个平面都形成完整语言模型表示。

#### 8.7 利用空间邻接进行平滑初始化

相邻节点可以共享基础参数，只保留小型局部 adapter；也可以在训练早期对相邻 adapter 使用较弱的参数或输出平滑约束。这样路由在邻近节点间切换时，输出不会发生完全无关的跳变。

该方法可能有用，也可能抑制真正的专门化。比任意相邻节点 Laplacian 平滑更可控的第一选择是：同一语义格子内部共享主体参数，叶节点只保留小 adapter；跨格子不默认平滑。平滑约束应做消融，并在后期减弱或移除。

#### 8.8 数值稳定性独立处理

- router score 和负载统计优先使用 FP32。
- 对 softmax router 考虑 router z-loss 或显式 logit 范数约束。
- Attention 使用 QK-Norm、QK-Clip 或其他明确控制 logit 范围的方法。
- SSM 状态使用稳定参数化、有界 gate、衰减和状态范数监控。
- 使用梯度裁剪，并分别记录 router、节点 kernel、状态更新和 embedding 的梯度尺度。

不能因为 route 指标稳定，就停止检查 attention、状态和低精度数值。

### 9. CPU 与加速卡的建议执行边界

在只有相邻平面边的最低复杂度模型中，合理的单平面执行流程是：

```text
前一平面完成当前 chunk
    -> 加速卡批量执行 Observe / Update / Score
    -> 一次传输紧凑候选分数和标识符到 CPU
    -> CPU 按 token 顺序扫描 selector 状态并生成 route list
    -> 一次传输 route list 到加速卡
    -> 加速卡按节点/格子打包 ActiveCompute / Emit
    -> 进入下一平面
```

必须避免：

```text
每个 token
    -> 加速卡等待 CPU
    -> CPU 选择
    -> 加速卡执行
    -> 再处理下一个 token
```

后者会把 host/device 同步延迟放入长度为 $L$ 的关键路径。

若加入只向前的跨平面 shortcut，调度单位应从“相邻平面”推广为“拓扑阶段”：

1. 一个阶段等待其所有拓扑前驱产生当前窗口所需的消息桶。
2. scheduler 按目标节点和逻辑到达时间合并相邻边与 shortcut 消息。
3. 加速卡执行本阶段的批量状态更新与评分。
4. CPU 完成本阶段各层级 selector 的顺序控制。
5. 加速卡执行激活计算并把消息投递到后续一个或多个阶段。

只要所有边严格向前，仍可按拓扑序处理。不同固定时延需要额外时间桶，但不要求退化为每 token 一次 host/device 同步。真正的反馈边则不能直接套用这一单次拓扑流程。

即使 selector 每个事件只处理少量标量，总事件数仍约为：

$$
O(PBL),
$$

其中 $P$ 是平面数，$B$ 是 batch size，$L$ 是 chunk 长度。随着节点计算越来越稀疏，CPU selector 反而可能成为 Amdahl 瓶颈。因此需要：

- 候选度数保持常数且较小。
- 每个平面批量扫描多个 batch 和 token。
- 使用紧凑连续内存和预分配 route buffer。
- CPU 选择与其他平面的加速卡计算双缓冲或流水重叠。
- 对 selector 单独测量每秒决策数，而不是只看其数据体积。

### 10. 建议的训练推进顺序

#### 阶段 A：固定均衡路由

使用静态 hash、固定局部路径或预生成均衡路由，不训练 selector。

目标是验证：点阵拓扑、节点 kernel、状态更新和稀疏梯度覆盖本身能否训练。若这一阶段失败，问题不应归因于学习式 router。

#### 阶段 B：token-local learned routing

加入只依赖当前节点输入和神经状态的可学习语义分数，不加入历史负载递推。

目标是隔离 learned routing 和 selected-only feedback 的影响。

#### 阶段 C：慢速负载偏置

加入停止梯度、慢更新、幅度受限的负载修正；先在 optimizer step 或固定大窗口之间更新，并在一次 forward 内冻结。

目标是验证负载均衡收益和语义专门化损失之间的权衡。

#### 阶段 D：单序列严格时间递推 selector

最后加入逐 token 更新的 selector 历史状态，并证明、测试其 chunk composition 和 `prefill = decode` artifact equality。

目标是判断精细时间均衡是否带来超过额外串行控制、路由变化和训练困难的收益。

不建议直接从阶段 D 开始训练完整 96 平面模型。否则一旦训练不稳定，很难区分根因。

### 11. 必须记录的训练指标

#### 11.1 路由一致性

- 固定验证前缀在不同 checkpoint 的 Top-K Jaccard overlap。
- 每个 token 最后一次改变目标节点发生在训练的什么位置。
- 第 $K$ 与第 $K+1$ 个候选之间的 score margin。
- 邻近 checkpoint 的路径编辑距离。
- 不同平面的 route saturation 速度。

#### 11.2 负载与死亡节点

- 每平面、每格子和每节点的激活次数。
- load coefficient of variation、Gini coefficient 和最大/平均负载比。
- 连续多个窗口未被激活的 dead node 比例。
- 节点收到状态更新但未执行昂贵 kernel 的比例。

#### 11.3 梯度与输入分布

- 每节点获得非零任务梯度的频率。
- router、Observe/Update、ActiveCompute 的梯度范数。
- 每节点输入均值、方差、范数和主成分随训练的漂移。
- route change 与节点输入分布突变的相关性。

#### 11.4 数值与状态稳定性

- attention 最大 logit。
- SSM 或其他持久状态的范数、谱或衰减统计。
- NaN、Inf、梯度裁剪触发率和低精度溢出。
- loss spike 与 route churn、load imbalance、attention logit、状态范数之间的时间相关性。

#### 11.5 语义不变量

- 同一序列在不同 batch 同伴下路由和输出相同。
- 同一序列采用不同 chunk 切分时，节点状态、route list、消息和输出 artifact 相同。
- `prefill` 与逐 token `decode` 的节点级状态、选择和输出一致。
- 训练和推理使用相同 selector 语义；训练期额外 shadow route 不进入 reference output。

### 12. 当前最重要的设计结论

当前最值得优先固定的不是某一种具体负载算法，而是以下边界：

1. 语义分数、神经状态和负载控制状态是不同对象。
2. CPU allocator 只对紧凑候选做顺序仲裁，不承担大张量神经计算。
3. 负载历史只在语义候选内部做小幅调整，不能取代内容路由。
4. hard selector 主要控制昂贵残差和发送激活，不能轻易切断全部状态更新、信息路径和梯度路径。
5. 模型语义中的状态必须按序列隔离；跨请求硬件负载不能改变模型结果。
6. 完整模型应从固定路由、token-local router、慢负载偏置逐级推进到 stateful selector。
7. 专家或节点专门化应作为可测量的统计现象，而不是预先假设的领域模块划分。
8. 路由稳定性与数值稳定性必须独立监控。

### 13. 待继续讨论的问题

1. `Observe / Update` 是否对所有局部候选执行，还是只对收到实际消息的节点执行？
2. 未激活节点的神经状态应该如何更新，才能兼顾训练覆盖、计算稀疏和长期状态语义？
3. 每个平面的 always-on backbone 应是统一共享块、每格子共享块、SSM，还是只保留轻量残差？
4. 历史负载状态应在序列边界重置，还是作为可延续的单序列 boundary state？
5. 负载修正只作为 Top-K tie-breaker，还是允许在更大的语义候选集合内重新排序？
6. 是否需要训练期 shadow route，以及允许多少额外计算预算？
7. 中间平面辅助损失如何设计，才不会把所有节点强制训练成相同表示？
8. 节点和格子到 16 张 Ascend 卡的静态映射，是否足以吸收剩余负载波动，减少 selector 对模型语义的干预？
9. selector 的逐 token CPU scan 在多大 $B$、$L$ 和 $P$ 下开始成为关键路径？

### 14. 主要参考

- 本地背景报告：[[tide-background-history-and-references#第二部分：人脑信号传播调查|人脑信号传播调查]]
- StableMoE: [Stable Routing Strategy for Mixture of Experts](https://arxiv.org/abs/2204.08396)
- EvoMoE: [An Evolutional Mixture-of-Experts Training Framework via Dense-To-Sparse Gate](https://arxiv.org/abs/2112.14397)
- ST-MoE: [Designing Stable and Transferable Sparse Expert Models](https://arxiv.org/abs/2202.08906)
- DeepSeekMoE: [Towards Ultimate Expert Specialization in Mixture-of-Experts Language Models](https://arxiv.org/abs/2401.06066)
- DeepSeek-V3: [Technical Report](https://arxiv.org/abs/2412.19437)
- Loss-Free Balancing: [Auxiliary-Loss-Free Load Balancing Strategy for Mixture-of-Experts](https://arxiv.org/abs/2408.15664)
- OLMoE: [Open Mixture-of-Experts Language Models](https://arxiv.org/abs/2409.02060)
- Qwen3: [Technical Report](https://arxiv.org/abs/2505.09388)
- Kimi K2: [Open Agentic Intelligence](https://arxiv.org/abs/2507.20534)
- GLM-4.5: [Agentic, Reasoning, and Coding Foundation Models](https://arxiv.org/abs/2508.06471)
- Graph of Tokens: [Improving Routing in Sparse Mixture of Experts with Graph of Tokens](https://arxiv.org/abs/2505.00792)
- STAR: [Rethinking MoE Routing as Structure-Aware Subspace Learning](https://arxiv.org/abs/2606.08814)
- MCF-MoE: [Multi-level Context Modeling for Consistent Expert Selection in Mixture-of-Experts](https://arxiv.org/abs/2607.16427)
- Less is MoE: [Trimming Experts in Domain-Specialist Language Models](https://arxiv.org/abs/2606.05538)

---

## 第三部分：执行能力与成本模型

### 9. Tide 的进一步设计目标

前面的讨论可以收敛为一个比“让一般 Graph 支持 prefill”更严格的目标：

> 给定有限 chunk，先生成语义完整的 reference event DAG；再把其中满足特定代数或依赖性质的区域，替换为经过等价性证明的并行 chunk operator，使最终 execution DAG 同时保持局部通信、超稀疏、correctness 和较低 span。

这里不要求整个 Graph 都能 scan。不同 node 或 subgraph 可以依靠不同理由获得并行性；无法并行化的区域仍可顺序执行，但必须显式暴露其 span 成本。

#### 9.1 Reference event DAG

给定全局起始位置 $B\in\mathbb N$、长度 $L\in\mathbb N_{>0}$、左边界延续状态 $C_B$，以及输入 chunk：

$$
X_{B:B+L}=(x_B,x_{B+1},\ldots,x_{B+L-1}),
$$

reference decode semantics 写成：

$$
(y_t,C_{t+1})=\operatorname{Step}(x_t,C_t),
\qquad B\leq t<B+L.
$$

把这段有限执行展开为 reference event DAG：

$$
\mathcal D_{\mathrm{ref}}(B,L,C_B)
=
(E_{\mathrm{ref}},\mathcal A_{\mathrm{ref}}).
$$

其中 $E_{\mathrm{ref}}$ 是实际发生的逻辑事件实例集合，$\mathcal A_{\mathrm{ref}}$ 是直接数据、状态或控制依赖边集合。沿用主文档的对象分层，一个事件实例由事件头与事件值组成；事件头可写为：

$$
h_e=(\eta_e,\kappa_e,\ell_e,\theta_e,\Omega_e,c_e).
$$

这里：

- $\eta_e$ 是事件实例标识符。
- $\kappa_e$ 是事件种类。
- $\ell_e$ 是外部位置、空间节点或已声明子图位置。
- $\theta_e$ 是由语义 profile 定义的逻辑时间戳。
- $\Omega_e$ 是事件直接处理或标识的归属支持集。
- $c_e$ 是输入前缀依赖上界。
- 事件值 $\nu(e)$ 另行记录数值产物、状态提交、路由和消息。
- 状态版本不是事件位置或事件身份的一部分；事件若读取或写入某个状态版本，相应状态依赖必须进入 $\mathcal A_{\mathrm{ref}}$。

因此，$\mathcal A_{\mathrm{ref}}$ 必须包含 data、state、control、visibility 与 commit dependencies。Graph schema 本身可以有环，只要对任意有限 $B,L$、合法 $C_B$ 和有限 internal rounds，实际执行可以展开成有限、dependency-complete 的 event DAG。所有 feedback edge 必须严格推进语义 profile 声明的逻辑秩，例如 step/round/phase/microstep 或 absolute-round/phase/iteration；消息 `owner` 本身不是默认时间秩。未定义的 zero-delay algebraic loop 不进入这一执行模型。

#### 9.2 Certified contraction 与 execution DAG

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
\mathcal D_{\mathrm{ref}}(B,L,C_B)
\xRightarrow{\text{certified contraction}}
\mathcal D_{\mathrm{exec}}(B,L,C_B).
$$

这一区分很重要。Mamba 的细粒度 reference recurrence 可以是长度为 $L$ 的 chain，但 scan certificate 允许把它替换成对数深度的 scan network。类似地，causal attention 的细粒度依赖很多，但可以由经过证明的 causal bulk kernel 承载。

因此，Tide 真正追求的不是“原始 reference DAG 看起来没有链”，而是：

> reference DAG 能否被划分成具有局部等价证书的 regions，并使收缩后的 execution DAG 具有较低 span。

### 10. 五类 Execution Capability

这些 capability 是 sub-DAG 的 lowering contract，不是没有验证义务的提示标签。

| Capability | 语义条件 | 主要并行方式 | 典型例子 |
| --- | --- | --- | --- |
| `token-local` | token 之间没有 mutable temporal dependency | batch / map | FFN、Norm、projection、token-local router |
| `scan-composable` | transition 有紧凑且封闭的 associative summary | parallel prefix scan | Mamba/SSM、affine recurrence |
| `causal-bulk` | 存在已证明等价的 causal chunk operator | attention/conv 等专用 bulk kernel | causal attention、causal convolution |
| `ready-set-local` | 同一就绪事件集合内没有相互依赖或可见写冲突 | wavefront packing | message-passing round、MoE routing |
| `sequential-fallback` | 尚无可用的并行等价 lowering | exact sequential execution | 当前 LH persistent selector |

#### 10.1 Token-local

若对所有输入位置 $t$：

$$
z_t=f(x_t;\theta),
$$

并且 $f$ 不读取由其他输入位置在本 region 内更新的 mutable state，则所有 $z_t$ 可以并行计算。

`token-local` 描述输入位置之间的依赖性质，不是消息 `owner` 的同义词，也不要求所有输入位置采用同一路径。MoE router 可以根据每个位置的 hidden state 动态选择不同 expert，只要同层各位置的 routing decisions 不通过 mutable selector state 相互影响。

#### 10.2 Scan-composable

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

#### 10.3 Causal-bulk

有些 causal operator 没有适合的有限维 associative summary，但已有高性能 chunk algorithm。若 reference operator 为：

$$
y_t=G_{B,t}(C_B,x_B,\ldots,x_t),
$$

定义 reference decode fold：

$$
\operatorname{DecodeFold}_{B,L}(X_{B:B+L},C_B)
=
((y_B,y_{B+1},\ldots,y_{B+L-1}),C_{B+L}),
$$

其中每个 $(y_t,C_{t+1})$ 都由第 9.1 节定义的
$\operatorname{Step}(x_t,C_t)$ 依次产生。若 chunk kernel $K_{B,L}$ 对所有合法输入满足：

$$
K_{B,L}(X_{B:B+L},C_B)
=\operatorname{DecodeFold}_{B,L}(X_{B:B+L},C_B),
$$

则它可以声明 `causal-bulk`。GPT causal attention 是主要例子；它不需要被强行解释为 Mamba 风格的 scan。

#### 10.4 Ready-set-local

在事件 DAG 中，称事件集合 $F_k$ 为一个就绪集合，当且仅当其中每个事件在该调度点的全部前驱均已完成。若 $F_k$ 中任意两个事件：

- 不读取对方尚未提交的 state。
- 不通过 mutable control state 改变对方的 routing decision。
- 不发生未定义顺序的 conflicting writes。

则该就绪集合可以并行执行并按计算核角色打包，称相应区域满足 `ready-set-local`。

`layer-local` 是 `ready-set-local` 在规则 Transformer chain 中的特殊情况。一般 Tide Graph 未必具有 layer；它可能按图距离、内部轮次，或者 $(t,r)$ 的反对角线形成 wavefront。

这里的 wavefront 只是调度术语：它表示按依赖关系连续推进的一系列就绪集合，不是消息、持久状态或新的 `frontier` 字段。

Phase 与就绪集合也不相同。Phase 定义大范围的 barrier、visibility 与 commit order；就绪集合是在满足这些约束后，由实际事件依赖与当前执行进度共同确定的可调度集合。它不是消息的因果前沿 `frontier`。

#### 10.5 Sequential fallback

任意无法归入前述类别的 reference region，仍可以由 exact interpreter 或 fused sequential kernel 执行。这保证了 Tide 表达能力，但不能把 kernel fusion 误报成 sequence parallelism。

若一个 fallback region 的 span 随 chunk 长度 $L$ 线性增长，并且位于全局 critical path 上，它就可能决定整个模型的 prefill 上限。当前 persistent LH selector 是主要候选。

### 11. Capability Contract

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

### 12. 适合 Tide 的 Graph 约束

一个有希望成为 `prefill-native` 的局部通信、超稀疏 Graph，应优先满足以下设计约束。

#### 12.1 Sparse work

令 $A_{t,r}$ 是 token $t$、round $r$ 的 active event set。总 work 应主要与：

$$
\sum_{t=0}^{L-1}\sum_{r=0}^{R-1}|A_{t,r}|
$$

及实际 active edges 数量相关，而不是与 $L\,R\,|V|$ 相关。运行时不能通过“执行全部 node 再 mask”隐藏地失去超稀疏性，除非它作为明确的小规模 fallback。

#### 12.2 Explicit state ownership

多个 events 对同一 state location 的写入只允许几种可判定形式：

- single-writer / exclusive ownership。
- associative reduction。
- 显式 versioned ordered writes。
- 进入 sequential fallback。

否则，Graph 虽然可以动态执行，但 chunk lowering 无法确定 visibility 与 commit semantics。

#### 12.3 Prefill-capable temporal state

跨输入位置状态应尽量由 `scan-composable` 或 `causal-bulk` 计算核承载。对于只在部分输入位置收到消息并实例化事件的空间节点，可以把该节点的事件压成按逻辑时间排序的稀疏事件序列，再执行 segmented scan 或 packed causal kernel。

如果 state transition 包含时间间隔，计算核需要显式接收输入位置、逻辑轮次或时间间隔 $\Delta t$。例如固定 decay 可以把没有节点事件的区间折叠为 $A^{\Delta t}$，而不是逐输入位置执行空操作。

#### 12.4 Ready-set-local routing

Router 应优先读取当前事件输入和已提交前驱状态。它不应在同一就绪集合内用一个全局可变计数器逐项更新其他输入位置的选择优先级。

可接受的 routing 形式包括：

- token-local top-k。
- 基于上一就绪集合边界快照的 routing。
- scan-composable controller state。
- speculation + validation + replay。

当前 LH selector 可以保留为机制样本和 correctness fallback，但不应默认成为 Tide 高性能 profile 的必要组成。

#### 12.5 Explicit fallback tax

每个 sequential fallback 都要进入 span report。若 runtime 只是把多个逻辑 tick pack 到一个 kernel 内顺序执行，work 和 launch overhead 可能改善，但 logical span 没有被消除。

### 13. Work、Span 与通信的联合目标

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

“局部通信 + 超稀疏”主要降低 $W$ 与 $C$；`token-local / scan-composable / causal-bulk / ready-set-local` 主要降低 $D$。只满足前者还不够：一条极稀疏但跨全部 token 的自适应链，work 很小，却无法获得高吞吐 prefill。

可以据此定义三个运行等级：

| 等级 | 定义 |
| --- | --- |
| `prefill-native` | 所有随 $L$ 增长的主要依赖链都能由 batch、scan、bulk 或 wavefront contraction 处理 |
| `prefill-compatible` | chunk correctness 成立，但仍残留少量随 $L$ 增长的 sequential span |
| `decode-only` | 关键路径基本随 token 数线性增长，chunk 主要只是 fused sequential execution |

### 14. 三类模型如何落入该设计

#### 14.1 GPT-style Transformer

- Norm、projection、FFN 和 residual arithmetic 是 `token-local`。
- causal self-attention 是 `causal-bulk`。
- block chain 仍按深度顺序执行，但它的 token-axis 不需要退回逐 token loop。

因此，模型 span 主要随 block depth 增长，而不是随 `block depth × token count` 增长。

#### 14.2 Mamba/SSM

- input projection、gate 和多数 pointwise operator 是 `token-local`。
- selective recurrent state 是 `scan-composable`。
- local convolution 可以是 `causal-bulk` 或专门的 scan/bulk lowering。

#### 14.3 Dynamic sparse Tide Graph

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
- `Router` 是 token-local 或 ready-set-local。
- inbox aggregation 是 associative reduction，或有显式 ordered semantics。
- node state 不与 routing 构成跨 token 的不可组合串行闭环。

那么每个 round 可以把所有输入位置和已实例化节点事件按 role 与 kernel type 打包。Graph 路径仍然可以是动态的，但 execution span 主要随 internal rounds 与 graph dependency depth 增长，而不是直接退化为 $\Theta(LR)$。

当前 LH selector 的困难正是它同时引入 persistent selector state、active-set-dependent future computation 和 conditional memory side effects。它可以被 Tide 正确表达，却暂时只能声明 `sequential-fallback`，直到找到等价的 composable lowering、可验证 speculation，或者重新定义 selector semantics。

### 15. 推荐的架构分层

Tide 可以据此划分为六层：

1. **Reference semantics**：定义 `Step(input_value, State)`、phase、visibility 和 commit order。
2. **Logical Event IR**：展开有限 chunk 的 token/round/phase/node/state-version dependencies。
3. **Capability registry**：登记 node/subgraph 的 reference operator、chunk lowering 与证明义务。
4. **Region partition and lowering**：识别 token-local、scan、causal-bulk、ready-set-local regions，并生成 execution DAG。
5. **Sparse scheduler and backend**：active event compaction、role-aware packing、CPU/Ascend lowering、barrier 与 state commit。
6. **Verification and cost witness**：验证 output/final-state equality，并报告 work、span、communication、memory 和 fallback critical path。

这个分层不要求 Tide 一开始解决任意动态 Graph。它允许从 GPT/Mamba 已知可行的 chain baseline 出发，逐步加入：

1. 固定稀疏 topology 与 all-active message passing。
2. Token-local dynamic routing。
3. Ready-set-local sparse event execution。
4. Node-local segmented scan 或 causal-bulk state。
5. 最后再研究 persistent/stateful selector、speculation 与 replay。

因此，当前设计目标可以最终概括为：

> “局部通信 + 超稀疏”负责降低 work 和 communication；`token-local / scan-composable / causal-bulk / ready-set-local` 负责降低 span；reference event DAG、capability contract 与局部等价证明负责确保这些优化没有改变 decode semantics。
