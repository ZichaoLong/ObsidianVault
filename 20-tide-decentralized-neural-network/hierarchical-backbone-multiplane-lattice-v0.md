---
type: architecture-candidate
status: draft
tags:
  - tide
  - hierarchical-backbone
  - multiplane-lattice
  - sparse-routing
  - prefill-decode
  - ascend
---

# 层级 Backbone 多平面点阵 v0

> [!summary] 本页定位
> 本页给出一个可以直接讨论、实现和否定的具体 Tide Graph 候选。它不是最终架构，也不是已经证明可训练的模型。它把层级 backbone、pre-norm residual、快慢路径、格子级专门化、节点级负载均衡、收到即更新、激活才发送以及 16 张 Ascend 卡映射，收缩成一个可重复的八平面 superblock。

> [!important] 与其他文档的关系
> 数学上，一般空间 DAG、显式 allocator、不等长路径和窗口拓扑序执行仍以 [[explicit-allocator-general-dag-model]] 为准。训练风险和 MoE 参考见 [[layered-lattice-selector-training-stability-memo]]。本页只实例化一个正向架构，不替代上述文档的数学定义。

## 一页版

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

## 代码导读：从 GPT block 到 HB-Lattice

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

## 1. 固定实例参数

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

## 2. 三个互不等同的坐标

### 2.1 拓扑平面

P0-P7 只表示一个 superblock 内的执行先后。平面不是神经生物学层，也不是语义专门化等级。

### 2.2 层级

Global、Region、Cell、Leaf 表示状态与路由的包含关系。一个 Leaf 慢路径可以跨 P5 和 P6 两个平面；同一 P4 平面同时包含 Cell backbone、Region selector 和 Global/Region carrier。

### 2.3 几何位置

每个 cell 有二维坐标 $(i,j)$，每个 leaf 有 cell 内坐标 $(u,v)$。几何位置决定固定邻接和设备放置，不自动决定语义专门化。

因此，`plane`、`hierarchy level` 和 `spatial coordinate` 必须在代码中使用不同字段。

## 3. 平面不要求同构

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

## 4. Node role 与 kernel kind

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

### 4.1 Merge 不等于任意 Aggregate

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

## 5. 四级 backbone

### 5.1 Global Hub

Global Hub 持有维度较小的全局 carrier $g_s$。v0 可先使用恒等或小型 SSM：

$$
g_s^{\mathrm{base}}=P_s^{G}(g_s).
$$

它不是完整 hidden tensor 的集中副本，而是低带宽全局 context。

### 5.2 Region Hub

四个 Region Hub 分别覆盖一行四个 cell。region 状态记为 $r_{s,q}$，其中 $q\in\{0,1,2,3\}$。

$$
r_{s,q}^{\mathrm{base}}
=
P_{s,q}^{R}(r_{s,q})
+
W_{s,q}^{G\to R}g_s.
$$

### 5.3 Cell Backbone

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

### 5.4 Leaf Site

每个 cell 有 16 个 leaf site。v0 中 leaf 主要承担稀疏 residual compute，不首先让每个 leaf 持有无界独立 KV。

每个 leaf 可持有：

- 有界 observer state；
- node-specific adapter 参数；
- 由所属 cell allocator 维护的激活计数；
- 可选的小型固定维度 SSM state。

昂贵 Attention 若需要长历史，优先读取 cell 共享状态 $Q_{s,c}$。这是为了让格子级专门化与格子内负载均衡可以同时成立。

## 6. 八个平面的逐步语义

### P0：Entry 与层级 context 注入

输入为上一个 superblock 的 $g_s$、$r_{s,q}$、$b_{s,c}$，以及当前 token 在各层级的输入消息和左边界持久状态。

操作：

1. 更新 Global/Region cheap backbone。
2. 将 Global/Region context 投影到 16 个 cell carrier。
3. 得到每个 cell 的 $x_{s,c}$。

输出 P1 Attention 分支输入，以及到 P2 的 identity bypass。

### P1：常亮 PreNorm Attention

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

### P2：Attention residual merge

固定双槽 merge：

$$
u_{s,c}=x_{s,c}+a_{s,c}.
$$

P2 是 Attention branch 的 merge point。

### P3：常亮 PreNorm FFN

$$
f_{s,c}^{\Delta}
=
F_{s,c}
\left(
\operatorname{Norm}(u_{s,c})
\right).
$$

### P4：FFN merge、快路径完成与慢路径 fork

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

### P5：第一级稀疏 leaf

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

### P6：第二级稀疏与局部跨 cell 传播

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

### P7：固定 deadline merge

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

## 7. Branch 声明

### 7.1 Attention branch

| 字段 | 值 |
| --- | --- |
| Parent | Cell backbone |
| Entry | P0 cell carrier |
| Compute | P1 |
| Merge | P2 Add-A |
| 最大寿命 | 2 宏平面 |
| Gate | v0 恒为 1 |
| 输出 | Attention residual delta |

### 7.2 FFN branch

| 字段 | 值 |
| --- | --- |
| Parent | P2 cell carrier |
| Entry | P2 |
| Compute | P3 |
| Merge | P4 Add-F |
| 最大寿命 | 2 宏平面 |
| Gate | v0 恒为 1 |
| 输出 | FFN residual delta |

### 7.3 Sparse spatial branch

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

## 8. 稀疏平面固定邻接

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

## 9. 具体 selector

### 9.1 Region selector

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

### 9.2 Cell leaf allocator

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

### 9.3 控制状态

所有 $\ell$ 都是单序列状态：

$$
\ell_{t+1}
=
\beta\ell_t
+
(1-\beta)\mathbf 1[\text{selected at }t].
$$

不同 batch 中的序列不能共享该状态。物理设备实时负载不得写入语义 selector。

## 10. 节点执行契约

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

## 11. 一个 token 的具体路径示例

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

## 12. 输入扩展与输出收拢

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

## 13. Prefill / decode 执行

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

## 14. 16 张 Ascend 卡映射

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

## 15. 为什么这是一个有用的第一版

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

## 16. 最需要审视的设计选择

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
