---
type: architecture-and-training
status: active-candidate
tags:
  - tide
  - hierarchical-backbone
  - checkpoint-growth
  - recursive-branching
  - sparse-routing
  - training-stability
  - prefill-decode
---

# Tide 模型架构与训练

> [!summary] 本页定位
> 本页统一记录 Tide 的两条战略路线、当前正向模型候选、selector/allocator 能力契约、训练风险和实验顺序。第一部分定义 Graph 收缩线、checkpoint 生长线及其可能但不保证发生的汇合；第二部分定义 HB-Sliced 并用 HB-Line-v0 给出结构 reference；第三、四部分记录训练和执行约束。一般空间 DAG 见 [[tide-mathematical-foundations#第二部分：显式 allocator 的一般空间 DAG|数学基础第二部分]]；函数保持生长与固定 merge 闭包见 [[tide-mathematical-foundations#第五部分：函数保持生长与有限 DAG 节点细化|数学基础第五部分]]；自适应控制下界见 [[adaptive-routing-prefill-lower-bound]]。

> [!important] 语义边界
> `prefill`、`decode`、batch 组合和物理调度不得改变单序列 reference semantics。CPU selector、加速卡 packing、设备放置和通信流水只属于实现；若历史负载进入语义，它必须是逐序列隔离、可延续且可重放的正式状态。

## 第一部分：两条设计路线与递归固定 merge 分支

> [!summary] 本部分定位
> Tide 同时保留一条从一般 Graph 向下收缩的理论/架构路线，以及一条从预训练模型向外生长的实现/实验路线。两条路线互相提供约束和证据，但本文不把它们最终汇合当作前提。递归固定 merge 分支只是当前最值得共同研究的候选交界面。

### 1. 两条路线承担不同职责

#### 1.1 Graph 收缩线

Graph 收缩线从表达力较强的机制集合出发：

```text
一般 Graph / LH mechanism pool
-> 有限、dependency-complete logical event DAG
-> 显式 allocator 的一般空间 DAG
-> HB-Lattice 的几何与层级直觉
-> HB-Sliced / HB-Line / HB-Plane
-> 有界递归、固定 merge 的结构化分支族
```

它的主要产物不是一个必须完整训练的“最大模型”，而是：

1. correctness、因果性和 chunk composition 的边界。
2. work、span、memory 和 communication 的成本约束。
3. 对 selector、状态副作用、反馈边和不等长路径的可接受条件。
4. 仍然保留局部通信与超稀疏目标的结构化候选。

LH 在这条路线中是复杂机制样本、CPU golden reference 和早期动机。若某个 LH 机制阻碍高性能 `prefill` 或训练稳定性，它可以被修改、替代或留在 compatibility family；Graph 收缩线不以复刻 LH 为完成条件。历史 HB-Lattice 承担从一般空间 DAG 到层级局部结构的中间直觉，但旧 v0 混合了空间平面、模型阶段和 runtime lowering；当前正式继承者是 HB-Sliced，而不是恢复旧八平面语义。

#### 1.2 Checkpoint 生长线

Checkpoint 生长线从已有成熟训练、部署事实和高性能 `prefill` 实现的模型出发：

```text
原生预训练 Transformer / Mamba
-> Tide baseline 完全等价装载
-> 函数保持的 residual branch
-> 共享 selector 的平铺兄弟分支
-> 有界递归分支
-> 可选的局部空间化、节点删除和结构变异
```

这条路线在早期追求严格归因：每一步只增加一种结构自由度，并保留一个可直接继续训练的 checkpoint。它的价值是让质量、训练稳定性和性能变化能够与具体设计对应，而不是一次从随机初始化训练一个同时改变拓扑、状态、selector 和 kernel 的大模型。

这条路线不要求永远与原 Transformer 兼容。随着实验积累，后期可以删除冗余节点、合并分支、改变状态表示、替换 kernel 或形成不同拓扑；但从发生非函数保持变异的阶段起，必须把模型称为 checkpoint-derived descendant，而不能继续声称完全 checkpoint-compatible。

#### 1.3 当前优先级不对称

两条路线都有独立价值，但当前执行优先级不同：

- Graph 收缩线继续负责理论边界、结构候选和反例。
- Checkpoint 生长线优先负责第一个真实可训练模型和逐级实验。
- Runtime 同时保留 LH golden path 和预训练模型原生实现两个 oracle；它们是支持设施，不构成第三条模型设计路线。

### 2. 何谓“完整复用 checkpoint”

“完整复用”至少包含三个彼此不同的要求。

| 要求 | 可检查含义 | 后续是否必须一直保持 |
| --- | --- | --- |
| 参数覆盖 | 原 checkpoint 的每个参数张量都映射到新模型的声明位置，没有静默丢弃 | 兼容阶段必须；结构变异后可不保持 |
| transition 等价 | 在指定新增参数和状态初始化下，原模型与扩展模型产生相同输出和下一状态 | 函数保持阶段必须；继续训练后不要求 |
| 新分支初始化复用 | 新分支使用随机参数、旧模块副本、拆分后的旧参数或共享主体加 adapter | 是实验变量，不是“参数覆盖”的同义词 |

设原模型的一步 transition 为

$$
\mathcal T_\theta:X\times\mathcal S\to Y\times\mathcal S,
$$

扩展模型的一步 transition 为

$$
\widehat{\mathcal T}_{\theta,\phi}:
X\times\widehat{\mathcal S}
\to
Y\times\widehat{\mathcal S}.
$$

这里 $\theta$ 是完整装载的旧参数，$\phi$ 是新增参数。还需要一个把旧 cache/state 放入扩展状态的映射

$$
\iota_{\mathcal S}:\mathcal S\to\widehat{\mathcal S}.
$$

函数保持初始点要求存在 $\phi_0$，使得对所有合法 $x\in X$ 和 $s\in\mathcal S$，若

$$
\mathcal T_\theta(x,s)=(y,s'),
$$

则

$$
\widehat{\mathcal T}_{\theta,\phi_0}
(x,\iota_{\mathcal S}(s))
=
(y,\iota_{\mathcal S}(s')).
$$

因此 equality gate 必须比较 logits、KV/SSM state、位置状态和其他边界状态；只比较一个短输入的最终 logits 不足以证明完整复用。

### 3. 四种 checkpoint 谱系阶段

下面的 C0-C3 描述模型与源 checkpoint 的谱系关系；第 8 节的 P0-P6 描述实验逐级增加自由度的顺序。二者不是同一编号系统。

#### 3.1 阶段 C0：原生基线装载

Tide 用自己的模块和 state-dict API 表达一个既有预训练模型，但不增加分支。原生实现与 Tide baseline 必须对齐：

- 参数张量与 tied-weight 关系。
- 单 token decode 与多 token prefill 输出。
- 每层 residual、Attention、FFN artifact。
- KV/SSM state、position/RoPE 输入和 continuation state。
- 训练模式下的 loss 与主要参数梯度。

为比较两条路线，可以把一个 pre-norm decoder-only Transformer 的 block chain 视为单 site、always-on、无空间 selector 的退化切片链；每个宏节点执行一个原 block。这个解释只提供共同的 Graph 记法，不是 C0 的实现要求，也不表示原模型已经采用 HB-Sliced。当前 HB-Line 形式上要求至少两个 site；若后续确实需要该退化 profile，应单独命名，而不是强行把它叫作 Line。

#### 3.2 阶段 C1：函数保持扩展

第一类 growth operator 是零 residual 分支：

$$
\widehat B(x)
=
B_\theta(x)+\alpha\,\Delta_\phi(x),
\qquad
\alpha_{\mathrm{init}}=0.
$$

它在 $\alpha=0$ 的初始点精确保持原函数，适合验证架构装载和 runtime，但必须区分三种训练方式：

1. 若 $\alpha$ 是固定常数 $0$，则损失对全部分支参数 $\phi$ 的梯度都精确为零，分支不会自行开始学习。
2. 若 $\alpha$ 是可训练标量且初始化为 $0$，则 $\alpha$ 本身可以先获得梯度；分支内部参数通常要等 $\alpha$ 离开零后才获得非零梯度。
3. 若不使用固定的零门，而把 $\Delta_\phi$ 的末端线性投影初始化为零，则该末端投影第一步可以获得梯度，投影之前的分支参数通常在后续步骤才开始获得梯度。

因此，C1 必须把“函数保持条件”和“分支如何获得第一批梯度”作为两个独立配置与测试项。

第二类 growth operator 是 clone-and-split：复制原有子模块，并把其最终线性贡献拆成若干份，使各份之和仍等于原输出。这可以同时保持函数并让多个副本获得梯度，但完全相同的副本具有对称性，需要通过数据、selector、adapter 或受控扰动打破。

#### 3.3 阶段 C2：兼容结构训练

原模型主路径仍是 always-on，新增 selector 只控制新增 residual 分支。此阶段可以逐步加入：

1. 单 block 的一个附加分支。
2. 一个父模块下多个并列兄弟分支。
3. 兄弟分支共享的一套 selector、预算和 merge。
4. 两层有界递归分支。
5. 模块级或 Attention head-group 级稀疏化。

旧 state-dict 始终可装载，旧路径也始终存在；但模型继续训练后不再与原 checkpoint 函数相同。“checkpoint-compatible”在这里表示参数和结构映射仍存在，不表示行为永远不变。

#### 3.4 阶段 C3：Checkpoint-derived 结构变异

当消融已经表明某些旧节点、head、FFN 通道或完整 block 长期冗余时，可以研究：

- 删除或合并节点。
- 把平铺分支重写为递归分支。
- 将 dense block 蒸馏到 SSM、Linear Attention 或其他 kernel。
- 改变 state layout、缓存方式和外层空间拓扑。
- 让 selector 真正跳过旧主路径的一部分。

这些操作可能改善推理性能，也可能使模型不再能直接装载原 state-dict。每次变异必须声明 teacher/checkpoint 来源、参数迁移函数、变异前后计算预算和继续训练数据；不能只用“从旧模型生长”掩盖不可归因的架构跳变。

### 4. 当前候选交界面：递归固定 merge 分支

令一个父模块的输入为 $x$，原始或 always-on 主分支为 $B_r$，候选分支的有限索引集合为 $J_r$。父模块共享的 selector 输出激活集合

$$
A_r(x)\subseteq J_r
$$

以及可选权重 $g_{r,j}(x)$。一种最直接的固定 merge 为

$$
\widehat B_r(x)
=
B_r(x)
+
\sum_{j\in A_r(x)}
g_{r,j}(x)\Delta_{r,j}(x).
$$

这里“固定”表示 merge 位置、输入槽和算子预先声明；$A_r(x)$ 可以随输入变化，未选择分支等价于向对应槽提供加法单位元 $0$。所有已选分支在父模块出口前完成，因此短分支不能先向外层空间后继发送、长分支再追赶修改同一输出。

每个 $\Delta_{r,j}$ 可以是：

- 单个 Attention、FFN、SSM、Linear Attention 或 DSA 类模块。
- `Attention -> FFN`、`SSM -> FFN` 等有限串联模块。
- 另一个满足同样单入口、单出口和固定 merge 契约的递归模块。

递归结构必须有有限最大深度、每层 fan-out 上界、每次选择的 Top-K 上界和最长串行路径上界。一个孙分支只有在其父分支已激活时才允许激活，因此实际激活子树是前缀闭合的。

![[assets/tide-two-route-convergence.svg]]

### 5. Selector scope 与空间连接分层

至少要区分三种 selector，不能把它们隐藏成一个全局控制器。

| 层次 | selector 读取和选择的对象 | 固定 merge 或提交点 |
| --- | --- | --- |
| 空间层 | 一个 cell/region 中哪些 HB site 执行并继续发送 | 下游节点入站汇聚或声明的空间收拢点 |
| 模块层 | 一个父模块下哪些短/长兄弟分支执行 | 父模块唯一出口 |
| Attention 内部 | 哪些 head 或 head group 执行 | Attention 输出投影之前 |

一个父模块分出的兄弟分支应共享一套 selector、预算和 selector state，而不是每个分支独立决定自己是否激活。嵌套 selector 的状态 namespace 属于相应父模块；不同序列、深度、空间 site 和父分支不能因物理共置而隐式共享可变语义状态。

第一版应让所有内部兄弟分支先在宏节点内部固定 merge，再由宏节点统一 `Emit` 到 $d+1$。这样外层空间连接仍由 HB-Sliced 的候选边定义。若一个内部分支可以独立向不同空间后继发送，它已经成为外层空间 DAG 的一部分，必须显式增加消息类型、分支来源、路由 artifact 和状态依赖，不能继续作为纯 `ActiveKernel` 配置处理。

### 6. Head-wise MoE 是嵌套固定 merge 的特例

对 $H$ 个 Attention heads，标准输出可以写成

$$
\operatorname{MHA}(x)
=
\operatorname{Concat}(h_1(x),\ldots,h_H(x))W_O
=
\sum_{i=1}^{H}h_i(x)W_O^{(i)}.
$$

因此 routed head 或 head-group 可以定义为

$$
\operatorname{RoutedMHA}(x)
=
\sum_{i\in A_{\mathrm{head}}(x)}
g_i(x)h_i(x)W_O^{(i)}.
$$

它仍在 Attention 内部固定回拢，再进入 block residual merge。实现可以保留固定 head 槽并让未选槽为零，也可以直接累加选中 head 的输出投影贡献；动态改变输出维度的拼接不应泄漏到 block 接口。

较稳妥的起点是少量 always-on core heads 加若干 routed head groups，而不是立即让每个微小 head 独立竞争。还必须单独选择状态语义：所有候选 head 是否都更新 K/V，还是只有选中 head 更新。前者更接近“收到即更新、激活才 readout”，状态更连续但节省不了全部 KV 成本；后者更稀疏，却会让未来 Attention state 依赖历史路由。

### 7. 两条路线如何交换证据

递归固定 merge 分支只是候选交界面，不保证两条路线最终重合。应分别记录三种关系：

| 关系 | 判定方式 |
| --- | --- |
| 结构汇合 | 两条路线得到同构或可由节点展开/收缩互相转换的 Graph family |
| 契约汇合 | 拓扑不同，但共享固定 merge、selector scope、状态所有权和 chunk correctness contract |
| 经验迁移 | 一条路线得到的训练、kernel 或 routing 结论能改善另一条路线，但模型仍不同 |

Graph 收缩线可以否决包含隐藏反向控制依赖、不可组合跨 token selector 或未定义状态提交的 growth operator。Checkpoint 生长线则可以通过消融说明某些 Graph 自由度没有收益，或发现固定 merge、always-on backbone 之外仍有稳定结构。若最终不汇合，两条路线仍分别产生理论边界和可部署模型，不构成研究失败。

### 8. Checkpoint 生长实验阶梯

![[assets/checkpoint-growth-ladder.svg]]

| 阶段 | 唯一主要新增变量 | 必须通过的 gate |
| --- | --- | --- |
| P0 原生基线 | Tide 装载与执行接口 | 参数、logits、cache/state、prefill/decode 和梯度对齐 |
| P1 单零分支 | 一个 residual delta | 初始 transition 等价；继续训练不劣于 matched baseline |
| P2 平铺分支 | 多个兄弟分支和固定 merge | 相同 active FLOPs 下的质量、吞吐和梯度覆盖 |
| P3 共享 selector | token-local soft/hard 选择 | route artifact equality、负载和 checkpoint 漂移 |
| P4 两层递归 | 有界递归与两级 selector | 信用分配、激活子树、最长路径和训练稳定性 |
| P5 空间化 | HB-Line/Plane 局部连接和设备放置 | 局部通信、稀疏 work 与端到端收益 |
| P6 结构变异 | 删除、合并或替换旧节点 | 迁移方法、质量恢复曲线和新模型独立 contract |

每个阶段至少保留 continued-pretraining 原模型、等参数 dense 扩展、等 active-FLOPs 平铺 MoE/branch 三类对照。不能同时改变 tokenizer、数据配比、优化器、selector、空间拓扑和 kernel，再把结果归因于“递归结构”。

---

## 第二部分：HB-Sliced 与 HB-Line-v0

> [!summary] 本部分定位
> 本部分只回答五个架构问题：静态空间节点是什么，静态候选边是什么，一个深度切片如何执行，selector 在哪里发生，以及有限 chunk 为什么只需固定次数的空间推进。HB-Line-v0 是用于看清这些对象的最小实例；HB-Plane 与 HB-Cube 只替换空间基图，不能反过来改变这些对象的含义。

> [!important] 当前主张
> HB-Line-v0 已有结构 reference，可验证 depth-major chunk、token-major decode 和任意两段 chunk continuation 的输出、route artifact 与完整状态相同。该结果证明的是当前 toy semantics 和两种 schedule 的一致性，不证明真实 Attention/SSM kernel、selector 低 span、模型可训练性或端到端吞吐。

### 1. 五类坐标不得混用

| 对象 | 符号 | 数学类型 | 直观含义 |
| --- | --- | --- | --- |
| 深度切片 | $d$ | 有限整数集合中的元素 | 网络从输入到输出推进到第几步 |
| 空间位置 | $u$ | 有限集合 $U$ 的元素 | 当前切片中哪个可复用计算位置 |
| 输入位置 | $t$ | 自然数 | 全局 token 流中的位置 |
| 层级尺度 | $j$ | 有限整数集合中的元素 | site、cell、region、global 中哪一级分组 |
| 微阶段 | $p$ | 固定有限集合中的元素 | Receive、Update、Allocate、Compute 等切片内部步骤 |

这里的“堆叠线段”只画 $(d,u)$。输入位置 $t$ 属于每条消息和每次状态转移；它不是第三条空间轴。微阶段 $p$ 属于 runtime lowering；它也不是新的空间平面。

### 2. 空间基图

#### 2.1 定义

令 $U$ 是非空有限集合。令

$$
F
\subseteq
\bigl\{\{u,v\}\mid u,v\in U,\ u\ne v\bigr\}.
$$

$F$ 的元素是无序二元子集。二元组

$$
H=(U,F)
$$

称为空间基图。对 $u\in U$，定义其空间邻居集合

$$
N_H(u)
=
\{v\in U\mid \{u,v\}\in F\}.
$$

$F$ 只说明“哪些空间位置彼此局部邻接”。它本身不是同一深度切片内的计算依赖边。

#### 2.2 Line、Plane 与 Cube

取整数 $n\ge 2$。HB-Line 使用

$$
U_{\mathrm{line}}=\{0,1,\ldots,n-1\},
\qquad
F_{\mathrm{line}}
=
\bigl\{\{i,i+1\}\mid 0\le i<n-1\bigr\}.
$$

对 $k\in\{2,3\}$ 和正整数 $n_1,\ldots,n_k$，定义坐标集合

$$
U_k
=
\prod_{j=1}^{k}\{0,\ldots,n_j-1\}
$$

以及

$$
F_k
=
\left\{
\{a,b\}
\ \middle|\
a,b\in U_k,
\sum_{j=1}^{k}|a_j-b_j|=1
\right\}.
$$

HB-Plane 取 $k=2$，HB-Cube 取 $k=3$。这个条件表示两个坐标恰有一个分量相差 $1$，其余分量相同。第一版均不使用环状边界；若以后加入周期边界，只改变 $F$，不改变后面的切片接口。

![[assets/hb-sliced-spatial-base-graphs.svg]]

维度变化不是纯粹的画图差异。若总 site 数为 $n$，规则线段、近似方形平面和近似立方体的典型直径分别为 $O(n)$、$O(n^{1/2})$ 和 $O(n^{1/3})$；内部最大邻居数分别为 $2$、$4$ 和 $6$。因此它们共享语义接口，但达到全局感受野所需深度、消息度数、路径数和训练难度不同。

### 3. 从空间基图生成前向计算 DAG

#### 3.1 静态节点与候选边

取整数 $D\ge 2$，并定义深度集合

$$
\mathcal D=\{0,1,\ldots,D-1\}.
$$

HB-Sliced 的静态计算节点集合为

$$
V_H=\mathcal D\times U.
$$

元素 $(d,u)$ 表示深度 $d$ 中空间位置 $u$ 的逻辑节点。候选消息边集合定义为

$$
E_H
=
\left\{
\bigl((d,u),(d+1,v)\bigr)
\ \middle|\
0\le d<D-1,
\ v\in\{u\}\cup N_H(u)
\right\}.
$$

其中 $v=u$ 是同位置前向边；$v\in N_H(u)$ 是局部扩散边。是否真的沿候选边发送，由当前输入位置的激活决定。

#### 3.2 DAG 性质

定义函数

$$
r:V_H\to\mathcal D,
\qquad
r(d,u)=d.
$$

对任意 $(x,y)\in E_H$，都有 $r(y)=r(x)+1$。若存在有向环，沿环每经过一条边，$r$ 都严格增加 $1$，回到起点时却必须恢复原值，矛盾。因此 $(V_H,E_H)$ 是 DAG。

这个证明与 $H$ 是线、平面、立方体或其他有限有界度图无关。即使无向空间基图 $H$ 含环，它也不会自动成为同一逻辑时刻的 zero-delay 计算环。

#### 3.3 为什么不直接加入同切片计算边

若把 $(d,u)\to(d,v)$ 直接加入计算图，则必须另外给出边方向和层内顺序。双向邻接会立即形成环；单向邻接也会增加与位置数有关的层内传播深度。HB-Line-v0 因而禁止这种边。

group allocator 确实会读取同一切片中多个节点的 score，但它在展开图中是独立微阶段：

```text
all Receive/Update/Score at depth d
    -> allocator(d, group)
    -> selected ActiveCompute/Emit at depth d
    -> messages for depth d+1
```

该展开只增加固定数量的微阶段，不等于允许节点沿 $F$ 在同一切片中反复传播。

### 4. HB-Line-v0 的具体实例

结构 reference 使用下面唯一的一组小参数，以便人工逐项核验：

| 参数 | v0 值 | 含义 |
| --- | ---: | --- |
| $U$ | $\{0,\ldots,7\}$ | 每个切片 8 个 site |
| $D$ | $6$ | 从 $d=0$ 到 $d=5$ 共 6 个切片 |
| 空间邻接 | 无回绕的一维半径 1 | $i$ 只邻接 $i-1$ 与 $i+1$ |
| cell partition | $\{0,1,2,3\}$、$\{4,5,6,7\}$ | 两个连续 cell |
| always-on sites | $1$、$5$ | 每个 cell 一个固定 backbone site |
| active budget | 每 cell 每位置最多 2 个 site | 一个 backbone 加最多一个稀疏 site |
| 输入扩展 | 向 $d=0$ 的 8 个 site 注入 | reference 的简化，不是最终通信方案 |
| 读出 | 合并 $d=5$ 发出的边界消息，再平均输出槽 $1$、$5$ | reference 的简化固定读出 |

![[assets/hb-line-v0-spatial-dag.svg]]

这张图只画静态架构：

1. 每一条横向线段对应固定 $d$ 下的空间基图副本。
2. 横向虚线表示 $F$，不是运行时消息边。
3. 淡色竖线和斜线是 $E_H$ 中的候选边。
4. 青色纵向路径是 always-on backbone 的一个实例。
5. 橙色路径只示意某个输入位置实际选择的稀疏子图。

图中只画 5 个切片和 6 个位置以减少线条；reference 仍使用 $D=6$ 和 $U=\{0,\ldots,7\}$。

### 5. 层级分组与 backbone

#### 5.1 层级分组是什么

集合 $U$ 的一个 partition 是一族非空子集，满足任意两个子集不相交，且所有子集的并集等于 $U$。取整数 $h\ge 1$，层级分组是有限序列

$$
(\mathcal P_0,\mathcal P_1,\ldots,\mathcal P_h),
$$

其中 $\mathcal P_0=\{\{u\}\mid u\in U\}$，$\mathcal P_h=\{U\}$，并且对每个 $0\le j<h$，$\mathcal P_j$ 中每个集合都包含于 $\mathcal P_{j+1}$ 的唯一集合。

site、cell、region、global 只是这组 partitions 的工程名称。它们不是额外空间维度，也不是深度切片。HB-Line-v0 具体取

$$
\mathcal P_0=\bigl\{\{u\}\mid u\in U\bigr\},
\qquad
\mathcal P_1=\bigl\{\{0,1,2,3\},\{4,5,6,7\}\bigr\},
\qquad
\mathcal P_2=\{U\}.
$$

未来可以增加更多尺度。

#### 5.2 always-on 与稀疏激活

选定 $j\in\{1,\ldots,h\}$，并令当前 allocator 的 group 集合为 $\mathcal G=\mathcal P_j$；因此 $\mathcal G$ 中的 group 两两不相交。对每个 $G\in\mathcal G$，静态指定非空 backbone 子集 $B_G\subseteq G$ 和正整数预算 $k_G$，并要求 $|B_G|\le k_G$。对深度 $d$、输入位置 $t$，令 $R_{d,G,t}\subseteq G$ 是实际收到消息的 site。allocator 输出激活集合

$$
A_{d,G,t}\subseteq R_{d,G,t},
$$

并满足

$$
B_G\cap R_{d,G,t}
\subseteq
A_{d,G,t},
\qquad
|A_{d,G,t}|\le k_G.
$$

因此，backbone site 只要收到消息就必须激活；其他接收 site 由 selector 决定。当 $d<D-1$ 时，一个激活 site 向下一切片中由 $\{u\}\cup N_H(u)$ 指定的全部候选后继发送；最后切片只沿单独声明的输出收拢边发送。未激活 site 已经完成状态更新，但不执行重 kernel，也不发送。

若使用多个层级 allocator，则每个层级分别选择一个 partition，并把前一级输出作为后一级候选；各级的次序和状态 namespace 必须显式声明。所有 allocator 依次位于 `Score` 与 `ActiveCompute` 之间。allocator 不得读取更深切片在当前 chunk 中刚产生的可变状态，也不得回头改变已经提交的上游激活。

### 6. 消息、节点状态与切片 transition

#### 6.1 消息

令 $\mathcal X$ 是有限维实向量空间。对 $0\le d<D-1$、输入位置 $t$ 和非负整数 source slot $\iota$，一条从 $(d,u)$ 发往 $(d+1,v)$ 的消息是有限记录

$$
m=(t,d,u,v,\iota,p),
$$

其中 $p\in\mathcal X$。五元组 $(t,d,u,v,\iota)$ 是消息标识符；HB-Line-v0 每条候选边至多发送一条消息，因而恒取 $\iota=0$。位置 $t$ 是消息字段，不表示 token、消息和轨迹是同一个对象。输入扩展消息和最后切片的输出收拢消息使用各自独立声明的边界记录类型。

令 $I_{d,u,t}$ 表示位置 $t$ 到达节点 $(d,u)$ 的有限消息序列。序列按 $(d-1,u_{\mathrm{source}},\iota)$ 的字典序排列；若 kernel 声明 merge 可交换、可结合，也可以使用相应的等价 reduce。物理到达顺序不进入 reference semantics。

#### 6.2 状态

对每个 $(d,u)\in V_H$，令 $\mathcal Q_{d,u}$ 是节点状态集合，并令 $q_{d,u,t}\in\mathcal Q_{d,u}$ 是输入位置 $t$ 处理前的单序列持久状态。对每个 $d\in\mathcal D$ 和 $G\in\mathcal G$，令 $\mathcal L_{d,G}$ 是 allocator 状态集合，并令 $\ell_{d,G,t}\in\mathcal L_{d,G}$。不同深度使用不同 state namespace：即使 $(d,u)$ 和 $(d+1,u)$ 放在同一张卡上，它们也不因此共享可变状态。

batch 中不同序列也不共享 $q$ 或 $\ell$。设备实时负载可以改变物理调度，但不能写入这些语义状态。

HB-Line-v0 只在一个输入位置已经通过全部 $D$ 个切片、且最终出站消息已经被读出后提交模型边界。因此位置 $B$ 的 continuation state 是下一个输入位置 $B$、全部 $q_{d,u,B}$ 和全部 $\ell_{d,G,B}$ 的有限元组，不含在途消息。若未来允许 pipeline 在消息尚未到达最终读出时返回，边界状态就必须另外携带这些在途消息，不能继续使用本简化。

#### 6.3 切片内固定步骤

对每个 $(d,u)\in V_H$，令 $\mathcal Z_{d,u}$ 是合并后节点输入的集合。`ObserveUpdate` 是一个确定函数，它把有限消息序列和节点状态映射到 $\mathcal Z_{d,u}\times\mathcal Q_{d,u}$；`Score` 是从 $\mathcal Z_{d,u}\times\mathcal Q_{d,u}$ 到 $\mathbb R$ 的确定函数。对每个非空 $I_{d,u,t}$，节点先执行

$$
(z_{d,u,t},q_{d,u,t+1})
=
\operatorname{ObserveUpdate}_{d,u}
(I_{d,u,t},q_{d,u,t}),
$$

再计算 cheap score

$$
\sigma_{d,u,t}
=
\operatorname{Score}_{d,u}
(z_{d,u,t},q_{d,u,t+1}).
$$

每个 group allocator 是确定函数：它读取有限映射 $\{(u,\sigma_{d,u,t})\mid u\in R_{d,G,t}\}$、静态配置和 $\ell_{d,G,t}$，输出 $A_{d,G,t}$ 与 $\ell_{d,G,t+1}\in\mathcal L_{d,G}$。只有 $u\in A_{d,G,t}$ 时才执行

$$
y_{d,u,t}
=
\operatorname{ActiveKernel}_{d,u}
(z_{d,u,t},q_{d,u,t+1})
$$

其中 `ActiveKernel` 是从 $\mathcal Z_{d,u}\times\mathcal Q_{d,u}$ 到预先声明的输出集合的确定函数；随后 `Emit` 把该输出映射为有限消息序列。若 $I_{d,u,t}$ 为空，v0 令节点状态保持不变，且该 site 不是候选。

![[assets/hb-sliced-node-transition.svg]]

该接口明确区分：

- `ObserveUpdate` 决定收到消息后必须提交的神经状态。
- `Score` 只产生紧凑控制输入，不能偷跑完整重 kernel。
- `Allocator` 决定激活和负载状态。
- `ActiveKernel` 才承载 Attention、FFN、SSM readout 或其他主要数值计算。
- `Emit` 在中间切片只沿 $E_H$ 中预先存在的后继发送，在最后切片只沿静态输出收拢边发送。

### 7. 一个 token 的直观路径

![[assets/hb-line-v0-token-route.svg]]

图中的橙色折线表示固定输入位置 $t$ 的一组消息依赖。它不是一个“token 对象在图里游走”：token 值 $x_t$、消息记录、节点事件和整条轨迹是四种不同对象。多个来自位置 $t$ 的消息可以在同一节点汇合；节点状态也可以把更早位置的信息带入位置 $t$ 的计算。

浅橙 site 已收到位置 $t$ 的消息并更新状态，但本次未继续激活。深橙 site 执行重 kernel 并发送。青色 site 是固定 backbone；它保证 selector 不会切断全部结构性前向路径和反向梯度通路，但不保证梯度数值不会衰减。

### 8. 连续伪代码

下面程序只展开架构语义，不指定 CPU、NPU 或线程调度：

```python
def hb_sliced_chunk(tokens, boundary_state):
    inbox_by_token = input_expand(tokens)

    for depth in range(D):
        next_inbox_by_token = empty_inboxes(tokens)

        # 位置顺序是 stateful selector 的 reference semantics。
        for t in token_positions(tokens):
            observed = parallel_map_receivers(
                observe_update_score,
                inbox_by_token[t],
                boundary_state.node[depth],
            )
            active = hierarchical_allocator(
                observed.scores,
                boundary_state.allocator[depth],
            )
            outgoing = parallel_map(
                active_compute_and_emit,
                active,
                observed,
            )
            next_inbox_by_token[t].append(outgoing)

        inbox_by_token = next_inbox_by_token

    return fixed_readout(inbox_by_token), boundary_state
```

实际实现不能在每个 token 上做一次 host/device 往返。合理 lowering 是：加速卡批量完成一个切片的 Observe/Update/Score，CPU 对紧凑 score 做每序列 scan，再把整批 route list 交回加速卡执行 packed ActiveKernel/Emit。

### 9. 架构节点与 kernel lowering

第一张空间图中的一个 $(d,u)$ 可以承载完整 node transition，不要求把 Attention、residual add 和 FFN 画成三个空间节点。例如 active kernel 可以是：

```python
def pre_norm_gpt_active_kernel(z, state):
    attention_delta = causal_attention(norm(z), state.kv)
    u = z + attention_delta
    ffn_delta = ffn(norm(u))
    return u + ffn_delta
```

如果两个 residual delta 都为零，结果精确退化为 $z$。对稀疏节点，可把 K/V projection 放在 `ObserveUpdate`，把 query、packed Attention、输出投影和 FFN 放在 `ActiveKernel`。Mamba/SSM 可把因果状态递推放在 `ObserveUpdate`，把较昂贵 readout 和发送放在 `ActiveKernel`。

这里存在两个表示层级：

| 表示层级 | 节点表示什么 | 用途 |
| --- | --- | --- |
| 架构层 | 一个完整 $(d,u)$ transition | 看空间 DAG、局部通信、激活和分支 |
| lowering 层 | Merge、KV update、Attention、FFN、allocator、Emit 等微阶段 | 实现、artifact equality 与性能优化 |

历史 HB-Lattice-v0 把 lowering 层的 P0-P7 同时画成“平面”，导致它们容易被误解为模型空间。HB-Sliced 不再使用这种主表示；只有确实产生跨节点依赖时，微阶段才在 expanded event DAG 中显式出现。

### 10. 输入扩展与输出收拢

完整模型不要求输入节点直接广播到所有 site。生产候选应使用只向前的层级 DAG：

```text
v_in
  -> global carrier
  -> region expansion
  -> cell expansion
  -> depth slice 0
  -> ...
  -> depth slice D-1
  -> cell contraction
  -> region contraction
  -> global readout
  -> v_out
```

扩展树和收拢树的深度、fan-out 与 merge 规则都属于静态图。HB-Line reference 为减少代码，直接向 $d=0$ 的全部 site 注入；在 $d=D-1$ 完成后，它把出站消息视为输出边界槽，按来源固定合并，并平均槽 $1$、$5$。这些规则不是最终通信设计。

### 11. Prefill、decode 与固定空间遍历次数

取整数 $B\ge0$ 和 $L\ge1$，当前 chunk 的全局输入位置集合为 $\{B,B+1,\ldots,B+L-1\}$。对其中固定输入位置 $t$ 和深度 $d$，把该切片的固定微阶段整体记为单元 $(d,t)$。HB-Line-v0 只有两类跨单元依赖：

$$
(d,t)\longrightarrow(d+1,t)
$$

其中 $0\le d<D-1$；它来自同一位置沿空间 DAG 前进。第二类依赖是

$$
(d,t)\longrightarrow(d,t+1)
$$

其中 $0\le d<D$、$t\ge0$；它来自节点和 allocator 的单序列持久状态。不存在 $(d+1,t)\to(d,t+1)$ 之类的反向隐藏依赖。

token-major decode 按

```text
(0,0),(1,0),...,(D-1,0),(0,1),(1,1),...
```

执行；depth-major chunk 按

```text
(0,0),(0,1),...,(0,L-1),(1,0),(1,1),...
```

执行。两者都保持上述两类依赖的先后关系。若每个 transition 是确定函数，并且不同深度的状态 namespace 不共享，则两种顺序只是同一个有限 event DAG 的两种合法拓扑序，因此产生相同输出、route artifact 和最终状态。

上面两个序列为节省字符写成了 $B=0$；一般 $B$ 只需把每个位置 $s\in\{0,\ldots,L-1\}$ 替换为 $B+s$，论证不变。

这给出两个不同强度的结论：

1. 空间推进次数为 $D$ 乘以固定微阶段数，与 chunk 长度 $L$ 无关。
2. 若 stateful selector 只能逐位置扫描，节点内部时间 span 仍可能是 $O(L)$；要达到 Transformer/Mamba 意义上的低 span，还需把 selector 声明为 token-local、scan-composable、causal-bulk，或显式承担 sequential fallback 成本。

可运行 reference 位于 [hb_line_v0_reference.py](examples/hb_line_v0_reference.py)：

```bash
python 20-tide-decentralized-neural-network/examples/hb_line_v0_reference.py
```

它同时检查：

- 一个完整 chunk 的 depth-major 执行等于逐 token 的 token-major decode。
- 一个完整 chunk 等于从任意中间边界拆成两次 chunk 执行。
- 比较对象包括输出向量、每个 $(t,d)$ 的 receiving/active site、消息数、节点状态和 allocator 状态。

### 12. 当前设计边界与下一步

HB-Line-v0 当前固定：空间 DAG 无环、只使用相邻切片边、所有消息时延为一个深度步、每个 group 至少一个 always-on site、收到即更新、激活才重计算和发送、固定最终读出。

它尚未决定：

1. 最终使用多少 site、多少深度和多少层级 partition。
2. backbone 是恒等、轻量 SSM、共享 GPT block，还是多级嵌套组合。
3. selector 先按语义筛候选还是先按负载给 quota。
4. 是否允许只向前的跨切片 shortcut 和固定 deadline branch。
5. line 的训练结果是否足以支持升级到 plane/cube。
6. 一个 site、一个 cell 或一个 region 应如何映射到本机 16 张 Ascend 卡。

升级到 HB-Plane/HB-Cube 前，应先在 HB-Line 上分别验证：局部通信度数、激活稀疏度、route artifact equality、状态增长、selector span、节点梯度覆盖和层级负载均衡。维度升级不能替代这些验证。

---

## 附录 A：历史 HB-Lattice-v0 索引

> [!warning] 历史材料，不是当前主模型
> 2026-08-07 的 HB-Lattice-v0 曾把 GPT-like 快路径、P5/P6 稀疏分支、P7 deadline merge、二维 cell/leaf 几何和 16 卡放置收缩成八个“宏平面”。这种表示混合了空间架构与 runtime lowering，现已由 HB-Sliced/HB-Line-v0 取代。

历史材料仍可从以下文件和 Git 版本追溯：

- [hb_lattice_v0_reference.py](examples/hb_lattice_v0_reference.py)：旧 toy semantics 与 `chunk == repeated decode` reference。
- [hb-lattice-v0-superblock.svg](assets/hb-lattice-v0-superblock.svg)：旧八阶段总图。
- [hb-lattice-v0-plane.svg](assets/hb-lattice-v0-plane.svg)：旧 4x4 cell/leaf 俯视图。
- [hb-lattice-v0-node-contract.svg](assets/hb-lattice-v0-node-contract.svg)：旧 CPU/NPU 节点 lowering 图。
- Git 提交 `bd035c7`：压缩前的完整逐段说明。

这些材料只用于回答“当前抽象从何而来”，不再定义当前节点、切片、selector、证明对象或实现顺序。

---

## 第三部分：Selector 与训练稳定性



> [!summary] 本页定位
> 本部分记录 HB-Sliced 候选架构中，CPU 侧严格时间递推 selector、加速卡侧节点计算、稀疏路径和节点持久状态共同带来的训练问题，以及从公开 MoE 研究和先进开源模型技术报告中可借鉴的稳定化方法。本文是研究备忘，不是数学定理、最终架构规范或已经验证的训练方案。

> [!example] 具体架构实例
> 本部分讨论一般训练风险；当前最小 HB 架构实例、节点契约和四张分离图见本页第二部分。历史八平面 superblock 只保留在附录 A，不再作为本部分的默认模型。第一部分的 checkpoint 生长模型也必须逐级接受本部分的 selector、路径漂移和信用分配检查。

本部分沿用较直观的中文名称：“节点”指一个 site，“格子”指一个 cell，“区域”指一个 region。若引用旧研究时出现“叶节点”，它只表示某次层级划分中最细、可被 selector 激活的 site，不为 HB-Line-v0 增加新的节点类型。

### 1. 当前候选架构

当前讨论的 HB-Line 是最低几何复杂度实例，不应被理解为最终只能有“线段、cell、site”三个固定层次。HB-Sliced 候选架构可概括为：

1. 空间图由固定有限个深度切片组成；每个切片中的位置集合是同一空间基图 $H=(U,F)$ 的副本。
2. 当前最小实例令 $H$ 为线段。升级到平面或立方体时，只替换 $U$ 与 $F$，不改变 node/allocator 接口。
3. site 之上可以配置 cell、region、hub 或更高尺度 backbone；这些尺度由 $U$ 上的嵌套 partition 定义，层次数不能写死。
4. 第一版只采用嵌套或互不相交的 partition。任意重叠区域会使状态归属、allocator 读写范围和负载统计明显复杂化，后置研究。
5. 普通消息边只从深度 $d$ 指向 $d+1$ 的同位置或空间邻居。allocator 作为 `Score -> Allocate -> Compute` 的显式固定微阶段，不允许节点沿同切片邻接反复传播。
6. 上游已激活节点向所有固定邻接后继发送消息。收到消息的节点总是执行状态更新；是否执行昂贵计算并继续发送，由本节点所属层级的 selector 或其他激活机制决定。
7. selector 可以存在于 site、cell 或更高区域尺度。不同尺度可以使用不同策略，例如高层 always-on、cell 级语义选择、cell 内 site 级负载分配。
8. selector 预期主要在 CPU 上处理紧凑控制数据；节点的大批量数值计算预期由加速卡处理。
9. 设备放置不进入 HB-Line 定义。line 可把连续 site/cell 分片到设备；未来 HB-Plane 可再研究把 4x4 cell 静态映射到本机 16 张 Ascend 卡。

这里需要区分三个相互独立的层次概念：

| 概念 | 作用 |
| --- | --- |
| 计算层级 | 哪些节点或区域执行神经计算、持有什么神经状态 |
| 路由层级 | selector 在什么范围读取摘要、维护负载状态并作出激活决定 |
| 设备层级 | 节点、格子或区域如何映射到 CPU 与加速卡 |

三者不必一一对应。一个格子可以是语义专门化单元，格子内多个节点则只是共享或近似共享参数的容量副本；同一个设备也可以承载多个计算层级。

这个候选架构的主要吸引力是：

- 空间计算图保持 DAG，可按深度切片推进。
- 空间局部性限制单次通信范围。
- 稀疏发送激活限制昂贵节点计算和后续传播规模。
- 一个切片内可以把多个 batch、多个 token 和多个节点的工作打包后交给加速卡。
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
| HB-Sliced Tide | hard routing 可改变后续多个深度切片的完整传播路径，并可与节点状态和历史负载状态耦合 | 标准 MoE 风险之外，还增加长路径信用分配、路径分布漂移和状态/路径耦合 |

因此，Mamba 不一定在优化意义上比 Transformer 更难，MoE 也不必然产生 loss spike。但 hard routing 确实引入了一组 dense Transformer 和连续 SSM 没有的训练风险。若 Tide 的一次选择会改变后续几十个深度切片的路径，其训练问题一般比单层 MoE 更强。

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

在标准 MoE 中，这已经会造成未选专家缺少任务反馈。在 HB-Sliced Tide 中，一个较早深度的选择还会改变后续多个切片的输入，未选路径的反事实质量更难获得。

#### 5.2 路径级分布漂移

第 $d$ 个深度切片的路由变化会改变第 $d+1$ 个切片的输入分布；第 $d+1$ 个切片的 router 和节点参数随之变化，又会继续改变更深切片。若有 96 个切片，这种变化可以沿整条路径放大。

#### 5.3 长路径信用分配

若只在最终输出处计算损失，较早深度的 selector 收到的学习信号要经过许多 hard choice、节点状态和局部 kernel。即使数值梯度仍能传播，信号也可能很弱且方差很大。

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

标准 MoE 的稀疏分支通常在一个 block 内立即求和并返回共同 residual stream，因此一次路由决定的生命周期很短。Tide 若让分支连续穿过许多深度切片而长期不收拢，路径分布漂移和信用分配都会更强。

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

加速卡根据 route list 对选中节点执行 packed Attention、FFN、SSM 或其他昂贵 kernel，并产生向下一深度切片的传播消息。

这种拆分的关键收益是：hard selector 主要控制昂贵残差和传播，而不是直接控制节点是否进行任何状态更新。收到消息并更新状态不等于一定获得有效任务梯度；只有该状态在当前或未来被读出并影响损失，梯度才会到达相应更新。

### 8. 稳定化原则

#### 8.1 层级化 always-on backbone

always-on backbone 不应只理解为“每个深度切片一个 shared expert”。它可以形成多个嵌套层级：

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

##### 8.1.1 前向跨切片 shortcut 与不等长路径

若一条跨切片边始终从较早深度指向较晚深度，它仍属于空间 DAG，不会因为“跨越多个切片”自动破坏 `prefill`。固定非负整数时延可以：

- 直接写入消息的逻辑到达时间；
- 或展开成若干只做延迟的中间节点。

真正需要定义的是：不同长度路径在何种逻辑时刻汇聚、节点按什么顺序更新状态、哪些消息对当前读出可见。只要这些规则固定、因果且节点窗口转导器满足时间分块组合律，不等长前向路径本身是可处理的。

工程上，等长路径加 residual 更容易做规则张量计算；带时间桶的不等长路径表达力更强，但需要 ragged inbox、watermark 和更复杂的 packed kernel。两者应作为可对比方案，而不是预先断言只有等长路径正确。

##### 8.1.2 反馈回路的边界

[[tide-background-history-and-references#第二部分：人脑信号传播调查|人脑信号传播调查]] 强调，真实脑网络包含并行分支、跨区 shortcut、丘脑中继和大量前馈/反馈闭环。这为 Tide 的多尺度 backbone、hub、旁路和选择性增益提供设计联想，但不构成数字模型应直接复制脑连接的证据。

对 Tide：

- 同 token、同内部时刻的反向边会重新引入空间环和 zero-delay 求解问题，暂不进入高性能主线。
- 带正时延、从 token $t$ 的高层状态影响 token $t+1$ 或更晚低层状态的反馈，可以在有限 chunk 上展开成 event DAG，但会引入时间递推，需要单独证明是否 scan-composable。
- 若只需要“先高层处理，再回到低层细化”的效果，可以在更晚深度切片复制一个低层类型节点，用前向 DAG 表达 refinement，而不必首先引入真实空间环。

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

##### 8.1.4 小词表与减少深度切片数

“用 byte 级词表让简单词主要由 backbone 学会，复杂长句扩散到更深分支”是有价值的研究假设，但当前没有理论保证。

byte tokenization 的收益包括更小 embedding/output vocabulary、无 OOV 和更细粒度组合；代价是序列显著变长，selector 递推次数、状态更新次数以及 Attention/SSM 的时间维度成本都会增加。简单词也需要多个 byte token 才能完成，因此“简单内容必然走短路径”需要由训练目标、路由代价或辅助监督主动促成。

可比较的方案至少包括：

1. 纯 byte token。
2. 常规 BPE/SentencePiece token。
3. byte 输入后先做局部 patch/compression，再进入层级 backbone。
4. 固定深度切片数但允许 conditional depth。
5. 减少深度切片数、提高每切片节点容量或状态表达力。

深度切片数不应直接类比 GPT block 数。若层级 backbone、局部状态和分支计算已经提供足够有效深度，减少切片数完全可能；但应由 scaling experiment 决定。

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

当每个已激活上游节点向 $c$ 个邻接后继发送时，单步新增记录量约与“激活发送数乘以 $c$”同阶。它仍受稀疏激活和有界度控制，但可能在长序列、多切片下成为主要内存成本。固定大小的 SSM 或 linear-attention state 在这一维度更容易控制。

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

这与 EvoMoE 的 dense-to-sparse 思路一致，但 Tide 还需要同时控制多切片路径和节点状态。

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

可在少量中间深度切片加入训练期辅助读出或 teacher representation matching。辅助损失应在训练后期衰减，避免强行要求每个切片都形成完整语言模型表示。

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

在只有相邻深度切片边的最低复杂度模型中，合理的单切片执行流程是：

```text
前一深度切片完成当前 chunk
    -> 加速卡批量执行 Observe / Update / Score
    -> 一次传输紧凑候选分数和标识符到 CPU
    -> CPU 按 token 顺序扫描 selector 状态并生成 route list
    -> 一次传输 route list 到加速卡
    -> 加速卡按节点/格子打包 ActiveCompute / Emit
    -> 进入下一深度切片
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

若加入只向前的跨切片 shortcut，调度单位应从“相邻深度切片”推广为“拓扑阶段”：

1. 一个阶段等待其所有拓扑前驱产生当前窗口所需的消息桶。
2. scheduler 按目标节点和逻辑到达时间合并相邻边与 shortcut 消息。
3. 加速卡执行本阶段的批量状态更新与评分。
4. CPU 完成本阶段各层级 selector 的顺序控制。
5. 加速卡执行激活计算并把消息投递到后续一个或多个阶段。

只要所有边严格向前，仍可按拓扑序处理。不同固定时延需要额外时间桶，但不要求退化为每 token 一次 host/device 同步。真正的反馈边则不能直接套用这一单次拓扑流程。

即使 selector 每个事件只处理少量标量，总事件数仍约为：

$$
O(DBL),
$$

其中 $D$ 是深度切片数，$B$ 是 batch size，$L$ 是 chunk 长度。随着节点计算越来越稀疏，CPU selector 反而可能成为 Amdahl 瓶颈。因此需要：

- 候选度数保持常数且较小。
- 每个深度切片批量扫描多个 batch 和 token。
- 使用紧凑连续内存和预分配 route buffer。
- CPU 选择与其他深度切片的加速卡计算双缓冲或流水重叠。
- 对 selector 单独测量每秒决策数，而不是只看其数据体积。

### 10. 建议的训练推进顺序

下面 A-D 是 selector 复杂度阶梯，与第一部分的 P0-P6 checkpoint 生长阶梯正交。第一版实验应先固定某个 P 阶段，再只改变 A-D 中的一项；不能把“增加递归深度”和“加入 stateful selector”作为同一次实验变化。

#### 阶段 A：固定均衡路由

使用静态 hash、固定局部路径或预生成均衡路由，不训练 selector。

目标是验证：HB-Line 拓扑、节点 kernel、状态更新和稀疏梯度覆盖本身能否训练。若这一阶段失败，问题不应归因于学习式 router。

#### 阶段 B：token-local learned routing

加入只依赖当前节点输入和神经状态的可学习语义分数，不加入历史负载递推。

目标是隔离 learned routing 和 selected-only feedback 的影响。

#### 阶段 C：慢速负载偏置

加入停止梯度、慢更新、幅度受限的负载修正；先在 optimizer step 或固定大窗口之间更新，并在一次 forward 内冻结。

目标是验证负载均衡收益和语义专门化损失之间的权衡。

#### 阶段 D：单序列严格时间递推 selector

最后加入逐 token 更新的 selector 历史状态，并证明、测试其 chunk composition 和 `prefill = decode` artifact equality。

目标是判断精细时间均衡是否带来超过额外串行控制、路由变化和训练困难的收益。

不建议直接从阶段 D 开始训练完整 96 切片模型。否则一旦训练不稳定，很难区分根因。

### 11. 必须记录的训练指标

#### 11.1 路由一致性

- 固定验证前缀在不同 checkpoint 的 Top-K Jaccard overlap。
- 每个 token 最后一次改变目标节点发生在训练的什么位置。
- 第 $K$ 与第 $K+1$ 个候选之间的 score margin。
- 邻近 checkpoint 的路径编辑距离。
- 不同深度切片的 route saturation 速度。

#### 11.2 负载与死亡节点

- 每深度切片、每 cell 和每 site 的激活次数。
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
3. 每个深度切片的 always-on backbone 应是统一共享块、每 cell 共享块、SSM，还是只保留轻量残差？
4. 历史负载状态应在序列边界重置，还是作为可延续的单序列 boundary state？
5. 负载修正只作为 Top-K tie-breaker，还是允许在更大的语义候选集合内重新排序？
6. 是否需要训练期 shadow route，以及允许多少额外计算预算？
7. 中间深度切片的辅助损失如何设计，才不会把所有节点强制训练成相同表示？
8. 节点和格子到 16 张 Ascend 卡的静态映射，是否足以吸收剩余负载波动，减少 selector 对模型语义的干预？
9. selector 的逐 token CPU scan 在多大 $B$、$L$ 和 $D$ 下开始成为关键路径？

### 14. 从人脑稀疏到 Tide node 稀疏：讨论综合

> [!summary] 本节定位
> 本节系统整理 2026-08-10 围绕动态稀疏、路径分布漂移、长路径信用分配、人脑微观与宏观功能稀疏、LH selector、粗粒度 node、replay、固定 merge 和高性能 `prefill` 的讨论。它给出设计假设、反例和实验顺序，不把脑科学类比写成训练稳定性定理。本部分前文第 3--13 节仍提供 MoE 证据、selector 接口和既有训练建议；本节负责把这些内容收束到同一个尺度分层中。

今日问题与本节内容的对应关系如下，后文按结论之间的逻辑关系重新排序，而不是按发言顺序逐条抄录：

| 今日讨论的问题 | 对应小节 |
| --- | --- |
| 路径分布漂移和长路径信用分配是否由任何稀疏激活必然引起；residual 与短生命周期 merge 到底改善什么 | 14.1 |
| 人脑是否也依赖大量 hard selector；它如何保持训练、推理和行为的相对稳定 | 14.2--14.4 |
| 人脑大颗粒功能稀疏是否不同于局部稀疏；是否依靠唯一主干收拢 | 14.5--14.6 |
| LH 的固定局部连接、收到即更新、激活后全下游发送、局部能量竞争、恢复和阈值语义 | 14.7 |
| 粗粒度 Tide node 能否通过增加节点数获得类似神经群体的平滑性；稠密 hidden vector 与 node 稀疏有何差别 | 14.8--14.9 |
| 状态化 selector、CPU 顺序控制、空间常数遍历与高性能 `prefill` 能否同时成立 | 14.10 |
| 海马式 replay 和各级 merge 处的局部学习如何在不改变推理 transition 的条件下借鉴 | 14.11--14.12 |
| 上述讨论对 Tide 架构与增量实验顺序的共同约束 | 14.13--14.14 |
| 模块内部大量小值为何通常不能直接转化为稀疏加速；当前硬件是否可能使稠密模型已经处于最佳粒度 | 14.15 |
| MoE 的全局候选、设备间 all-to-all 和共同 residual merge 与 Tide 局部结构稀疏有何本质区别 | 14.16 |
| 构造局部计算介质是否约等于解决路径漂移和信用分配；其中哪些内容可以证明 | 14.17 |
| 人脑两种尺度的稀疏对粗粒度 hard node 有何反向证据；狭窄中间粒度是否存在如何成为 Tide 核心假设 | 14.18 |
| 2026-08-10 的前沿开放权重模型采用了什么结构；为什么仍以规则 block 与短生命周期 MoE 为主 | 14.19 |
| MoE 在立即 merge 后是否仍能影响下一层路由和后续 Token；它与 Tide 的信息量和路径身份有何区别 | 14.20 |
| 从“只有末级叶子稀疏”到一般 Tide 应如何形成可逐级验证的架构阶梯 | 14.21 |
| “更长距离的信用分配”中的距离到底是什么；何时 Tide 确实比 MoE 更难 | 14.22 |

#### 14.1 稀疏激活本身不是两个训练问题的充分条件

首先区分四个不同问题：

| 问题 | 数学或工程含义 | 动态 hard routing 是否必然带来 |
| --- | --- | --- |
| 路由边界不连续 | selector score 穿过 Top-K 边界时，执行子图离散变化 | 除退化情形外，是 |
| selected-only feedback | 未选路径缺少“若选择它会怎样”的任务反馈 | 通常是 |
| 路径分布漂移 | 同类输入在不同 checkpoint 或历史状态下进入不同下游分布 | 容易发生，但不是必然 |
| 长路径信用分配 | 某次选择经过很长控制生命周期后才得到有效学习信号 | 取决于发散到收拢的距离和中间控制依赖 |

静态剪枝、固定 hash、固定稀疏拓扑和冻结 router 可以具有很高稀疏度，却没有 checkpoint routing drift。连续 soft gate 或稀疏连续 gate 也可以改变分支权重，而不产生同样强的离散边界。因此不能把上述问题归结为“任何稀疏激活都会发生”。风险最强的组合是：

> 可学习的离散选择、差异较大的候选函数、未覆盖的反事实分支，以及过长的控制生命周期同时出现。

令 always-on 主路径为 $b(x)$，有限候选分支集合为 $J$，分支 $j\in J$ 的 residual 函数为 $\Delta_j$，分支权重为 $g_j(x)$，hard mask 为 $a_j(x)\in\{0,1\}$，则固定加法 merge 可以写成：

$$
y(x)
=
b(x)
+
\sum_{j\in J}
a_j(x)g_j(x)\Delta_j(x).
$$

若路由从分支 $i$ 切换到分支 $j$，并且其他分支不变，则稀疏残差的跳变量为：

$$
\Delta y(x)
=
g_j(x)\Delta_j(x)
-
g_i(x)\Delta_i(x).
\tag{T-14.1}
$$

由此可把主要风险拆成三个近似独立、需要分别测量的量：

1. **切换频率 $C$**：同类输入多频繁地改变 active set。
2. **边界跳变量 $J_{\mathrm{jump}}$**：一次 active-set 改变造成的表示差 $\lVert\Delta y(x)\rVert$，或该量在指定验证集上的统计量。
3. **控制寿命 $D_{\mathrm{control}}$**：该选择在多少层、状态更新或后续 routing 中仍保持独立路径身份。

当分支被约束成尺度较小的有界 residual delta 时，residual 设计主要降低 $J_{\mathrm{jump}}$；固定且频繁的 merge 主要降低 $D_{\mathrm{control}}$；margin、慢速 router、EMA teacher、蒸馏和后期冻结主要降低 $C$。只写成 residual 形式、却不限制 residual 分支的尺度，并不会自动减小跳变量；三类措施也都不能单独解决全部问题。

标准 MoE 即使在一个 block 内立即 merge，仍然保留 Top-K 边界不连续、selected-only feedback 和可能的 routing drift。但 merge 后路径身份被压回共同 residual stream，因此它没有 HB-Sliced 中“某次选择继续改变随后几十个切片的 routing”的同等长控制链。其早期专家贡献仍需通过后续深层网络到达最终 loss，但这部分更接近普通深网络的长程梯度，而不是持续未收拢的路径身份信用分配。

#### 14.2 人脑确实稀疏，但不等价于大量 MoE 式 hard selector

至少要区分四种脑稀疏性：

| 稀疏性 | 含义 |
| --- | --- |
| 结构稀疏 | 一个神经元只连接全脑神经元中的极小部分 |
| 群体稀疏 | 某个时刻只有部分神经元具有较强活动 |
| 时间稀疏 | 单个神经元只在部分时间产生 spike |
| 功能稀疏 | 某些神经群只对部分情境、任务或动作显著贡献 |

一个高度简化的神经元工作流是：

~~~text
接收固定解剖连接上的大量突触输入
-> 连续更新膜电位、树突和局部突触状态
-> 超过局部阈值时产生离散 spike
-> spike 沿预先存在的轴突影响固定下游
~~~

这里确实存在大量 hard threshold，但它与 MoE router 有五个关键差异：

1. 阈值主要决定“是否广播 spike”，通常不为每次 spike 动态选择任意目标；轴突目标大体固定。
2. 一个 spike 的贡献通常很小，下游同时整合大量神经元的输入。
3. 未产生 spike 不等于状态不更新；亚阈值膜电位、突触状态和可塑性仍可能变化。
4. 稀疏模式由大量局部阈值、兴奋/抑制平衡、增益和复发动力学共同形成，不是一个全局 Top-K 控制器一次决定完整路径。
5. 接近 hard choice 的基底节门控、工作记忆更新和动作提交只占完整认知过程的一部分；直接、间接和超直接通路也不是严格的一开一关。

因此，人脑更接近“固定稀疏图上的大量局部 `Update + EmitGate`”，而不是“每层用一个 router 在多个完整且相互独立的专家之间排他选择”。

#### 14.3 人脑没有消除微观漂移，而是保持宏观功能不变量

同一任务在多天或更长时间尺度上可以出现 representational drift：具体参与的神经元、单细胞调谐和微观活动模式发生变化，而行为仍相对稳定。一个有用的抽象是给定微观状态集合 $\mathcal S_{\mathrm{micro}}$、宏观功能状态集合 $\mathcal Q_{\mathrm{macro}}$ 和粗粒化函数：

$$
\alpha:
\mathcal S_{\mathrm{micro}}
\to
\mathcal Q_{\mathrm{macro}}.
$$

大量不同的微观状态可以满足：

$$
\alpha(s)=q.
$$

只要活动漂移仍留在同一个宏观功能等价类中，具体神经元路径变化不必改变行为。可能共同起作用的稳定机制包括：

- 群体编码、冗余和多个部分可替代的微观实现。
- 下游读取依赖群体统计、低维轨迹或通信子空间，而不是永久绑定单一神经元。
- 部分稳定核心表征与允许漂移的外围表征并存。
- 下游突触也缓慢持续适应，而不是假设上游永久冻结。
- 稳态可塑性、抑制平衡和突触缩放防止长期过强或沉默。
- 毫秒活动、较慢突触学习、更慢结构变化和离线巩固之间存在时间尺度分离。

这不表示人脑已经严格解决路径漂移。遗忘、习惯干扰、错误归因和行为波动都说明问题仍然存在。其工程目标更接近“宏观行为足够稳定、错误可由持续反馈纠正”，而不是“同一刺激必须重放逐神经元相同 artifact”。

#### 14.4 人脑也没有已知的精确全局信用分配算法

生物信用分配仍是开放问题。较可信的图景不是一个最终 scalar loss 精确反传整个全脑路径，而是多种局部和延迟教学机制并行工作：

- 感觉系统持续获得局部预测误差和真实感觉反馈。
- 小脑通过攀缘纤维等通路获得较直接的事件、预测和校准信号。
- 基底节利用多巴胺奖励预测误差学习动作、价值和认知门控。
- Eligibility trace 暂时保留近期活动过的突触资格，延迟调制信号到达后再影响可塑性。
- 海马和皮层的离线重放、睡眠及系统巩固反复呈现过去经历。
- 注意、目标和神经调质决定哪些局部区域在当前阶段允许更强可塑性。
- 进化和发育已经提供反射、感觉主通路、局部学习规则和价值先验，脑并非从随机 Graph 与单一终局 loss 开始训练。

因此，人脑采用的是“足够好的局部信用、多个闭环反馈、延迟资格痕迹和反复纠错”，不是已经发现了等价于精确 backpropagation 的生物算法。这也解释了为何学习需要重复练习、探索、睡眠和巩固，并仍会失败。

#### 14.5 大颗粒功能稀疏不是脑区被完全关闭

大尺度脑区或功能网络的所谓“激活”通常是相对于持续背景活动的增量。可作如下直观分解：

$$
z_{\mathrm{brain}}(t)
=
z_{\mathrm{baseline}}(t)
+
\Delta z_{\mathrm{task}}(t).
\tag{T-14.2}
$$

未出现在某张 task-activation map 中，不表示脑区没有代谢、没有放电、没有接收输入或没有更新状态。大颗粒功能稀疏更接近：

~~~text
多个持续存在的结构和背景动力学
+ 少数任务相关网络获得更高增益
+ 某些网络间的有效通信暂时增强
+ 若干宏观状态在任务期间成为主导
~~~

大颗粒功能状态不是与局部稀疏完全独立的第二种机制。它由局部阈值、兴奋/抑制竞争、长程连接、丘脑协调、神经调质、振荡相位和复发动力学经过粗粒化共同产生。但粗粒化会出现新的亚稳态与吸引子效应：状态内部允许大量平滑或随机微观漂移，状态之间则可以在证据积累后发生相对突出的切换。

因此，大颗粒功能稀疏并非处处平滑，也不是任意跳变。较稳定的宏观切换通常包含：连续证据积累、决策 margin、吸引子或 hysteresis、防止边界抖动的抑制竞争，以及切换后的感觉反馈和在线修正。

#### 14.6 人脑不存在唯一全局主干，但存在多级稳定接口

人脑没有一条严格对应 Transformer residual stream 的唯一全局 backbone。更接近的图景是“多条相对稳定主通路、多种闭环和多级汇聚接口”：

- 感觉系统有相对稳定的外周、脑干/丘脑和皮层主通路。
- 视觉腹侧流与背侧流分工但持续交换和重汇聚。
- 皮层-基底节-丘脑环路完成选择后重新影响皮层。
- 小脑结果通过丘脑、脑干等接口重新进入运动或认知网络。
- 额顶、丘脑和其他 hub 协调多个任务相关网络。
- 动作最终汇聚到脑干、脊髓和肌肉等共同输出系统。

固定 merge 对 Tide 的价值，不是声称脑中存在同一种加法 merge，而是为可变微观路径建立稳定宏观接口：分支在有限生命周期后必须产生声明类型的状态或 tensor，再由固定算子进入下一段。Tide 可以采用多个层级 backbone 与 region-local merge，而不必强制全模型只有一条主干。

#### 14.7 LH 的结构稀疏、状态更新与局部 selector

LH 复杂参考实现已经明确具有结构稀疏，当前 Tide 也计划保留以下核心语义：

1. 空间 Graph 只包含局部连接，不是全连接。
2. 节点一旦激活，就向其所有静态下游节点发送消息；selector 主要决定节点是否激活，而不是为每条消息任意改写目标拓扑。
3. 下游只要收到上游消息，就可以记忆并更新 KV cache、SSM 或其他神经状态。
4. 下游是否激活并继续发送，由下游局部策略决定。
5. 某个逻辑时刻没有收到消息时，内部状态仍可以按明确规则保持、leak 或 decay。
6. 同一区域中的节点竞争有限激活预算；节点激活后可以进入恢复期，激活阈值也可以慢速调整。

这里的“能量竞争”目前只对应数字模型中的区域激活预算、恢复状态和慢速阈值，不表示已经定义或验证了一个物理能量模型。

历史 LH selector 主要统计过去激活次数，并据此降低再次激活的优先级。它粗略实现了防止长期过强或长期沉默的 homeostatic/refractory 效果，但没有显式表示当前消息经过时间累积后是否已经形成足够激活证据。

为避免再次混淆状态，本节沿用本部分第 6.1 节“神经状态”的 $q_{i,t}$ 表示 KV/SSM 等神经状态，并新增：

| 符号 | 对象 | 作用 |
| --- | --- | --- |
| $q_{i,t}$ | 神经状态 | KV、SSM、Linear Attention accumulator 等 |
| $u_{i,t}$ | 信号累积状态 | 积累当前和近期入站消息形成的激活证据 |
| $r_{i,t}$ | 恢复状态 | 节点激活后暂时提高再次激活成本 |
| $\theta_{i,t}$ | 慢速阈值状态或固定参数 | 调节长期激活率和兴奋性；若它是状态，其更新规则必须另行声明 |
| $c_{i,t}$ | 历史负载统计 | 记录较慢的使用率，不承载神经表示 |

下面只定义一种待实验的控制动力学，不把它当作 LH 的唯一解释。令 $R$ 为一个非空有限节点集合，称为一个 selector 区域；令 $t\in\mathbb N$ 为单条序列中的 token 逻辑位置，而不是物理执行时刻。对每个 $i\in R$：

- $I_{i,t}$ 是节点 $i$ 在位置 $t$ 收到的有限消息多重集。
- $E_i$ 是把 $I_{i,t}$ 映射成实数激活证据的函数，并规定 $E_i(\varnothing)=0$。
- $s_{i,t}\in\mathbb R$ 是本部分第 6.2 节“语义分数”定义的内容语义分数。
- $a_{i,t}\in\{0,1\}$ 是本位置的最终激活指示量。

取 $\lambda_i,\rho_i,\eta_i\in[0,1]$ 和 $\alpha_i,\gamma_i,\beta_i,\mu_i,\nu_i\geq 0$。节点先把当前位置的消息纳入信号累积量，并让恢复状态衰减：

$$
\widehat u_{i,t}
=
\lambda_i u_{i,t}
+
E_i(I_{i,t}),
\qquad
\widehat r_{i,t}
=
\rho_i r_{i,t}.
\tag{T-14.3}
$$

令区域平均历史负载为

$$
\overline c_{R,t}
=
\frac{1}{|R|}
\sum_{j\in R}c_{j,t}.
\tag{T-14.4}
$$

局部 selector 不应只读取其中一个量。可先定义节点 $i$ 的有效分数：

$$
\ell_{i,t}
=
s_{i,t}
+
\alpha_i \widehat u_{i,t}
-
\mu_i \widehat r_{i,t}
-
\nu_i(c_{i,t}-\overline c_{R,t})
-
\theta_{i,t},
\tag{T-14.5}
$$

令 $K_R\in\{0,1,\ldots,|R|\}$ 为区域激活预算，并令 $\mathcal F_R$ 为所有满足 $|A|\leq K_R$ 及其他预先声明静态拓扑约束的子集 $A\subseteq R$ 所成的有限集合。一个确定的区域选择策略是函数

$$
\Pi_R:\mathbb R^R\to\mathcal F_R.
$$

它从带节点下标的有效分数向量中产生激活集合：

$$
A_{R,t}
=
\Pi_R
\left(
(\ell_{i,t})_{i\in R}
\right).
\tag{T-14.6}
$$

令 $a_{i,t}=\mathbf 1[i\in A_{R,t}]$。完成本位置的选择后，控制状态按下式延续到位置 $t+1$：

$$
\begin{aligned}
u_{i,t+1}
&=
\widehat u_{i,t}-\gamma_i a_{i,t},\\
r_{i,t+1}
&=
\widehat r_{i,t}+\beta_i a_{i,t},\\
c_{i,t+1}
&=
\eta_i c_{i,t}+(1-\eta_i)a_{i,t}.
\end{aligned}
\tag{T-14.7}
$$

这里 $s_{i,t}$ 是内容与节点的语义匹配，$\widehat u_{i,t}$ 是包含当前消息后的积累证据，$\widehat r_{i,t}$ 是选择前的短时恢复成本，$c_{i,t}$ 是慢负载统计。把四者分开，才能实验“语义、信号强度、恢复和均衡”各自是否有效；若重新压成一个历史计数，就无法知道训练失败来自哪一部分。

当 $I_{i,t}$ 为空时，式 T-14.3 仍应用 leak/decay。若同一逻辑位置有多条上游消息，必须先按固定、确定且与物理到达顺序无关的规则形成 $I_{i,t}$ 或其聚合结果。神经状态 $q_{i,t}$ 的含义及其更新仍分别由本部分第 6.1 节“神经状态”和第 7.1 节“`Observe / Update / Score`”负责，不应与这里的控制状态递推合并成一个含义不明的“节点状态”。

#### 14.8 粗粒度 Tide node 不会因数量增加而自动平滑

一个 LH/Tide node 可能代表大量神经元，甚至是一个完整 Attention、SSM、FFN 或 Transformer block。关闭一个神经元与关闭一个宏观 kernel 不是同一粒度。若每次只选择一个相互独立的完整模块：

$$
y=b(x)+\Delta_i(x),
$$

则从 $i$ 切换到 $j$ 的变化仍为式 T-14.1。把候选节点数从 16 增加到 4096 不会自动缩小该跳变量，反而可能增加决策边界数量。

若同时激活 $K$ 个较小贡献，并做归一化 merge：

$$
y
=
b(x)
+
\frac{1}{K}
\sum_{i\in A(x)}
\Delta_i(x),
\tag{T-14.8}
$$

只替换其中一个节点时，单次变化才可能随单节点贡献尺度下降。因此，增加 node 数只有同时满足下列条件时，才可能近似人脑的群体平滑性：

1. 同时激活多个节点，而不是始终 Top-1。
2. 单节点只提供有界 residual delta，不替换完整主路径。
3. 同一 cell 内节点共享主体参数、状态接口或输出子空间。
4. 邻近输入或相邻逻辑时刻的 active set 有较高 overlap。
5. 多个节点在固定 cell/region 边界重新聚合。

稠密模型中的 hidden vector 已经提供一种微观群体表示：很多坐标接近零，少量坐标较大，但整体函数通常随输入连续变化。接近零的坐标不自动转化为硬件计算稀疏；一旦把连续坐标分组成可跳过的完整模块，就重新引入 group threshold 与粗粒度跳变。

因此，Tide 更合理的尺度分工是：

~~~text
Node 内部：
    稠密向量或细粒度稀疏向量
    Attention / SSM / FFN
    连续群体表示

Node 之间：
    固定局部结构稀疏
    条件 residual contribution
    局部 K-of-M 激活
    层级固定 merge
~~~

更多小节点还会减小单次矩阵尺寸、增加 metadata、packing 和通信开销。因此“节点越多越接近脑”不是单调结论；必须同时测量稳定性收益与加速卡利用率损失。

#### 14.9 不同 Tide node 不应共享同一种稀疏语义

建议至少声明三类架构角色：

| Node 类型 | 激活方式 | 训练与稳定性要求 |
| --- | --- | --- |
| Backbone node | always-on 或极高激活率 | 提供稳定信息、状态和梯度路径 |
| Population node | cell 内 K-of-M，多节点共同贡献 | 小 residual、共享主体、频繁节点换路可接受 |
| Specialist node | 条件激活、较低频率、较明显功能贡献 | 强证据、margin、hysteresis、固定 merge 和局部监督 |

Population node 更接近神经群体中的细粒度功能稀疏；specialist node 更接近条件性的记忆检索、校准或任务网络参与。二者不能只因都使用 hard mask，就由同一个无差别 selector 管理。

一个候选层级是：

~~~text
Region
├── always-on local backbone
├── Cell A：稳定语义功能
│   ├── 多个共享主体的 population nodes
│   └── 局部累积、恢复与负载均衡
├── Cell B：另一种稳定语义功能
└── 少量 specialist branches
        -> fixed region merge
~~~

语义专门化优先发生在 cell/region 级；cell 内节点可以作为容量副本、参数共享分片或相近子空间中的微观实现。这样节点级路由允许漂移，而 cell 的宏观输入输出 contract 保持稳定。

下面把“更多小节点可能使单次换路更平滑”写成一个明确的充分条件。令 $\mathcal H$ 为有限维赋范向量空间，$C$ 为有限节点集合，节点 $i\in C$ 在固定输入 $x$ 上的 residual contribution 为 $v_i(x)\in\mathcal H$。对 active set $A\subseteq C$，定义带节点下标的输入元组

$$
z_A(x)
=
\left(
\mathbf 1[i\in A]v_i(x)
\right)_{i\in C}
\in
\mathcal H^C.
$$

令 fixed merge 为函数 $M_C:\mathcal H^C\to\mathcal H$，并定义 $h_C(A,x)=M_C(z_A(x))$。若存在 $L_C\geq 0$，使得任意 $z,z'\in\mathcal H^C$ 均满足

$$
\left\|M_C(z)-M_C(z')\right\|
\leq
L_C
\sum_{i\in C}\left\|z_i-z_i'\right\|,
$$

则对任意两个 active set $A,A'\subseteq C$，直接得到：

$$
\left\|h_C(A,x)-h_C(A',x)\right\|
\leq
L_C
\sum_{i\in A\triangle A'}
\left\|v_i(x)\right\|.
\tag{T-14.9}
$$

这里 $A\triangle A'=(A\setminus A')\cup(A'\setminus A)$ 是对称差。式 T-14.9 说明，提高 active-set overlap、限制单节点 contribution、共享表示空间和采用具有较小 $L_C$ 的稳定 merge，比单纯增加候选节点数更直接。该界只约束固定输入上的 merge 输出变化，不证明训练过程中的 active set 会稳定，也不证明最终任务损失的变化同样小。

#### 14.10 局部 stateful selector 可以保持空间常数遍历，但不自动低 token span

对固定无环空间 Graph，可以让上游节点先产生整个有限 chunk 的带逻辑时间消息；节点随后一次接收按逻辑时间整理的 inbox，并在节点内部执行：

~~~python
for t in logical_times:
    neural_state = update_neural_state(neural_state, inbox[t])
    excitation = leak(excitation) + evidence(inbox[t])
    recovery = decay(recovery)
    active = local_select(
        semantic_score[t], excitation, recovery, threshold, load_state
    )
    if active:
        emit[t] = active_compute(neural_state, inbox[t])
        recovery = apply_refractory(recovery)
~~~

于是空间执行仍可保持：

~~~text
上游节点完成整个 chunk
-> 当前节点获得完整时间序列 inbox
-> 当前节点产生整个 chunk 的 route list 和消息
-> 下游节点开始处理
~~~

这与“空间节点拓扑遍历次数不随 chunk 长度增长”兼容，也允许 K/V projection、Attention、SSM readout、FFN 和消息 packing 使用大批量 kernel。但 selector 内的 $u/r/\theta/c$ recurrence 可能仍有 $O(L)$ 顺序 span。

线性 leak、affine accumulator 和可结合统计量可能进一步 scan；threshold、reset、refractory 与 region Top-K 一般不会自动具有结合律。第一版可以接受 CPU 处理小型顺序控制递推，但必须测量它何时成为关键路径，不能把它称为 Transformer 意义上的完全 token-parallel prefill。

保持 `prefill = decode` 还要求：

- selector 只读取本 region 的历史控制状态和当前已到达的上游消息。
- selector 不读取当前 chunk 尚未计算的下游状态或物理设备负载。
- 控制状态逐序列隔离，并进入 chunk boundary state。
- decay 使用逻辑时间差，不使用物理等待时间。
- 同一逻辑时间的消息采用确定聚合，与物理到达顺序无关。
- batch 组合、chunk 切分和设备调度不改变 route artifact。
- 若一组相互竞争的节点在空间上并列，应把竞争表示为位于其前方的显式 region allocator，不能让 selector 同时读取自己选择之后才产生的输出。

#### 14.11 Replay 必须区分训练调度与推理 transition

“海马重放不兼容高性能 prefill”只对模型在推理过程中主动回放内部轨迹的强版本成立。至少应区分：

| Replay 类型 | 是否改变推理 transition | 与高性能 prefill 的关系 |
| --- | --- | --- |
| 训练数据 replay | 否 | 旧序列仍可用普通 chunk prefill 重新训练 |
| Route/hidden/teacher artifact replay | 否 | 可用旧路径、旧表示和 logits 约束当前 checkpoint |
| 推理时模型内部 latent replay | 是 | 引入动态循环、额外状态和可能的跨 token 控制链 |

前两类是训练与巩固方法，不要求推理时重演过去。可以对固定 replay 样本记录旧模型的投影表示和输出分布，并使用：

$$
\mathcal L_{\mathrm{replay}}
=
\left\|
P(h^{\mathrm{new}})
-
P(h^{\mathrm{old}})
\right\|^2
+
\lambda
D_{\mathrm{KL}}
\left(
p^{\mathrm{old}}
\Vert
p^{\mathrm{new}}
\right).
\tag{T-14.10}
$$

人类语言理解本身不提供 Transformer 式高性能 `prefill` 的证据。视觉可以并行接收多个文字，但认知和决策具有显著序列性、反馈和有限工作记忆。Tide 应把脑科学用于启发结构稀疏、稳态控制和信用分配，而把 Attention、SSM、causal bulk 与 packed kernel 作为机器架构独有的工程优势。脑中的微环路和上下文保持也不必逐神经元复制；Attention、SSM 和 Linear Attention 可以作为粗粒度数字功能模块。

#### 14.12 Fixed merge 处逐段学习不等于切断端到端梯度

设第 $r$ 个有限生命周期分支段对位置 $t$ 的固定 merge 输出为：

$$
h_{r+1,t}
=
B_r(h_{r,t})
+
\sum_{j\in A_{r,t}}
g_{r,j,t}
\Delta_{r,j}(h_{r,t}).
\tag{T-14.11}
$$

主模型始终保留最终语言模型损失 $\mathcal L_{\mathrm{final}}$，并允许该损失端到端反向传播。所谓“各级 merge 处逐段学习”，首先只表示在训练时为确定的 merge 表示增加较近的辅助信号，而不是执行 greedy layer-wise training 或停止主梯度。

一种 representation-distillation loss 是：

$$
\mathcal L_{\mathrm{repr}}^{(r)}
=
\sum_t
\left\|
P_r(h_{r+1,t})
-
\operatorname{stopgrad}
\left(
h^{\mathrm{teacher}}_{r+1,t}
\right)
\right\|^2.
\tag{T-14.12}
$$

也可以增加训练期中间 next-token 读出：

$$
\mathcal L_{\mathrm{LM}}^{(r)}
=
\sum_t
\operatorname{CE}
\left(
W_rh_{r+1,t},
x_{t+1}
\right).
\tag{T-14.13}
$$

总损失可以写成：

$$
\mathcal L
=
\mathcal L_{\mathrm{final}}
+
\sum_r
\alpha_r
\mathcal L_{\mathrm{repr}}^{(r)}
+
\sum_r
\beta_r
\mathcal L_{\mathrm{LM}}^{(r)}
+
\lambda_{\mathrm{replay}}
\mathcal L_{\mathrm{replay}}.
\tag{T-14.14}
$$

$P_r$、$W_r$ 和这些辅助 loss 可以只在训练时存在，推理时删除。对长度为 $L$ 的 chunk，所有位置的投影和交叉熵仍可使用规整矩阵计算；$x_{t+1}$ 只作为监督目标进入 loss，不进入位置 $t$ 的前向依赖，因此不破坏 causal prefill。

辅助 loss 缩短了表示和分支获得监督的距离，但仍不能自动给 hard selector 的未选索引提供反事实梯度。还需要在训练期选择 soft gate、大于推理期的 $K$、少量 shadow branch、straight-through surrogate 或带局部 baseline 的 policy-gradient/advantage estimator。训练期额外执行不能进入 reference output；本部分第 11.5 节“语义不变量”的 route artifact equality 仍以推理 selector 语义为准。

辅助目标也可能过强地迫使所有中间深度形成相同表示。第一版应优先使用 teacher representation matching、小权重辅助读出并在训练后期衰减 $\alpha_r,\beta_r$，同时做无辅助 loss 对照。

#### 14.13 对 Tide 的综合架构建议

本轮讨论收敛到以下尺度化架构，而不是“所有 nodes 都是独立专家”：

~~~text
多级 always-on backbone
-> region/cell 级稳定语义接口
-> cell 内多个小 residual population nodes
-> 少量具有明确进入/退出条件的 specialist branches
-> 各级有限生命周期和 fixed merge
-> 下一层级 backbone / region
~~~

建议优先遵守：

1. `Update` 与 `EmitGate` 分离：收到消息即更新声明的神经状态，激活主要决定昂贵计算和继续发送。
2. 固定局部连接：节点激活后向所有静态下游发送，不首先引入任意动态目标改写。
3. Cell 级专门化：语义 routing 优先选择 cell；cell 内只在真正可交换或相近的 population nodes 间做强负载均衡。
4. 多主干而非单主干：每个层级或 region 有稳定 backbone 和 merge contract。
5. 大颗粒 specialist 使用更强证据、margin 与 hysteresis；population nodes 允许更频繁的局部换路。
6. 分支输出使用归一化、有界 residual contribution，避免一个 node 切换替换全部语义。
7. Router 参数、稳态阈值和结构变化使用慢时间尺度；token-time 激活可以快速变化，但不能读取物理调度状态。
8. 脑式反馈、推理时 replay 和未收拢长控制链不进入第一版 strict prefill 模型。

需要特别区分两种 hysteresis。跨 optimizer step 的慢 router/threshold 更新和后期冻结属于训练稳定化，不改变单次推理语义；跨 token 的状态化进入/退出规则属于模型 transition，会产生顺序控制状态，必须进入 boundary state 并承担相应 span。

#### 14.14 建议的增量实验阶梯

为了避免一次引入全部 LH 与脑式机制后无法归因，建议按下列顺序推进：

1. 固定空间 DAG、always-on backbone、全部 residual branches 执行并 fixed merge。
2. 加入静态稀疏 active set，先验证容量、质量、packing 和通信。
3. 加入只读取当前输入的 token-local 语义 selector。
4. 加入独立信号累积 $u_{i,t}$，暂不加入恢复状态和负载均衡。
5. 加入恢复状态 $r_{i,t}$ 与慢速阈值 $\theta_{i,t}$。
6. 加入历史负载 $c_{i,t}$，并限制它只在语义上可接受的 cell 内做均衡。
7. 加入训练期 shadow route、merge-local auxiliary loss 和 replay consistency。
8. 加入两层递归分支和更长但有界的 specialist 生命周期。
9. 最后才比较推理时 delayed feedback、内部 replay 或其他会形成跨 token 控制链的机制。

每一级除最终质量和吞吐外，至少记录：

- Active-set overlap、route churn 和切换 margin。
- 式 T-14.1 的边界跳变量分布。
- 每次选择的控制寿命和 fixed-merge 距离。
- Cell 级与 node 级输入分布漂移。
- 激活、梯度、语义和优化器状态饥饿。
- Shadow branch 相对 selected branch 的局部 regret。
- Selector CPU 顺序时间、packed kernel 利用率和通信量。
- 不同 chunk 切分、batch 组合和逐 token decode 的完整 artifact equality。

在先把 $C$、$J_{\mathrm{jump}}$ 与 $D_{\mathrm{control}}$ 分别归一化成无量纲非负统计量后，一个值得检验、但当前不是定理的风险代理是：

$$
R_{\mathrm{route}}
\propto
C
\cdot
J_{\mathrm{jump}}
\cdot
D_{\mathrm{control}}.
\tag{T-14.15}
$$

实验应分别改变三项，而不是只改变 Top-K 或稀疏比例。若该代理具有预测力，Tide 可以在保持高稀疏度的同时，通过较高 active-set overlap、较小 node delta、较短局部生命周期和更稳定的 cell 级语义显著降低训练风险。

#### 14.15 数值接近零不等于可获利的稀疏计算

模块内部的 hidden value 接近零，首先是一种数值或表示现象，不自动成为硬件可以跳过的工作。必须区分：

1. **近零值**：浮点值很小但不等于零；跳过它会改变模型函数。
2. **精确零值**：数值等于零，但其位置可能是不规则且随输入变化的。
3. **结构化零值**：零值满足硬件预先支持的 block、N:M 或其他规则模式。
4. **模块未激活**：一个具有明确边界的完整 kernel 在本次执行中可以不运行。

固定一个硬件平台和输入 workload，并采用把关键路径开销相加的简化时间模型。令 $T_{\mathrm{dense}}\in\mathbb R_{\geq 0}$ 为稠密 kernel 的实际执行时间；令 $T_{\mathrm{detect}}$、$T_{\mathrm{pack}}$、$T_{\mathrm{index}}$ 和 $T_{\mathrm{sparse}}$ 为检测非零位置、重排数据、处理索引以及执行稀疏 kernel 的非负时间。在该模型中，稀疏执行真正有时间收益的条件是：

$$
T_{\mathrm{detect}}
+
T_{\mathrm{pack}}
+
T_{\mathrm{index}}
+
T_{\mathrm{sparse}}
<
T_{\mathrm{dense}}.
\tag{T-14.16}
$$

式 T-14.16 没有一个脱离硬件、数据类型、矩阵形状和 batch 大小的统一稀疏率阈值；流水重叠存在时还应直接测量总关键路径，而不能机械相加各项。当前加速卡上的大矩阵稠密乘具有连续访存、成熟调度和很高的矩阵单元利用率；动态无结构稀疏则还会引入索引、分支、packing 和负载不均衡。因此即使 hidden vector 中有大量小值，稠密计算仍可能是当前硬件下最合适的执行粒度。未来硬件若原生支持静态局部通信、稀疏数据流或更低成本的动态调度，式 T-14.16 两侧的关系可以改变。

只增加并行分支而不跳过任何分支，主要增加的是容量和总计算量：

$$
y(x)
=
b(x)
+
\sum_{j\in J}\Delta_j(x).
$$

它可能改善表达能力、优化或物理并行度，但不是条件计算。MoE 的主要计算收益来自只执行 $A(x)\subset J$ 中少量专家：

$$
y(x)
=
b(x)
+
\sum_{j\in A(x)}g_j(x)\Delta_j(x),
\qquad
|A(x)|\ll |J|.
\tag{T-14.17}
$$

因此，若把 expert 看作 node，MoE 已经实现了粗粒度 node 计算稀疏；它没有自动解决的是 node 换路的语义平滑性。扩大 dense 模型的深度和宽度，以及扩大 MoE 的总专家数但保持较小 active expert 数，都是当前硬件上较常见的规模扩展方式，因为二者最终仍把昂贵工作整理成规则的稠密 kernel。

Tide 必须进一步区分两个粒度：

| 粒度 | 含义 |
| --- | --- |
| 语义 node | 模型中具有参数、状态、输入输出 contract 和激活语义的对象 |
| 执行 tile | runtime 在特定硬件上一次打包、放置或调用的工作单元 |

一个语义 node 不必对应一次很小的 kernel launch。多个 node 可以跨 token、batch 或 cell 被打包成 grouped GEMM 或其他大 kernel。该 lowering 只有在不执行语义上未激活的昂贵分支、并保持 route artifact equality 时，才同时保留模型稀疏性和硬件效率。

#### 14.16 从 MoE 星形结构到局部计算介质

标准 MoE 的专家不是彼此全连接。更准确的逻辑结构是：共同 token residual stream 产生 router score，一个 token 可以从全体专家中选择任意少数专家，所选专家的输出随后立即 merge 回同一个 token stream。若专家分布在不同设备上，token dispatch 与 gather 在物理实现中通常表现为设备间 all-to-all 通信。因此应区分：

~~~text
逻辑层：全局候选专家 -> 少量选择 -> 共同 residual merge
物理层：token 在设备间 dispatch / gather，常形成 all-to-all collective
~~~

MoE 的共同 merge 不只是通信结构，也是一项训练优势：一次专家选择的独立路径身份通常只持续一个 block，随后又进入稳定的公共接口。Tide 若改成持续存在的局部 node 网络，就同时放弃了这项短控制寿命优势。

下面给出局部结构稀疏的最低数学描述。令固定有限空间 DAG 为 $G=(V,E)$，并给定正整数 $\Delta$，使每个节点 $v\in V$ 都满足：

$$
\deg^+(v)\leq\Delta,
\qquad
\deg^-(v)\leq\Delta.
\tag{T-14.18}
$$

于是 $|E|\leq\Delta|V|$。对一个随规模 $n$ 增长的 Graph family $\{G_n=(V_n,E_n)\}_{n\in\mathbb N}$，“有界局部连接”进一步要求存在同一个 $\Delta$，使式 T-14.18 对每个 $G_n$ 都成立；仅对单个有限 Graph 声称“存在某个最大度数”是平凡事实。

对单条序列中的 token 位置 $t$，令 $A_t\subseteq V$ 为激活节点集合。若沿用“节点激活后向所有静态下游发送”的语义，则本位置实际用于发送的边集合为：

$$
E_t^{\mathrm{emit}}
=
\left\{
(u,v)\in E:
u\in A_t
\right\}.
\tag{T-14.19}
$$

没有出现在 $A_t$ 中的接收节点仍可以因为收到 $(u,v)\in E_t^{\mathrm{emit}}$ 上的消息而执行 `Observe / Update`；$A_t$ 只表示哪些节点执行声明的昂贵激活计算并继续发送。式 T-14.18 是结构稀疏，$A_t$ 与式 T-14.19 是执行时激活稀疏，二者不能相互替代。

这种局部计算介质的潜在收益是：

- 参数和 KV/SSM 等状态可以长期留在拥有它们的 node 或 region 附近。
- 静态邻接可以映射到设备、chiplet 或片上网络中的局部链路。
- 激活节点不必把 token 动态发送到任意全局设备。
- 多层局部路径可以组合出单层 MoE 星形结构没有的计算轨迹。
- 模型规模增长时，节点度数与单次局部通信范围仍可保持有界。

相应代价是：局部路径可能长期不收拢，全局负载调节变难，早期选择持续改变后续输入分布，路径分布漂移和信用分配都可能比短生命周期 MoE 更严重。结构局部性本身不解决这些问题，也不自动保证整个图具有足够小的直径或信息混合能力。Tide 因而不能简单地删除 merge；更可行的方向是使用局部、周期性和层级化的 fixed merge 与 always-on backbone，在不恢复单一全局 all-to-one 星形结构的前提下限制路径寿命。

固定逻辑邻接还必须与物理放置共同设计。若逻辑邻居被放到相距很远的设备上，式 T-14.18 只提供图论局部性，不提供物理通信局部性。当前通用加速卡可能仍偏好把一个 region 内的多个语义 node 合并为较大的执行 tile；未来 many-core、chiplet、wafer-scale 或近存硬件则可能使固定局部边更直接地映射成低成本通信通道。

#### 14.17 “解决”路径漂移与信用分配的准确含义

构造局部计算介质，确实要求 Tide 正面处理比 MoE 更强的路径分布漂移和信用分配风险，但不能把研究目标写成“证明漂移完全消失”或“证明任意训练必然收敛”。路径变化本身可以存在；关键在于它是否仍保持声明的宏观功能 contract。

令 $\mathcal U$ 为待比较的有限 chunk 输入集合，$\mathcal C$ 为合法左边界状态集合，$\mathcal H_{\mathrm{out}}$ 为赋范输出空间，$\Omega$ 为某个固定有限模型的合法 route artifact 集合。对每个 $\omega\in\Omega$，定义强制使用该 artifact 时的输出函数

$$
F_\omega:
\mathcal U\times\mathcal C
\to
\mathcal H_{\mathrm{out}}.
$$

再定义非负路径差异函数

$$
d_{\mathrm{route}}:
\Omega\times\Omega
\to
\mathbb R_{\geq 0},
\qquad
d_{\mathrm{route}}(\omega,\omega)=0.
$$

它可以取为各局部 merge 段 active-set 对称差大小之和。本文不要求它一定满足三角不等式，因此称为差异函数而不是默认称为度量。定义固定输入与边界状态上的换路扰动：

$$
J(\omega,\omega';x,C)
=
\left\|
F_\omega(x;C)
-
F_{\omega'}(x;C)
\right\|.
\tag{T-14.20}
$$

令 $\mathcal P$ 为预先声明的合法比较四元组集合：

$$
\mathcal P
\subseteq
\Omega\times\Omega\times\mathcal U\times\mathcal C.
$$

一类可以尝试严格证明的结构性充分条件是：存在常数 $\varepsilon\geq 0$，使每个 $(\omega,\omega',x,C)\in\mathcal P$ 都满足

$$
J(\omega,\omega';x,C)
\leq
\varepsilon
d_{\mathrm{route}}(\omega,\omega').
\tag{T-14.21}
$$

本部分式 T-14.9 的 bounded residual 与 Lipschitz fixed merge 是获得局部版本式 T-14.21 的一种方式。它只说明固定模型参数下的换路影响有界，不说明 router 会少换路，也不说明两个 artifact 对任务具有相同质量。不同 checkpoint 之间的完整路径分布漂移还同时改变模型参数，即函数族 $F_\omega$ 本身也会变化；式 T-14.21 只控制其中的 route-sensitivity 分量，不能直接充当完整 checkpoint drift 界。

信用分配可采用另一组结构代理：

1. 每个动态选择在最多 $H$ 个空间深度后进入 fixed merge，即 $D_{\mathrm{control}}\leq H$。
2. always-on residual backbone 为所有输入保留固定的前向与反向计算路径。
3. merge-local auxiliary loss 或 teacher target 把某些监督路径长度限制在预先声明范围内。
4. 训练期 soft/shadow route、较大的 $K$ 或其他 estimator 为未选分支提供受控反事实反馈。

前两项可以作为架构性质证明；第三项可以证明“存在较短监督依赖路径”；第四项可以证明哪些分支被执行并进入 loss。但这些都不能证明梯度数值一定足够大、非凸优化一定收敛、selector 一定形成有用功能或最终质量一定提高。always-on 路径的存在尤其不等于其 Jacobian 不会衰减或抵消。

因此，“Tide 解决了路径漂移和信用分配”应拆成三层结论：

| 层次 | 可以要求的结论 |
| --- | --- |
| 数学与架构 | `prefill = decode`、有界连接度、有界控制寿命、换路扰动界、明确状态所有权和监督路径存在性 |
| 训练实验 | route churn、边界跳变量、梯度覆盖、输入分布漂移和最终质量处于可接受范围 |
| 系统实验 | 跳过的工作大于 selector、packing、通信和负载不均衡开销，得到实际端到端收益 |

只有三层同时成立，局部计算介质才算在一个具体模型规模、任务和硬件平台上得到证真；单独证明 DAG correctness 或单独观察训练 loss 正常都不充分。

#### 14.18 狭窄中间粒度假设

人脑的两种尺度观察，对粗粒度 hard node 提供的是有限但重要的反向证据，而不是一个否定定理。

第一，单神经元 spike、群体稀疏与稠密 hidden vector 中大量小坐标都体现了“许多小贡献共同形成宏观表示”的图景。两者并不严格等价：hidden coordinate 没有固定神经元身份，换基后坐标稀疏性也可能改变；但该类比说明，微观贡献的出现和消失通常不会替换完整宏观功能模块。

第二，大尺度功能网络通常表现为持续背景活动之上的增益、耦合和主导程度变化，而不是整个脑区严格从 0 关闭到 1 开启。宏观区域还具有重叠、冗余和多条重汇聚路径。这倾向于反对“独立大模块之间频繁 Top-1 切换天然稳定”的假设，并支持以下 Tide 分解：

~~~text
Observe / Update：通常仍执行
ActiveCompute：只在选择后执行昂贵稠密 kernel
Emit：只在激活后沿固定局部边继续传播
~~~

该脑科学类比仍不能决定数字模型的最优粒度。人脑的物理基底、能量预算、学习规则和序列处理方式不同，也没有提供 Transformer 式高性能 `prefill` 的范例；基底节、动作提交等系统也确实包含较强的离散门控。因此它只能作为反对粗暴大模块开关、支持群体重叠和持续底座的设计倾向。

Tide 面临的核心冲突可以写成：

> 被跳过的条件分支必须足够昂贵，稀疏执行才有系统收益；但单个分支的语义贡献又必须足够小、不同 active set 必须足够重叠、动态路径必须足够快地 merge，训练和输出才不会因 hard routing 发生不可控跳变。

先固定一个实验 protocol，其中包含任务、数据规模、dense baseline、硬件平台、时间或能耗二选一的收益口径、有限 route 比较集，以及数值越大表示质量越高的质量指标。一个候选 Tide 设计记录 $\xi$ 至少包含合法输入集合 $\mathcal U_\xi$、有限可选 node 集合 $V_\xi^{\mathrm{opt}}$、active-set 函数

$$
A_\xi:
\mathcal U_\xi
\to
2^{V_\xi^{\mathrm{opt}}},
$$

以及节点执行成本函数

$$
\kappa_\xi:
V_\xi^{\mathrm{opt}}
\to
\mathbb R_{>0}.
$$

这里 $2^{V_\xi^{\mathrm{opt}}}$ 表示 $V_\xi^{\mathrm{opt}}$ 的幂集。令 $\mathfrak X$ 为所有满足以下条件的候选设计记录构成的集合：

1. node 内部的昂贵 kernel 使用稠密计算，node 之间采用固定局部结构。
2. 动态激活是非平凡的：存在 $x,x'\in\mathcal U_\xi$ 使 $A_\xi(x)\neq A_\xi(x')$。
3. 确实存在被跳过的正成本工作：存在 $z\in\mathcal U_\xi$ 和 $v\in V_\xi^{\mathrm{opt}}$ 使 $v\notin A_\xi(z)$；由 $\kappa_\xi$ 的值域可知 $\kappa_\xi(v)>0$。

第二、三项共同排除了“所有输入始终走同一路径”和“只做一次静态剪枝”的退化解。对每个 $\xi\in\mathfrak X$ 定义下列函数或统计量：

| 量及值域 | 含义 |
| --- | --- |
| $\operatorname{Correct}(\xi)\in\{0,1\}$ | 是否满足 protocol 声明的 chunk correctness；取值为 1 时必须另附证明或验证证书 |
| $\Delta(\xi)\in\mathbb N$ | 空间 Graph 的最大入度与最大出度二者中的较大值 |
| $G_{\mathrm{hw}}(\xi)\in\mathbb R$ | 相对 dense baseline 的端到端时间或能耗收益，正值表示有收益 |
| $J_{\max}(\xi)\in\mathbb R_{\geq 0}$ | protocol 固定有限 route 比较集上的最大换路扰动 |
| $H_{\mathrm{control}}(\xi)\in\mathbb N$ | 动态选择保持独立路径身份的最大声明寿命 |
| $Q(\xi)\in\mathbb R$ | protocol 指定的模型质量指标 |
| $Q_{\mathrm{ref}}\in\mathbb R$ | dense baseline 在同一任务上的质量 |

再给定允许的最大局部度数 $\Delta_0\in\mathbb N_{>0}$、可接受常数 $\varepsilon\geq 0$、$H_0\in\mathbb N$ 和 $\delta\geq 0$。定义候选可行设计集合：

$$
\begin{aligned}
\mathfrak X_{\mathrm{feasible}}
=
\bigl\{
\xi\in\mathfrak X:
&\ \operatorname{Correct}(\xi)=1,\\
&\ \Delta(\xi)\leq\Delta_0,\\
&\ G_{\mathrm{hw}}(\xi)>0,\\
&\ J_{\max}(\xi)\leq\varepsilon,\\
&\ H_{\mathrm{control}}(\xi)\leq H_0,\\
&\ Q(\xi)\geq Q_{\mathrm{ref}}-\delta
\bigr\}.
\end{aligned}
\tag{T-14.22}
$$

> [!important] Tide 狭窄中间粒度假设
> 对至少一组有实际意义的任务、规模和硬件平台，存在某种设计使 $\mathfrak X_{\mathrm{feasible}}\neq\varnothing$。

这是一项混合数学与经验的可证伪假设，不是当前定理。Correctness、有界连接和有界控制寿命可以形式证明；$G_{\mathrm{hw}}$、$J_{\max}$ 和 $Q$ 必须通过实现与实验测量。当前硬件上该集合可能为空，意味着相应规模下 dense 模型已经处于更合适的粒度；硬件、编译器、packing 方法或模型规模变化后，同一设计族的可行集合也可能从空变为非空。

如果 Tide 最终成功，更准确的结论不是“所有局部稀疏 Graph 都优于 dense 或 MoE”，而是：已经为某个非平凡范围的任务、规模和硬件证实狭窄中间粒度确实存在，并找到了进入该区域的一组结构与训练方法。这本身就是 Tide 最重要的研究结果之一。

#### 14.19 前沿模型提供的现实基线

本小节只记录截至 2026-08-10 可以从官方仓库、模型卡或技术报告确认的结构事实。参数量中的“激活”表示一次 Token 前向实际使用的参数量级，不表示这些参数在训练中都收到同样大小的梯度。Qwen3.8-Max 的完整 checkpoint 配置在该日期尚未公开，因此只记录发布页已经披露的口径，不从第三方推测层数和专家数。

| 模型 | 总参数 / 激活参数 | 稀疏与主干结构 | 与本节直接相关的其他结构 |
| --- | --- | --- | --- |
| GLM-5.2 | 744B / 40B | 78 个主干层，前 3 层为 dense；MoE 层含 256 个 routed experts，每 Token 选择 8 个，并有 1 个 shared expert | DSA、IndexShare、1M context |
| Kimi K3 | 2.8T / 104B | 93 层，896 个 experts，每 Token 选择 16 个，并有 2 个 shared experts；采用 Stable LatentMoE 与 Quantile Balancing | 69 层 KDA 与 24 层 Gated MLA，AttnRes，1M context |
| DeepSeek-V4-Pro | 1.6T / 49B | 61 层，384 个 experts，每 Token 选择 6 个，并有 1 个 shared expert；前 3 层采用报告声明的 hash routing | CSA/HCA 混合 attention、四流 mHC，1M context |
| DeepSeek-V4-Flash | 284B / 13B | 43 层，256 个 experts，每 Token 选择 6 个，并有 1 个 shared expert | 与 Pro 同属 V4 架构族的较小版本 |
| Qwen3.8-Max | 2.4T / 95B | 发布页将其归入 Qwen3.5 路线的 sparse-MoE 架构；截至本节日期，完整权重配置尚未公开 | Gated DeltaNet 与 full attention 的混合主干，1M context |

表中缩写是各模型官方材料中的架构名称。本节不依靠这些缩写的内部细节得出结论；真正相关的共同结构是：这些模型仍把绝大多数计算组织为规则的深度堆叠，每个 MoE 子层从较大的专家集合中选择少数专家，然后立即回到共同 hidden/residual stream。Attention、DeltaNet 或其他序列模块可以变化，但没有把一次专家选择扩展成长期存在、持续限制未来可达节点集合的一般局部 Graph 路径。

这说明前沿模型已经在实践中找到了下列容量与计算折中。设一个 MoE 子层有 $N$ 个大小相近的 routed experts，每个 expert 有 $p$ 个参数，每个 Token 激活 $k$ 个，其中 $k\ll N$。忽略 router、shared expert 和共同主干后，该子层的总参数量与每 Token 激活参数量分别为：

$$
P_{\mathrm{total}}\asymp Np,
\qquad
P_{\mathrm{active}}\asymp kp.
\tag{T-14.23}
$$

“容量扩充”指整个输入分布可以使用由 $N$ 个 expert 共同形成的函数族；“单个 expert 的语义贡献”指某个具体 Token 输出中该 expert residual 的影响大小。二者不是同一个量，因此不构成形式矛盾。MoE 不要求每个被选 expert 的贡献都很小；它依靠共同 residual stream、Top-K 加权、shared expert 或 dense 层、短生命周期 merge 和负载控制，把一次离散选择的风险限制在局部子层。该平衡已经被上述模型的训练与部署经验性证实，但没有由此得到“任意 MoE 都稳定”或“任意专家切换都只有小扰动”的定理。

这些模型没有改成 Tide 所设想的局部计算介质，至少有五个现实原因：

1. 规则 block、grouped GEMM、expert parallel 和 all-to-all 已有成熟 kernel、编译器和集群实现。
2. 每层重新开放完整 expert 候选集合，避免一次早期选择长期限制未来计算能力。
3. 立即 merge 给下一层提供固定宽度的公共接口，并把离散控制身份限制在一个子层内。
4. 全局 token 池更容易做容量分配和设备负载均衡；固定局部邻接则必须同时解决局部热点和信息混合。
5. 规则主干便于复用 checkpoint、训练配方和扩展规律；一般局部 Graph 同时改变优化、通信、状态所有权和 runtime。

这不是局部计算介质不可行的证据。它说明 Tide 主动放弃了 MoE 的部分成熟优势，以换取固定局部通信、长期本地参数/状态和组合式局部路径；因此 Tide 必须额外证明或实验验证局部路径确实带来收益，并把控制寿命、训练稳定性和硬件利用率限制在可接受范围内。

#### 14.20 MoE merge 后保留语义影响，但不保留显式路径身份

考虑 decoder-only 模型第 $\ell$ 个 MoE 子层和 Token 位置 $t$。令 $h_{\ell,t}$ 为 router 的输入表示，$A_{\ell,t}$ 为被选 expert 集合，$g_{\ell,j,t}$ 为 expert $j$ 的权重，$E_{\ell,j}$ 为其函数。省略归一化和其他公共分支后，固定 merge 可以写成：

$$
h_{\ell,t}^{+}
=
h_{\ell,t}
+
\sum_{j\in A_{\ell,t}}
g_{\ell,j,t}E_{\ell,j}(h_{\ell,t}).
\tag{T-14.24}
$$

下一层 router 读取由 $h_{\ell,t}^{+}$ 继续计算得到的公共表示。因此本层专家选择完全可能改变下一层 expert 集合：

$$
A_{\ell,t}
\longrightarrow
h_{\ell,t}^{+}
\longrightarrow
h_{\ell+1,t}
\longrightarrow
A_{\ell+1,t}.
\tag{T-14.25}
$$

若 $t_A<t_B$ 是两个 Token 位置，位置 $t_A$ 的 expert 输出还可以进入后续层为该位置形成的 K/V 或其他因果状态，再影响位置 $t_B$ 的表示和路由：

$$
A_{\ell,t_A}
\longrightarrow
h_{\ell,t_A}^{+}
\longrightarrow
\operatorname{Memory}_{\ell+1}(t_A)
\longrightarrow
h_{\ell+1,t_B}
\longrightarrow
A_{\ell+1,t_B}.
\tag{T-14.26}
$$

所以，“MoE 立即 merge”不表示早期专家选择的语义影响被删除。它仍会引起两类普通的长程影响：一类沿模型深度传播，另一类通过 causal Attention、SSM 或其他序列状态跨 Token 传播；它也可能使下游 router 的输入分布随 checkpoint 改变。

立即 merge 真正删除的是**显式控制路径身份**。式 T-14.24 输出的是共同向量，而不是“当前 Token 仍位于 expert $j$ 的私有子图”这一控制状态。下一层通常重新面对完整候选 expert 集合，不会因为上一层选了 $j$ 就在拓扑上只能访问 $j$ 的后继。因此应同时区分：

| 概念 | merge 后是否继续存在 |
| --- | --- |
| expert 产生的数值语义影响 | 可以继续存在，并可影响后续层和后续 Token |
| 当前 hidden vector 中可由后续网络利用的信息 | 继续存在，但已经进入共同表示 |
| “上一层选中了哪个 expert”这一显式 route artifact | 通常不作为下一层控制输入继续传递 |
| 由上一选择直接限定的未来可达节点集合 | 标准 block-local MoE 中不存在；下一层重新选择 |

由此也不能断言标准 MoE 与 Tide “拥有相同的信息量”。标准 MoE 的跨 Token 历史通常保存在公共 Attention K/V、SSM state 或 residual stream 中，expert 本身通常没有独立的单序列持久状态。Tide 可以给每个 node 配置独立的 KV/SSM/局部记忆；上游激活决定哪些 node 收到消息，后来的激活又决定何时读出这些状态。即使两者都满足 causal semantics，它们的状态分解、历史可见性和未来可达集合仍然不同。

若历史负载统计进一步进入 Tide selector，它还是标准 MoE 通常没有的额外控制状态。该状态可以用于序列内负载均衡，但必须成为单序列 reference semantics 的正式组成部分；它不能读取物理 batch 组成或实时设备负载，否则会破坏本部分第 4.3 节要求的 batch 与 chunk 不变性。

#### 14.21 从末级叶子稀疏到一般 Tide 的架构阶梯

为了避免从 dense Transformer 一步跳到长期不收拢的一般 Graph，应把候选架构分成四级。每一级都只在前一级上增加一种新的语义能力，并重新验证质量、训练、`prefill` 和系统收益。

**第 0 级：只有末级叶子稀疏。** 每个层级化分支结构中的所有非叶 node 都常亮，只有最末一级叶 node 可以被 selector 跳过；叶 node 输出立即进入固定 merge，随后返回共同 residual stream。若下一段重新开放全部末级叶候选、叶 node 不保留会在 merge 后改变未来可达集合的私有控制状态，则它在控制拓扑上等价于一个层级化、局部候选的 block-local MoE。这里的“等价”只指发散、稀疏选择、立即 merge 和候选集合重置的结构，不表示两个模型数值函数自动相等。

**第 1 级：有界的层级稀疏分支。** always-on backbone 和各级 hub 保持常亮，允许多个层级出现稀疏叶分支，但每个分支必须在声明的至多 $H$ 个 Graph 深度内进入 fixed merge。它比第 0 级允许更丰富的递归分支，同时仍给控制生命周期一个与 chunk 长度无关的上界。

**第 2 级：接收者门控的局部介质。** 某些非叶 node 也可以不激活；已激活 node 沿全部固定局部出边发送，所有实际收到消息的下游 node 都更新本地状态，但只有被 selector 激活的接收者执行昂贵计算并继续发送。对固定空间 DAG $G=(V,E)$，令 $M_{v,t}$ 为 node $v$ 在逻辑位置 $t$ 收到的有限消息多重集合，$I_{v,t}=\Gamma_v(M_{v,t})$ 为声明的确定性聚合结果，则一个最小 node transition 为：

$$
\widehat S_{v,t}
=
U_v(S_{v,t},I_{v,t}),
\qquad
a_{v,t}
=
A_v(\widehat S_{v,t},I_{v,t})
\in
\{0,1\}.
\tag{T-14.27}
$$

当 $a_{v,t}=1$ 时：

$$
y_{v,t}=F_v(\widehat S_{v,t},I_{v,t}),
\qquad
\forall w\in\operatorname{succ}(v),
\quad
m_{v\to w,t}=P_{v\to w}(y_{v,t}).
\tag{T-14.28}
$$

当 $a_{v,t}=0$ 时，式 T-14.27 的状态更新仍然保留，但不执行式 T-14.28 的昂贵计算和发送。若 $M_{v,t}=\varnothing$，状态保持、decay 或空步更新必须由模型另行声明，不能由 runtime 自行决定。

进入 reference semantics 的 node 状态应写成有限元组：

$$
S_{v,t}
=
\left(
S_{v,t}^{\mathrm{semantic}},
S_{v,t}^{\mathrm{load}}
\right).
\tag{T-14.29}
$$

$S^{\mathrm{semantic}}$ 包含 KV、SSM 或其他神经状态；$S^{\mathrm{load}}$ 包含进入 reference semantics 的单序列激活计数、恢复量或能量预算。实现还可以维护另一个 runtime 记录 $R_{v,t}$，用于队列、设备负载和物理调度，但 $R_{v,t}$ 不是 $S_{v,t}$ 的分量，也不能作为 $U_v$、$A_v$ 或 $F_v$ 的输入。式 T-14.27--T-14.29 使“状态更新”与“昂贵激活并继续传播”成为两个不同操作。它比 MoE 更强，因为未激活 node 可以保存以后才被读出的潜在语义影响。

**第 3 级：长期保持路径身份的一般 Tide。** 路由可以在多个局部区域和 Token 之间持续限制未来可达 node，node-local state 与路径历史共同改变后续路由，且没有较短的强制 merge 上界。这一级表达力最强，但路径分布漂移、跨 Token 信用分配、状态存储和 `prefill` 并行都最难；它不应作为第一个 checkpoint-growth 实验。

四级之间的关系不是“越一般越好”。第 0 级是最接近现有 checkpoint 和 MoE 训练经验的起点；第 1 级检验有界递归分支；第 2 级才检验 Tide 特有的 `Observe / Update` 与稀疏继续传播；第 3 级只有在前三级已经给出正面证据后才值得进入。

对第 2 级还必须把三种性能结论分开：

1. **语义正确性**：chunk 执行与逐 Token reference transition 产生相同 artifact。
2. **空间常数遍历**：固定有限空间 DAG 可以按拓扑序处理，每个 node 对整个 chunk 调用一次或固定次数，空间遍历次数不随 chunk 长度 $L$ 增长。
3. **node 内 Token 并行**：$U_v$、$A_v$ 和 $F_v$ 具有 causal bulk、scan 或其他可批量代数结构，从而不在 node 内逐 Token 串行。

若每个 node 等待所有前驱产生完整 inbox，按逻辑时间排序并确定性处理，只读取自己的左边界状态、当前 inbox、静态参数和上游结果，那么固定空间 DAG 可以获得前两项。任意 stateful selector 仍可能迫使 node 内按 Token 顺序执行，因此前两项不自动推出第三项。该区分允许第一版先接受 CPU 侧局部顺序 selector，同时保留以后把 Attention、SSM、FFN 和可组合 selector lowering 成批量 kernel 的空间。

#### 14.22 信用分配中的三种距离

“更长距离的信用分配”不是指 node 在欧氏空间中相距更远。令一次有限前向执行展开成事件 DAG $\mathcal D=(\mathcal E,\mathcal A)$，其中 $\mathcal E$ 是有限事件集合，$\mathcal A\subseteq\mathcal E\times\mathcal E$ 是直接依赖边集合。若

$$
p=(e_0,e_1,\ldots,e_n)
$$

满足 $(e_i,e_{i+1})\in\mathcal A$，则称 $p$ 为从 $e_0$ 到 $e_n$ 的一条依赖路径，其长度为边数 $n$。一个早期选择事件到最终 loss 事件之间可能有多条路径；残差 backbone 可以提供短路径，状态递推和稀疏分支则可能产生长路径。

为了说明数值梯度，再额外假设每个事件 $e_i$ 产生一个实数 $z_i$，存在可微函数 $f_i$ 使 $z_{i+1}=f_i(z_i)$，并且最终 loss 为可微函数 $\mathcal L(z_n)$。在只有这一条数值依赖链的简化情形，反向信用包含导数连乘：

$$
\frac{\mathrm d\mathcal L}{\mathrm d z_0}
=
\frac{\mathrm d\mathcal L}{\mathrm d z_n}
\prod_{i=0}^{n-1}
f_i'(z_i).
\tag{T-14.30}
$$

向量值事件把普通导数替换成 Jacobian；一般 DAG 中还要在汇合处对来自不同后继的反向贡献求和。式 T-14.30 只用于说明路径长度为何会影响数值梯度；它不是梯度必然衰减的定理。若某条边来自 hard Top-K 索引，该离散选择本身通常没有普通意义下的导数，还会叠加 selected-only feedback，而不只是导数连乘问题。事件边数还取决于预先选择的事件分解粒度，因此只有在固定同一 reference event schema 后，才能用它比较两个架构。

对 Tide 至少应分别记录三种结构距离：

| 距离 | 含义 | MoE 与 Tide 的主要差别 |
| --- | --- | --- |
| 数值语义距离 | 某个中间数值贡献到最终 loss 所经过的 event 边数 | 深层 Transformer、MoE 和 Tide 都可能很长 |
| 控制寿命 | 一次离散选择仍保持独立路径身份、限制未来候选集合的 Graph 深度 | block-local MoE 通常到本子层 merge 为止；Tide 可以跨多个切片 |
| 状态读写延迟 | 某个 Token 写入 node 状态，到后续 Token 真正读出该影响之间的位置差 | 标准无独立 expert state 的 MoE 没有这条额外 node-local 链；有状态 Tide 可以很长 |

以两个 Token 位置 $t_A<t_B$ 为例，若 $u$ 在位置 $t_A$ 激活并向 $v$ 发送，$v$ 当时只更新状态，直到位置 $t_B$ 才激活并读出，则存在依赖链：

$$
a_{u,t_A}
\longrightarrow
m_{u\to v,t_A}
\longrightarrow
S_{v,t_A}^{+}
\longrightarrow
S_{v,t_A+1}
\longrightarrow
\cdots
\longrightarrow
S_{v,t_B}
\longrightarrow
a_{v,t_B}
\longrightarrow
y_{v,t_B}
\longrightarrow
\mathcal L.
\tag{T-14.31}
$$

这里最终训练信号必须区分：位置 $t_A$ 的发送是否有用、$v$ 的哪次状态更新有用、位置 $t_B$ 的激活是否有用，以及中间其他消息对 $S_{v,t_B}$ 各贡献多少。如果训练采用截断反向传播，式 T-14.31 的早期部分还可能根本收不到该 loss；如果 selector 是 hard 的，激活决策又需要 estimator、soft/shadow route 或其他训练机制。

因此，“Tide 比 MoE 有更长的信用分配”只能作如下有条件陈述：

| 架构级别 | 是否必然比标准 MoE 更长 |
| --- | --- |
| 第 0 级末级叶子稀疏并立即 merge | 不必然；控制寿命与 block-local MoE 接近 |
| 第 1 级有界层级分支 | 可能更长，但由声明常数 $H$ 限制 |
| 第 2 级接收者门控且以后读出 node state | 通常新增跨 Graph 和跨 Token 的信用链，可能明显更长 |
| 第 3 级长期路径与状态耦合 | 可以随 Graph 深度或 chunk 长度增长；对每个有限 chunk 仍是有限链，但不再有与 $L$ 无关的统一小上界 |

“收到消息总是更新状态”可以减少 node 完全看不到数据的激活饥饿，却不自动解决信用分配。一个长期未激活的 node 即使持续写入状态，也可能直到很晚才通过输出影响 loss；此时梯度只是从“是否写入”问题变成了“哪次写入在以后有用”的延迟归因问题。always-on backbone、频繁 fixed merge、显式限制分支寿命和状态读写延迟、merge-local auxiliary loss，以及从第 0 级逐步增长，分别提供短梯度路径或缩短特定信用链，但都不能单独证明非凸训练必然稳定。

### 15. 主要参考

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
- GLM-5.2: [Official Repository and Release Notes](https://github.com/zai-org/GLM-5)
- Kimi K3: [Official Repository and Technical Report](https://github.com/MoonshotAI/Kimi-K3)
- DeepSeek-V4: [Transparency Center](https://www.deepseek.com/transparency/) and [Technical Report](https://arxiv.org/abs/2606.19348)
- Qwen3.8: [Official Release Blog](https://qwen.ai/blog?id=qwen3.8)
- Gerstner et al.: [Eligibility Traces and Plasticity on Behavioral Time Scales](https://doi.org/10.3389/fncir.2018.00053)
- Lillicrap et al.: [Backpropagation and the Brain](https://doi.org/10.1038/s41583-020-0277-3)
- Turrigiano: [Homeostatic Synaptic Plasticity](https://doi.org/10.1101/cshperspect.a005736)

---

## 第四部分：执行能力与成本模型

> [!important] 本部分的证据层级
> 本部分同时使用三种不同强度的陈述，后文不得互相替代：
>
> - **已证明的语义或复杂度结论**必须给出明确前提，并链接到证明或可检查的等价证书。
> - **架构设计目标**规定 Tide 希望满足的 contract、gate 和成本账本；它本身不是“某个实现已经达标”的定理。
> - **经验假设**包括 learning value、训练稳定性、硬件利用率和 scaling behavior，只能由实验与测量支持。

### 1. Tide 的进一步设计目标

前面的讨论可以收敛为一个比“让一般 Graph 支持 prefill”更严格的目标：

> 给定有限 chunk，先生成语义完整的 reference event DAG；再把其中满足特定代数或依赖性质的区域，替换为经过等价性证明的并行 chunk operator，使最终 execution DAG 同时保持局部通信、超稀疏、correctness 和较低 span。

这里不要求整个 Graph 都能 scan。不同 node 或 subgraph 可以依靠不同理由获得并行性；无法并行化的区域仍可顺序执行，但必须显式暴露其 span 成本。

#### 1.1 Reference event DAG

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

#### 1.2 Certified contraction 与 execution DAG

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

#### 1.3 高性能有限前缀执行的四道 gate

下面四道 gate 是本项目采用的**设计审查框架**，不是一个已经证明为必要且充分的分类定理：

| Gate | 要回答的问题 | 所需证据 |
| --- | --- | --- |
| Semantic gate | chunk/window 执行是否保持 reference streaming semantics | event dependency、窗口组合律、完整 artifact 与 continuation equality |
| Progress gate | 对声明支持的 sealed finite cut，执行是否在有限工作后返回 | bounded rounds、良基秩、guarded delay、有限格、或带终止条件的 solver certificate |
| Parallel-complexity gate | 在问题规模增长时，work、span、memory 与 communication 是否可接受 | 显式 execution DAG、复杂度推导、fallback critical path 与资源账本 |
| Hardware-lowering gate | 上述算法能否映射成目标设备上规则且高利用率的实现 | 具体 kernel/layout、端到端 profiling、吞吐、延迟、显存与通信测量 |

Semantic gate 和 Progress gate 主要决定“声明的有限前缀结果是否精确且可返回”；Parallel-complexity gate 与 Hardware-lowering gate 才进一步决定它是否能称为高性能。低理论 span 不推出 GPU/NPU 上的高利用率；反过来，把逐位置串行循环融合进一个 kernel 也不会消除逻辑 span。

通过某一道 gate 的结论必须限定作用域。例如“某个固定 $K$ 的 family 总会终止”属于带前提的 progress 结论；“某个 packed sparse kernel 在 Ascend 上更快”属于特定 shape、dtype、layout 和设备上的经验测量，不能提升为 graph family 的数学定理。

### 2. 五类 Execution Capability

这些 capability 是 sub-DAG 的 lowering contract，不是没有验证义务的提示标签。

| Capability | 语义条件 | 主要并行方式 | 典型例子 |
| --- | --- | --- | --- |
| `token-local` | token 之间没有 mutable temporal dependency | batch / map | FFN、Norm、projection、token-local router |
| `scan-composable` | transition 有紧凑且封闭的 associative summary | parallel prefix scan | Mamba/SSM、affine recurrence |
| `causal-bulk` | 存在已证明等价的 causal chunk operator | attention/conv 等专用 bulk kernel | causal attention、causal convolution |
| `ready-set-local` | 同一就绪事件集合内没有相互依赖或可见写冲突 | wavefront packing | message-passing round、MoE routing |
| `sequential-fallback` | 尚无可用的并行等价 lowering | exact sequential execution | 当前 LH persistent selector |

> [!important] SCC 是认证边界，不是第六种 capability
> `certified SCC` 表示一个多节点循环区域具有明确的 boundary transfer、continuation，以及所声明的 semantic/progress/cost/lowering 证书。它回答“认证和封装的作用域是什么”，不回答“内部怎样并行”。SCC 内部及其边界 lowering 仍须分解为本节已有的五类 capability：例如 fixed-round 展开可使用 `token-local` 与 `ready-set-local`，仿射 recurrence 可使用 `scan-composable`，专用窗口算子可使用 `causal-bulk`，尚无并行证书的迭代则进入 `sequential-fallback`。仅把任意困难循环包成宏节点，不能获得新的性能结论。

#### 2.1 Token-local

若对所有输入位置 $t$：

$$
z_t=f(x_t;\theta),
$$

并且 $f$ 不读取由其他输入位置在本 region 内更新的 mutable state，则所有 $z_t$ 可以并行计算。

`token-local` 描述输入位置之间的依赖性质，不是消息 `owner` 的同义词，也不要求所有输入位置采用同一路径。MoE router 可以根据每个位置的 hidden state 动态选择不同 expert，只要同层各位置的 routing decisions 不通过 mutable selector state 相互影响。

#### 2.2 Scan-composable

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

#### 2.3 Causal-bulk

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

#### 2.4 Ready-set-local

在事件 DAG 中，称事件集合 $F_k$ 为一个就绪集合，当且仅当其中每个事件在该调度点的全部前驱均已完成。若 $F_k$ 中任意两个事件：

- 不读取对方尚未提交的 state。
- 不通过 mutable control state 改变对方的 routing decision。
- 不发生未定义顺序的 conflicting writes。

则该就绪集合可以并行执行并按计算核角色打包，称相应区域满足 `ready-set-local`。

`layer-local` 是 `ready-set-local` 在规则 Transformer chain 中的特殊情况。一般 Tide Graph 未必具有 layer；它可能按图距离、内部轮次，或者 $(t,r)$ 的反对角线形成 wavefront。

这里的 wavefront 只是调度术语：它表示按依赖关系连续推进的一系列就绪集合，不是消息、持久状态，也不是 `causal input frontier` 或 `progress frontier` 字段。

Phase 与就绪集合也不相同。Phase 定义大范围的 barrier、visibility 与 commit order；就绪集合是在满足这些约束后，由实际事件依赖与当前执行进度共同确定的可调度集合。它不是消息的 `causal input frontier`。

#### 2.5 Sequential fallback

任意无法归入前述类别的 reference region，仍可以由 exact interpreter 或 fused sequential kernel 执行。这保证了 Tide 表达能力，但不能把 kernel fusion 误报成 sequence parallelism。

若一个 fallback region 的 span 随 chunk 长度 $L$ 线性增长，并且位于全局 critical path 上，它就可能决定整个模型的 prefill 上限。当前 persistent LH selector 是主要候选。

### 3. Capability Contract

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

### 4. 适合 Tide 的 Graph 约束

一个有希望成为 `prefill-native` 的局部通信、超稀疏 Graph，应优先满足以下设计约束。

#### 4.1 Sparse work

令 $A_{t,r}$ 是 token $t$、round $r$ 的 active event set。总 work 应主要与：

$$
\sum_{t=0}^{L-1}\sum_{r=0}^{R-1}|A_{t,r}|
$$

及实际 active edges 数量相关，而不是与 $L\,R\,|V|$ 相关。运行时不能通过“执行全部 node 再 mask”隐藏地失去超稀疏性，除非它作为明确的小规模 fallback。

#### 4.2 Explicit state ownership

多个 events 对同一 state location 的写入只允许几种可判定形式：

- single-writer / exclusive ownership。
- associative reduction。
- 显式 versioned ordered writes。
- 进入 sequential fallback。

否则，Graph 虽然可以动态执行，但 chunk lowering 无法确定 visibility 与 commit semantics。

#### 4.3 Prefill-capable temporal state

跨输入位置状态应尽量由 `scan-composable` 或 `causal-bulk` 计算核承载。对于只在部分输入位置收到消息并实例化事件的空间节点，可以把该节点的事件压成按逻辑时间排序的稀疏事件序列，再执行 segmented scan 或 packed causal kernel。

如果 state transition 包含时间间隔，计算核需要显式接收输入位置、逻辑轮次或时间间隔 $\Delta t$。例如固定 decay 可以把没有节点事件的区间折叠为 $A^{\Delta t}$，而不是逐输入位置执行空操作。

#### 4.4 Ready-set-local routing

Router 应优先读取当前事件输入和已提交前驱状态。它不应在同一就绪集合内用一个全局可变计数器逐项更新其他输入位置的选择优先级。

可接受的 routing 形式包括：

- token-local top-k。
- 基于上一就绪集合边界快照的 routing。
- scan-composable controller state。
- speculation + validation + replay。

当前 LH selector 可以保留为机制样本和 correctness fallback，但不应默认成为 Tide 高性能 profile 的必要组成。

#### 4.5 Explicit fallback tax

每个 sequential fallback 都要进入 span report。若 runtime 只是把多个逻辑 tick pack 到一个 kernel 内顺序执行，work 和 launch overhead 可能改善，但 logical span 没有被消除。

### 5. Work、Span 与通信的联合目标

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

#### 5.1 语义与进展能力轴

语义正确、有限前缀能否返回、以及有限输入后是否整体静止，是与性能不同的一条轴。每个模型或 SCC family 应分别声明它支持到哪一层：

| 等级 | Contract | 不自动保证 |
| --- | --- | --- |
| `stream-step-exact` | 每个已执行 step/event 的状态、消息、route、commit 与 readout 符合确定的 reference semantics | 任意 sealed finite cut 都能在有限时间推进完成 |
| `finite-cut-total` | 在 `stream-step-exact` 基础上，对声明输入域中的每个合法 sealed finite cut，`AdvanceUntil(cut)` 在有限工作后返回完整 artifacts、continuation 与 sound progress certificate | 有限输入引发的所有未来内部活动最终静止 |
| `quiescence-total` | 在声明输入域中，有限且已 seal 的外部输入所引发的全部内部工作最终静止，`RunToQuiescence` 在有限工作后返回 | 低 span、低 work 或高效硬件实现 |

`quiescence-total` 是比“可以不断完成有限 cut”更强的 settling 要求；长期运行但 finite-prefix productive 的流处理可以是 `finite-cut-total` 而非 `quiescence-total`。对只定义了单步 transition、却没有 finite-cut productivity 证明的开放循环，只能声明 `stream-step-exact` 或 experimental/best-effort 范围，不能把“跑了一段时间”报告成 total prefill。

这些标签本身是 contract 名称。只有相应证明、验证或受限输入域证书齐全时，“某个 family 达到该等级”才是可接受的结论。

#### 5.2 Sequence-bulk 性能轴

在独立的性能轴上，可以保留三个运行等级：

| 等级 | 定义 |
| --- | --- |
| `prefill-native` | 所有随 $L$ 增长的主要依赖链都能由 batch、scan、bulk 或 wavefront contraction 处理 |
| `prefill-compatible` | chunk correctness 成立，但仍残留少量随 $L$ 增长的 sequential span |
| `decode-only` | 关键路径基本随 token 数线性增长，chunk 主要只是 fused sequential execution |

这三个标签必须附带 $W,D,C$、memory、shape 与 backend witness。`decode-only` 是 sequence-bulk 性能判断，不是否定 chunk correctness：一个 `finite-cut-total × decode-only` 的实现可以精确返回有限前缀，只是主要沿 token 轴顺序执行。类似地，`stream-step-exact` 也不能推出 `decode-only`；某个 streaming semantics 可能另有经过证明的 native chunk lowering。

#### 5.3 Tide-Prefill 与 Tide-Streaming 是正交组合 profile

`Tide-Prefill` 和 `Tide-Streaming` 不增加第三、第四条战略设计路线。第一部分的 Graph 收缩线与 checkpoint 生长线回答“候选架构从哪里来、怎样演化”；这里的 profile 回答“同一个候选在语义/进展轴与 sequence-bulk 性能轴上承诺什么”。

建议把一次 profile 声明写成显式元组：

$$
\operatorname{Profile}
=
(\text{semantic/progress level},
 \text{sequence-bulk level},
 \text{backend/evidence scope}).
$$

- `Tide-Streaming` 以 `stream-step-exact` 为语义基础，并必须明确它是否进一步达到 `finite-cut-total` 或 `quiescence-total`；严格/production profile 对其声明支持的 cuts 要求 `finite-cut-total`，只有单步正确性而没有 finite-cut progress certificate 的开放 Graph 应标为 `Tide-Streaming-Experimental`。它不承诺通用低 token-axis span，但仍可使用 batch、空间并行、ready-set packing 和 pipeline。
- `Tide-Prefill` 至少要求 `finite-cut-total` 以及 prefill 后可精确接续 streaming 的 continuation equality；再以 `prefill-native` 作为高性能目标，`prefill-compatible` 作为明确标税的中间态。若只能 `decode-only`，它可以是 exact prefill reference，却不能称为高性能 Tide-Prefill。

二者不是互斥集合。一个 `finite-cut-total × prefill-native` 模型既能以 streaming reference 运行，也满足高性能 prefill profile；一个探索性开放 Graph 则可能只有 `stream-step-exact × decode-only`。SCC certification 只为这个元组提供局部证据，不形成第三条坐标。

### 6. 若干结构化模型如何落入该设计

#### 6.1 GPT-style Transformer

- Norm、projection、FFN 和 residual arithmetic 是 `token-local`。
- causal self-attention 是 `causal-bulk`。
- block chain 仍按深度顺序执行，但它的 token-axis 不需要退回逐 token loop。

因此，模型 span 主要随 block depth 增长，而不是随 `block depth × token count` 增长。

#### 6.2 Mamba/SSM

- input projection、gate 和多数 pointwise operator 是 `token-local`。
- selective recurrent state 是 `scan-composable`。
- local convolution 可以是 `causal-bulk` 或专门的 scan/bulk lowering。

#### 6.3 Dynamic sparse Tide Graph

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

#### 6.4 固定 $K$ 轮 GNN / message passing

**结构性结论（带前提）**：若空间图有限、每轮只读取前一轮已提交状态、每个节点和边在一轮内产生有限事件，并且 $K$ 是预先给定的有限值，那么把 round 写入逻辑秩后，$K$ 轮执行可以静态展开为有限 event DAG。原始空间 schema 即使含环，也不会因此产生开放的同刻循环。

这仍不产生新的 execution capability。典型 lowering 是：

- 同一 round 的独立 edge/node events 使用 `ready-set-local`。
- node update 与 per-message transform 在没有跨位置 mutable dependency 时使用 `token-local`。
- inbox 若具有已声明的 associative merge，则使用 reduction；否则必须保留 ordered semantics。
- round 之间的深度至少反映 $K$ 个依赖阶段，除非另有经过证明的跨 round contraction。

固定 $K$ 给出 bounded-unroll 的 progress certificate，不自动给出 `prefill-native`：不规则图布局、聚合热点和跨设备通信仍要通过复杂度与硬件 gate；若另一个 model family 允许 $K$ 随问题规模增长，还必须把这种增长计入 span。它也不构成“GNN 机制具有 learning value”的证据，后者仍是经验问题。

#### 6.5 DEQ / implicit layer

DEQ 更适合被建模为显式 solver-wrapped zero-delay SCC，而不是对环内节点做一次任意拓扑遍历。这里有三项必须分别声明：

1. **Semantic contract**：reference result 是精确固定点，还是由具体 solver、容差、最大迭代数和失败值共同定义的数值结果。
2. **Progress contract**：收缩映射、单调有限格、受限输入域收敛证明，或语义内的 bounded iteration；“训练时通常收敛”只是经验观察。
3. **Execution contract**：每次迭代内部继续使用现有五类 capability；迭代链若无额外 contraction，仍是 `sequential-fallback`。把 solver 封装成 SCC 不会隐藏其 work、span 和 memory。

若改变容差、提前停止规则或近似 solver 会改变 reference artifact，就应把它记录为模型/语义变换，而不是 exact lowering。Implicit differentiation 还需要独立的 backward correctness、conditioning 和成本证据；forward fixed-point certificate 本身不证明这些性质，也不证明 DEQ 相对基线的 learning value。

### 7. 推荐的架构分层

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

### 8. Learning value 与 compute-matched 实验

#### 8.1 两类风险必须分开

> [!warning] 研究优先级判断，不是定理
> Tide 当前的**首要科学风险**是 learning value：局部通信、持久状态、feedback 和动态 routing 是否能被稳定学到，并在能力或泛化上带来相对强基线的可重复收益。首要**规模化风险**是 sequence-level bulk execution：若长序列 forward/backward 只能沿 token 轴串行，可承担的模型、数据、上下文、随机种子和消融数量都会下降。前者不能由并行计算理论证明，后者也不能仅凭小规模 kernel microbenchmark 排除。

Learning value 至少要拆成下列可否证问题：

1. **Optimization**：训练是否稳定，梯度、信用分配、route load 与 state dynamics 是否健康。
2. **Mechanism use**：模型是否真的使用目标 feedback/state/routing，而不是退化为更简单的近似架构。
3. **Capability and generalization**：是否改善明确任务能力、长度泛化、组合泛化或分布外行为。
4. **Efficiency-normalized value**：在匹配训练资源后，优势是否仍存在。
5. **Scaling behavior**：收益能否随模型、数据与上下文扩大。

“函数类表达力更强”不推出可学习性；一次训练 loss 更低也不推出更好的泛化。相反，实验失败也可能来自 sequence-bulk 受限造成的训练不足，而不是机制本身没有 learning value。Teacher forcing 只提前给出外部 token，不会自动删除模型内部真实的状态、反馈或 routing 依赖。

#### 8.2 Compute-matched 比较套件

Compute-matched evaluation 是**实验设计要求**，不是质量相等或公平性的数学定理。参数、token、FLOPs、显存、能耗和墙钟通常无法在同一对实验里全部同时严格匹配，因此应报告一组互补比较，而不是挑选唯一有利口径：

| 比较视角 | 固定或对齐 | 主要回答 |
| --- | --- | --- |
| Capacity-matched | 总参数、激活参数、宽深等主要容量变量 | 收益是否只来自更多参数或更大 active compute |
| Data-matched | 训练 token、数据顺序/分布与上下文课程 | 在相同数据暴露下是否更有效 |
| FLOP-matched | 可审计的 forward+backward 训练 FLOPs | 在相近算术预算下是否有质量收益 |
| Resource-matched | device-hours 或墙钟，并同时报告峰值显存与能耗 | 在现实实验预算下是否可兑现 |
| Quality-matched | 达到同一验证质量或任务阈值 | 达标所需 token、FLOPs、时间与推理成本 |

每组核心实验至少还应：

- 使用多个随机种子并报告方差或置信区间。
- 给基线与 Tide 候选合理且可审计的调参预算。
- 同时报训练曲线、稳定性、吞吐、峰值显存、通信和长上下文成本。
- 做机制消融与 counterfactual probe，例如冻结/清零长期状态、约束反馈、替换 learned route、缩短迭代次数，确认目标机制确实承担收益。
- 分开报告 in-distribution quality、长度/组合泛化和 scaling trend，避免用单一 benchmark 汇总 learning value。

#### 8.3 阶段性投入规则

一个保守的**研究策略**是先用 `stream-step-exact` reference 和可承受的小规模实验否证 learning hypothesis；出现可重复机制信号后，再投入 ragged batching、SCC 专用 lowering 和多设备 runtime，并尝试把有效机制约束为 bounded、scan-composable 或 causal-bulk family。若约束、蒸馏或近似改变 reference semantics，它是新的模型变换，必须重新比较 quality 与 continuation，而不能记作原模型的 exact optimization。

这套策略不预设 Tide-Prefill 或 Tide-Streaming 最终更优。它只要求每次研究声明同时给出：科学假设、语义/进展等级、sequence-bulk 等级、计算预算和证据状态。
