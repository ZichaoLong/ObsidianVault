---
type: mathematical-model-instances
status: active
cssclasses:
  - textbook-math
tags:
  - tide
  - mathematics
  - instances
  - weighted-message
  - hb-lattice
---

# HB-Lattice 上的带权消息实例

本文在 [HB-Lattice 拓扑](../topologies/hb-lattice.md)上绑定[共同局部架构](../local-semantics/weighted-message/architecture-learning-note.md)，给出 KV、稠密发送与混合记忆实例。候选传播、发送强度和计算量由图与所选函数共同决定；[全连接分层实例](fully-connected-layered-weighted-message.md)提供另一种拓扑下的组合。

## 1. 采用的定义与参数

### 1.1 图与局部选择

取拓扑定义中的 $b,h,n,N$、区域关系 $\mathcal H_\ell$ 与偏移集 $\mathcal D_\ell$，沿用节点、区域、边 $e_{\ell,\omega,\omega',s,a}$、端口及日程，$L=2h+1,D=L+2$。全部实例在一次运行中保持空间图和时间。

以下定义一族 KV 基线，记忆描述和区域评分允许逐区域选择。表中的函数由共同架构及模块教材给定。

| 对象 | 基线固定的选择 | 仍需给定的参数及范围 |
|---|---|---|
| 图与时间 | 本节的 HB-Lattice 拓扑 | 全图的 $b,h,n,N$；逐层固定的区域关系与横向偏移集 |
| 载荷与聚合 | $P=X_v=\mathbb R^{1+d}$，区域共享 Agg | 全图宽度 $d$；逐区域的聚合参数，来源映射见 §2.1 |
| 记忆与内容 | KV 空缓存初态、KV 内容函数 | 逐区域的状态宽度与共享基座；逐节点的适配器、摘要、检索与 Full 参数 |
| 描述与选择 | Read$^+$、拼接局部评分、固定增益、约束 quad | 逐区域选择时间摘要或内容检索、独立或区域 Attention 评分；逐节点评分参数及固定增益；逐区域 $k_j,\eta_j,\tau_{\mathrm{sel},j}$，$1\le k_j\le n$；增益满足共同有限上界 |
| 状态采用与发送 | 全部候选保留更新、单点区域历史、广播 Full、$K_j=n$ | 使用共同 Next，无额外状态采用参数 |
| 窗口与位置 | §1.2 的位置尺度与衰减换算 | 逐区域的窗口、短期衰减、Read 与 Full 旋转参数 |
| 外部边界 | §2.2 的单位入口和残差读出 | 内容序列 $h_t$、读出矩阵与尺度 |

§2.3 给出其中一个七层组合；§2.5 替换发送函数；§3 替换中间层记忆及其描述、内容函数。所有尺寸、矩阵、偏置和标量参数在一次绑定中固定。相连节点使用相同载荷宽度，描述与评分按共同架构 §5 检查相容性。每个完整参数取值确定一个模型。

### 1.2 KV 的位置、窗口与衰减

对第 $\ell$ 层节点取

$$
\operatorname{Pos}_{v_{\ell,\omega,s}}(\theta)=\frac{\theta-\ell}{D},
\qquad \operatorname{Pos}_{v_{\ell,\omega,s}}(Dt+\ell)=t.
\tag{1}
$$

为每区域 $j$ 声明 $H_j\in\mathbb N_{\ge1}\cup\{\infty\}$，取 $T_v=DH_j$。位置 $t'$ 写入的条目在位置 $t$ 可读，当且仅当 $0\le D(t-t')<T_v$；窗口覆盖最近 $H_j$ 个输入位置或全部接收历史。短期摘要率取 $\beta_{v,\mathrm{short}}=\bar\beta_{j,\mathrm{short}}/D$，其中 $\bar\beta_{j,\mathrm{short}}>0$，长期率为零。Read 与 Full 的旋转维数及频率分别声明，均使用式 (1) 的位置坐标。稀疏写入和分段继续保留原始时间。

## 2. KV 基线与发送变式

本节固定一份 KV 组合，函数分别沿用[共同架构](../local-semantics/weighted-message/architecture-learning-note.md)、[区域分配](../local-semantics/weighted-message/region-allocation-learning-note.md)与 [KV 模块](../local-semantics/weighted-message/kv-memory-learning-note.md)。拓扑和时间使用 §1.1 的声明。

### 2.1 基线与来源

采用 §1.1 的 KV 基线，各参数取有限值，形状依照被引用函数的定义。区域 Attention 只汇集本区域同一逻辑时间的完整候选，消息沿[拓扑定义的边](../topologies/hb-lattice.md#2-相邻层邻域)传播。

替换发送函数时，沿用区域分配教材的完整定义及容量对应；替换记忆时按共同架构 §5 检查描述和参数形状。配置对应见附录 S。

输入来源类别为 $\mathrm{in}$。对每条边 $e:v\to v'$，令

$$
\operatorname{SrcClass}_{v'}(\mathrm{msg},e)=v,
\qquad
\operatorname{SrcClass}_{v_{1,\varnothing,s}}(\mathrm{ext},i_s)=\mathrm{in}.
\tag{2}
$$

每个接收区域的类别集为其全部潜在父节点身份，第一层加入口类别。该映射覆盖全部原子标签，消息仍保留原始边身份与时间。不同节点的入邻域通常不同，共享 Agg 参数也会得到不同的内容与历史。

### 2.2 输入、读出与任务

给定只依赖输入前缀的 $h_t\in\mathbb R^d$，在所有入口注入 $x_{i_s}(t)=(1,h_t)$。固定输出槽

$$
\begin{aligned}
\Lambda_t&=\{(Dt+L,o_s):s\in\mathbb Z_n\},\\
O_t&=\operatorname{ReadOut}_{\Lambda_t}(Z),\qquad
 y_t=h_t+\alpha_{\mathrm{out}}W_{\mathrm{out}}O_t,
\end{aligned}
\tag{3}
$$

其中 ReadOut 为局部架构教材的 ReadOut，$W_{\mathrm{out}}\in\mathbb R^{d\times d}$、$\alpha_{\mathrm{out}}\ge0$。在 $Dt+L+1$ 比较已经确定的输出槽。通用 ReadOut 对全部终端缺席取零；本实例每位置均有正强度终端输出，见 §2.4，内容相消仍可使 $O_t=0$。读出发生在图外。独立语言模型可用 token 嵌入作为 $h_t$，以 $y_t$ 接任务读出。

### 2.3 一个可直接配置的形状

采用[拓扑 §4 的七层形状](../topologies/hb-lattice.md#4-图规模)：$b=2,h=3,n=64$，$\mathcal H_\ell=\mathcal H_\ell^0$，$\mathcal D_\ell=\{0,1\}$。连接更丰富的比较形状取偏移 $\{0,1,2,3\}$。

一组配置形状可取 $d=512,H_{\mathrm{att}}=8,d_h=64,p_a=d_s=d_r=d_{\mathrm{sel}}=r_a=32,d_f=2048$，各区域 $k_j=2$，Agg 取区域共享，局部评分、增益和预算正则取 cat、fixed、quad。记忆与区域评分按下表选择：

| 层 | 记忆与评分 | $H_j$ | Full 旋转 | Read 旋转 |
|---|---|---|---|---|
| $1,2,3$ | $\mathrm{qry},\mathrm{att}$ | $512$ | 每头完整 $64$ 维 | $d_s=32$ 维全部旋转 |
| $4$ | $\mathrm{sum},\mathrm{ind}$ | $\infty$ | NoPE | 时间摘要无需检索旋转 |
| $5,6,7$ | $\mathrm{sum},\mathrm{att}$ | $512$ | 每头部分 $32$ 维 | 时间摘要无需检索旋转 |

对所有旋转族取基数 $10^4$、频率 $(10^4)^{-2(a-1)/d^{\mathrm{rot}}}$，其中 $1\le a\le d^{\mathrm{rot}}/2$；Full 的距离偏置取零。其余标量和矩阵由配置给出。这个形状在展开侧采用内容检索与区域匹配，中间层保留全历史，收拢侧采用摘要与区域匹配；也可逐区域代入已定义的其他组合。

### 2.4 区域到达与节点稀疏

[拓扑的邻域定义](../topologies/hb-lattice.md#2-相邻层邻域)使源区域的每个节点都连向每个相连目标区域，且 $\mathcal D_\ell$ 非空。因此一个区域只要有正强度发送，每个相连目标区域就都有有效候选。第一层收到单位输入，非空选择沿递归区域连接传播，故每个输入位置的所有区域均有节点接收并激活，终端输出存在。

若全图各区域均采用区域分配教材的约束分配，还满足每区发送强度之和至少为 $1$。第一层有 $M_j=n$；若某父区域发送强度之和至少为 $1$，相连目标区域所有节点的接收强度之和至少为 $1$，并有

$$
M_j=\sum_{v\in\mathcal R_j}\min(1,\gamma_v r_v^{\mathrm{in}})
\ge\min\left(1,\sum_{v\in\mathcal R_j}r_v^{\mathrm{in}}\right)=1,
$$

其中未接收节点按 $r_v^{\mathrm{in}}=0$ 计。总和下限于是为 $1$，逐层归纳成立。全图各区域均用硬选择时，从单位输入出发，每条实际消息强度均为 $1$，每区非空选择同样保证发送强度之和至少为 $1$。采用固定总强度 Attention 的区域，只要有正接收候选便发送总强度 $1$；直接 Attention 及混合选择继续保证每区有正发送，其总强度按各自公式确定。

区域内的候选可只占一小部分，具体节点随上游选择与邻域变化；正温度运行中各节点的接收强度和写入权重可小于 $1$，缓存长度也可不同。全图采用约束分配时，单节点弱接收与区域 $M_j\ge1$ 可以同时成立，区域内可调整的分配范围由区域分配教材 §2.1 与 §4.1 判断。每个区域至少保留一个激活节点，给出上述广播与非空选择组合的 Full 成本下限。

若全部区域在正温度使用固定总强度 Attention、直接 Attention、区域总量分配、按比例分配、bern 或 ent 的 $\alpha=1$，第一层全部节点都发送，零偏移边让下一层全部节点都有正接收，归纳得到全图所有节点均激活；消息仍只沿既定 HB 边传播。quad 与 ent 的 $\alpha>1$ 可以在正温度通过精确零减少这里的激活数量。各选择函数的写入仍按实际 $w(r^{\mathrm{in}})$；发送强度另由所选函数决定。

<a id="25-直接-attention-的强度传播"></a>

### 2.5 稠密发送的强度传播

直接 Attention 的总发送强度是各候选上限的加权平均。取 $b=2,h=1,n=4$、$\mathcal H_\ell=\mathcal H_\ell^0$、$\mathcal D_\ell=\{0\}$，各层区域数为 $1,2,1$。全图采用直接 Attention、固定增益 $\gamma=1$，令每区域各候选评分相等。单位入口给出：

| 层 | 每节点接收强度及上限 $r_v^{\mathrm{in}}=\mu_v$ | 每节点发送强度 $c_v$ | 每区域总发送强度 |
|---|---|---|---|
| $1$ | $1$ | $1/4$ | $1$ |
| $2$ | $1/4$ | $1/16$ | $1/4$ |
| $3$ | $1/8$ | $1/32$ | $1/8$ |

第二层每节点接收一个父节点；第三层每节点汇合两个父区域中对应节点的发送。所有节点均激活，终端有正强度输出，同时总强度逐层减小。基础连接的展开侧在相等评分、相同节点上限、$\gamma=1$ 时，有 $\mu_{\ell+1}=(|\mathcal D_\ell|/n)\mu_\ell$。传播到输出的正性与单位强度保障因而各有条件。

保持图、单位入口、增益及相等评分，改用固定总强度 Attention。uniform 与 mu 在各区域内均分权重，得到：

| 层 | 每节点接收强度 $r_v^{\mathrm{in}}$、写入权重 $w_v$ 及 $\mu_v$ | 每节点发送强度 $c_v$ | 每区域总发送强度 |
|---|---|---|---|
| $1$ | $1$ | $1/4$ | $1$ |
| $2$ | $1/4$ | $1/4$ | $1$ |
| $3$ | $1/2$ | $1/4$ | $1$ |

此时每个区域的发送总强度均为 $1$，各节点的写入权重仍取实际接收强度。区域总量分配在此例各区域也发送总量 $1$。相同算例中，$k_j=1$ 的约束 Shannon 具有同一前向；评分不等时，各函数分别按自己的定义分配。例如第二层 $M_j=1$，Shannon 的分配由约束固定，固定总强度 Attention 仍可响应评分变化。

## 3. KV 与循环记忆的组合

保留 §1.1 选定的 HB 拓扑与时间，以及 §2.1—2.2 的来源和边界。§2.3 的七层形状可令中间层 $4$ 使用 [delta](../local-semantics/weighted-message/recurrent-memory-learning-note.md)，以矩阵查询 $M^{\mathrm{state}}$ 形成描述，其余层仍用 KV；替换区域采用循环教材的状态空间、零初态、Upd、Mem、当前特征与 $G_v$，取 $d_k=d_m=64$，描述宽度统一为 $d_s=32$。各区域继续独立选择评分和发送函数。循环短期衰减按 $\lambda=\bar\lambda/D$ 换算，长期率为零，其余参数由组合给定。

候选传播和消息计数公式只依赖图与实际发送，§2.4 和第 5 节的相应结论继续成立。更换记忆可以改变评分、激活者和实际路径，计数按新运行确定。缓存长度只描述 KV 区域，循环区域保存固定大小状态。区域 query 只要求描述类型相容，不要求不同区域有相同状态空间。

按层调用各区域自己的精确状态与 Full 契约，得到同一正典记录和切面继续。数值性质应用共同架构 §6，两种记忆分别提供局部引理。

## 4. 分段继续与所用数学性质

固定总强度 Attention 使用固定正温度，普通版和接收加权版均可持续用于训练、推理。它与其他已定义选择共用本节的精确分段继续和联合求值。

给定位置区间 $[p,q)$ 的左切面 $Q_{Dp}$ 及完整端口输入，可以逐层求值。先取得该层所有区域的完整驱动纤维，再按区域调用所选模块的 BatchRegionState 和逐节点 BatchFull。KV 使用其教材 §6 的前缀与读取构造，循环使用其教材 §4 的仿射复合，由此确定下一层所需的消息。同层区域之间没有消息依赖，层内多个区域可独立求值。稀疏边只改变需要汇集的父节点集合。

在 $Dq$ 处没有跨界消息，继续保留节点状态、单点历史和原始位置。切在位置内部时还须保留 $W_b$。Read 的内容检索和 Full 均只读取各自快照及原始时间，整段、连续多 chunk 与逐位置求值满足同一精确记录契约。查询、缓存与消息的工作量由第 5 节计量。

固定 $\mathcal H_\ell,\mathcal D_\ell$、区域、时间和局部配置后，数值性质应用[共同架构 §6](../local-semantics/weighted-message/architecture-learning-note.md#6-数值性质的组合)。KV 与循环模块分别验证状态条件；正温度输入连续性和单位输入的软硬极限分别使用各自的发送函数及评分条件。该组合定理直接覆盖本实例的稀疏邻域。

若全部区域采用 quad 或固定 $\alpha>1$ 的 ent，且对应硬运行满足评分条件，则共同架构的正温度推论给出：在固定参数、输入和有限时间范围内，充分小正温度使完整记录及切面继续状态精确等于硬运行。所需温度界按该次硬运行确定。

硬选择每个区域每位置激活 $1$ 至 $k_j$ 个候选，激活者随输入和历史改变。既有空间边可在其他位置继续使用。连接较丰富的 HB 和较稀疏的 HB 各自在自己的固定图上使用同一结论。永久删边改变空间图；在同一图上，局部选择决定各次实际使用的边。

## 5. 候选传播与全图成本

记 $\mathcal C_\ell(t),\mathcal A_\ell(t)$ 为位置 $t$ 在第 $\ell$ 层全部区域的候选、激活集合，$I_\ell(t)$ 为该层存在外部注入的节点集合，$N^+(v)$ 为出邻域。本文 $I_1(t)$ 为第一层全体节点，其余为空。各选择函数都按正发送强度广播，消息的存在与激活对应，因此

$$
\begin{aligned}
\mathcal C_{\ell+1}(t)
 &= I_{\ell+1}(t)\cup
    \bigcup_{v\in\mathcal A_\ell(t)}N^+(v),\\
|\mathcal C_{\ell+1}(t)|
 &\le |I_{\ell+1}(t)|+\Delta_\ell|\mathcal A_\ell(t)|,\\
\#\mathrm{message}_{\ell\to\ell+1}(t)
 &=\sum_{v\in\mathcal A_\ell(t)}|N^+(v)|,
\end{aligned}
\tag{4}
$$

其中 $\Delta_\ell$ 为该层最大出度。显式保留零 Full 及零广播会产生额外候选。满足[共同架构命题 1](../local-semantics/weighted-message/architecture-learning-note.md#62-零消息与正温度输入)的组合保持消息投影、有效状态和 ReadOut，候选与消息计数须按实际计算规则重算。

含固定总强度 uniform Attention 的混合组合须保留消息存在掩码：缺席槽只作张量填充，不产生真实候选。把缺席改为存在的零强度消息，可能改变下游份额与前向结果；各发送函数的适用范围见[性质对照](../local-semantics/weighted-message/architecture-learning-note.md#64-发送规则的性质对照)。

硬运行另有

$$
|\mathcal B_\ell|\le|\mathcal A_\ell(t)|\le
 \sum_{\omega\in\mathcal B_\ell}k_{(\ell,\omega)},
\qquad
|J|\le\#\mathrm{Full}(t)\le\sum_{j\in J}k_j.
\tag{5}
$$

在 §2.3 的形状中，每位置 Full 数在 $22$ 至 $44$ 之间。第一层全体 $64$ 个节点准备，其中一至两个激活；第二层的两个区域都会到达，总候选至多为 $2\times4=8$。后续各区的节点覆盖由实际选择及邻域重叠决定，所有区域始终有非空候选。

同一形状若全部区域采用固定总强度 Attention、直接 Attention、区域总量分配、按比例分配、bern 或 ent 的 $\alpha=1$，正温度下每位置为 $1408$ 个候选、$1408$ 次 Full、$3584$ 条内部消息。发送强度即使很小，这些工作仍然存在；各节点的写入权重可小于 $1$。混合选择时按式 (4) 逐层计数，不能直接套用全稠密或硬运行数字。

更一般地，若下一层有 $1000$ 个节点、当前有 $10$ 个激活者且没有其他注入，全连接会使下一层 $1000$ 个节点全部准备；出度至多 $4$ 时，候选至多为 $40$。减少一次上游发送可能同时省去下游的聚合、记忆投影与写入、Read、选择、Full 和进一步发送。

在其他发送者保持不变的条件下，撤去 $v$ 的发送会直接移除的候选恰为

$$
N^+(v)\setminus\left(
 I_{\ell+1}(t)\cup
 \bigcup_{u\in\mathcal A_\ell(t)\setminus\{v\}}N^+(u)
\right).
\tag{6}
$$

因此父邻域重叠和其他注入会削弱这项节约。式 (6) 是保持其他发送者不变的覆盖比较；实际选择须保留本区域的至少一个激活者，撤去唯一激活者时必须另选节点，其邻域也须计入。后续内容、评分和选择也可能改变，整图总工作量不能由单个发送强度的变化直接判定为单调下降。

当前已收到消息的节点，即使未激活，仍完成本次准备并保留写入。Read、选择与下游工作按共同架构附录 S.2 分类，具体状态和算术成本由所选记忆模块确定。

本实例的训练对照见 [可选研究问题与对照](../memos/training/weighted-message-research-questions.md)，图、局部函数与继续记录的程序对应见 [实现核对](../reference/weighted-message-implementation-checks.md)。

## 附录 S：配置对应

第 2 节采用 memory_family=kv、read_mode=+、local_score=cat、send_gain=fixed、selection_mode=constrained、regularizer=quad。第 2.3 节按层给出 memory_read=sum／qry 和 region_score=ind／att；query_weight 未另声明时取 mu。第 3 节中间层改为 memory_family=delta、memory_read=state。

固定尺度的稠密区域 Attention 使用 region_score=att、alpha_loc=0、alpha_sel=1 及固定正 allocation_temperature。发送可取 unit_attention、direct_attention、pooled_attention 或约束 Shannon；它们在弱接收处按第 2.5 节产生不同结果。unit_attention 的 allocation_base 为 uniform／mu，direct_attention 为 mu／received，pooled_attention 固定 mu。其余取值和参数生效范围统一见[区域分配附录 S.1](../local-semantics/weighted-message/region-allocation-learning-note.md#s1-配置名称)。
