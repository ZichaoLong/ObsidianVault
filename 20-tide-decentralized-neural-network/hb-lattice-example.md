---
type: mathematical-architecture-example
status: active
cssclasses:
  - textbook-math
tags:
  - tide
  - mathematics
  - semantic-anchor
  - architecture
  - weighted-kv
  - hb-lattice
---

# HB-Lattice 构造与组合实例

本文定义一个分层的 HB-Lattice：区域递归展开，到中间层达到最大数量，再逐层收拢；相邻层节点按固定邻域连接。每层可以有多个选择区域，各自根据当前候选与私有记忆作选择。空间图在一次运行中固定，实际计算路径随输入、历史和门控变化。

第 1 节独立给出拓扑与时间，第 2 节给出采用 [[weighted-kv-sparse-activation-example|带权 KV]] 的完整组合，第 3--4 节说明继续求值、候选传播及工作量。读者可先掌握 [[settlegraph-learning-note|SettleGraph]]。[[weighted-kv-layered-example|全连接分层实例]] 提供相同局部函数下的比较基线。

## 1. 拓扑、区域与时间

### 1.1 递归展开与收拢

取整数分支数 $b\ge2$、展开深度 $h\ge1$、区域宽度 $n\ge1$，令总层数 $L=2h+1$。记 $\mathbb Z_n=\{0,\ldots,n-1\}$，节点内部的横向坐标按模 $n$ 相加。第 $\ell$ 层的区域地址为长度 $q_\ell$ 的字：

$$
q_\ell=h-|\ell-(h+1)|,\qquad
\mathcal B_\ell=\{0,\ldots,b-1\}^{q_\ell},
\qquad 1\le\ell\le L.
\tag{1}
$$

长度零只有空字 $\varnothing$。区域与节点定义为

$$
\begin{aligned}
J&=\{(\ell,\omega):1\le\ell\le L,\ \omega\in\mathcal B_\ell\},\\
V&=\{v_{\ell,\omega,s}:1\le\ell\le L,\ \omega\in\mathcal B_\ell,\ s\in\mathbb Z_n\},\\
\rho(v_{\ell,\omega,s})&=(\ell,\omega),\qquad
\mathcal R_{(\ell,\omega)}=\{v_{\ell,\omega,s}:s\in\mathbb Z_n\}.
\end{aligned}
\tag{2}
$$

各区域互不相交。区域秩取其层号，故 $r_{v_{\ell,\omega,s}}=\ell$。同层不同区域具有相同秩；所有消息边都严格增加秩。节点全序取 $(\ell,\omega,s)$ 的字典序，用于选择平票。

### 1.2 相邻层邻域

对每个 $1\le\ell<L$，固定非空横向偏移集 $\mathcal D_\ell\subseteq\mathbb Z_n$，要求 $0\in\mathcal D_\ell$。先定义递归区域连接关系

$$
\mathcal H_\ell^0=
\begin{cases}
\{(\omega,\omega a):\omega\in\mathcal B_\ell,\ 0\le a<b\},&\ell\le h,\\
\{(\omega a,\omega):\omega\in\mathcal B_{\ell+1},\ 0\le a<b\},&\ell>h.
\end{cases}
\tag{3}
$$

取一个已声明的固定关系
$\mathcal H_\ell^0\subseteq\mathcal H_\ell\subseteq\mathcal B_\ell\times\mathcal B_{\ell+1}$。
基础形状取 $\mathcal H_\ell=\mathcal H_\ell^0$；增加区域连接或横向偏移可以得到连接更丰富的形状。

对每个 $(\omega,\omega')\in\mathcal H_\ell$、$s\in\mathbb Z_n$、$a\in\mathcal D_\ell$，放置一条有独立身份的边

$$
e_{\ell,\omega,\omega',s,a}:
 v_{\ell,\omega,s}\longrightarrow
 v_{\ell+1,\omega',s+a\bmod n},\qquad
\delta(e_{\ell,\omega,\omega',s,a})=1.
\tag{4}
$$

这些是全部消息边，层内没有消息边。偏移按集合给出，同一对端点不会因重复偏移产生重边。对基础形状的第 $\ell\to\ell+1$ 层连接，展开侧源节点出度为 $b|\mathcal D_\ell|$、目标节点入度为 $|\mathcal D_\ell|$；收拢侧分别为 $|\mathcal D_\ell|$、$b|\mathcal D_\ell|$。横向零偏移和递归关系使每个节点都位于某条入口到终端的路径上。

$|\mathcal D_\ell|\ll n$ 给出局部邻域。增大偏移集改变空间上允许的连接；在固定形状上改变局部门控则改变本次实际发送。取全部区域对和全部偏移可得到相邻层全连接，同时保留多区域选择。

### 1.3 端口、日程与位置

第一层与最后一层均只有一个区域。取 $\mathsf I=\{i_s:s\in\mathbb Z_n\}$、$\mathsf O=\{o_s:s\in\mathbb Z_n\}$，端口归属为

$$
\gamma(i_s)=v_{1,\varnothing,s},\qquad
\varepsilon(o_s)=v_{L,\varnothing,s}.
$$

固定输入长度 $N\ge1$。对位置 $t\in\{0,\ldots,N-1\}$，令 $D=L+2$，

$$
\theta_{v_{\ell,\omega,s},t}=Dt+\ell,\qquad
\iota_{i_s}(t)=Dt+1,
\qquad \operatorname{Pos}_{v_{\ell,\omega,s}}(\theta)=\frac{\theta-\ell}{D}.
\tag{5}
$$

各边时延等于端点秩差，端口日程对齐，满足 SettleGraph 的单次结算条件。消息汇合仍属于同一输入位置，每节点每位置至多处理一次；处理时的位置坐标恰为 $t$。同层多个区域各自结算。

为每区域 $j$ 声明 $H_j\in\mathbb N_{\ge1}\cup\{\infty\}$，取 $T_v=DH_j$；短期摘要率取 $\beta_{v,\mathrm{short}}=\bar\beta_{j,\mathrm{short}}/D$，其中 $\bar\beta_{j,\mathrm{short}}>0$，长期率为零。窗口覆盖最近 $H_j$ 个输入位置或全部接收历史。Read 与 Full 的旋转维数及频率分别声明，均使用式 (5) 的位置坐标。

## 2. 局部函数与边界绑定

本节固定一份 KV 组合，函数分别沿用[共同架构](local-architecture-learning-note.md)、[区域分配](region-allocation-learning-note.md)与 [KV 模块](weighted-kv-sparse-activation-example.md)。拓扑和时间始终由第 1 节给定。

### 2.1 基线与来源

全图共享载荷宽度 $d$，取 $P=X_v=\mathbb R^{1+d}$、区域共享 Agg、KV 空缓存初态、$\tau_j=+$、$\kappa_j=1$、默认 Next 和单点区域历史。Full 采用 KV 内容函数与共同广播，向全部出边和输出端口复制本次载荷。

各区域取拼接局部评分、固定增益和约束二次分配，声明 $1\le k_j\le n$、阈值、正温度及 $K_j=n$。记忆描述、区域评分和位置可按 §2.3 分区绑定；其余宽度、矩阵、偏置与残差尺度按各模块定义给出有限值。区域 Attention 只汇集本区域同一逻辑时间的完整候选，消息仍沿式 (4) 传播。

替换发送函数时，沿用区域分配教材的完整定义及容量对应；替换记忆时按共同架构 §5 检查描述和参数形状。配置对应见附录 S。

输入来源类别为 $\mathrm{in}$。对每条边 $e:v\to v'$，令

$$
\operatorname{SrcClass}_{v'}(\mathrm{msg},e)=v,
\qquad
\operatorname{SrcClass}_{v_{1,\varnothing,s}}(\mathrm{ext},i_s)=\mathrm{in}.
\tag{6}
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
\tag{7}
$$

其中 ReadOut 为局部架构教材的 ReadOut，$W_{\mathrm{out}}\in\mathbb R^{d\times d}$、$\alpha_{\mathrm{out}}\ge0$。在 $Dt+L+1$ 比较已经确定的输出槽。通用 ReadOut 对全部终端缺席取零；本实例每位置均有正强度终端输出，见 §2.4，内容相消仍可使 $O_t=0$。读出发生在图外。独立语言模型可用 token 嵌入作为 $h_t$，以 $y_t$ 接任务读出。

### 2.3 一个可直接配置的形状

取 $b=2,h=3,n=64$，各层区域数依次为

$$
1,2,4,8,4,2,1.
$$

共有 $22$ 个区域、$1408$ 个节点。取 $\mathcal H_\ell=\mathcal H_\ell^0$，偏移集统一为 $\{0,1\}$，共有 $3584$ 条边；展开侧最大出度为 $4$，收拢侧为 $2$。偏移集改为 $\{0,1,2,3\}$ 时边数为 $7168$，提供一个连接更丰富的比较形状。

一组配置形状可取 $d=512,H_{\mathrm{att}}=8,d_h=64,p_a=d_s=d_r=d_{\mathrm{sel}}=r_a=32,d_f=2048$，各区域 $k_j=2$，Agg 取区域共享，局部评分、增益和预算正则取 cat、fixed、quad。记忆与区域评分按下表选择：

| 层 | 记忆与评分 | $H_j$ | Full 旋转 | Read 旋转 |
|---|---|---|---|---|
| $1,2,3$ | $\mathrm{qry},\mathrm{att}$ | $512$ | 每头完整 $64$ 维 | $d_s=32$ 维全部旋转 |
| $4$ | $\mathrm{sum},\mathrm{ind}$ | $\infty$ | NoPE | 时间摘要无需检索旋转 |
| $5,6,7$ | $\mathrm{sum},\mathrm{att}$ | $512$ | 每头部分 $32$ 维 | 时间摘要无需检索旋转 |

对所有旋转族取基数 $10^4$、频率 $(10^4)^{-2(a-1)/d^{\mathrm{rot}}}$，其中 $1\le a\le d^{\mathrm{rot}}/2$；Full 的距离偏置取零。其余标量和矩阵由配置给出。这个形状在展开侧采用内容检索与区域匹配，中间层保留全历史，收拢侧采用摘要与区域匹配；也可逐区域代入已定义的其他组合。

### 2.4 区域到达与节点稀疏

式 (4) 使源区域的每个节点都连向每个相连目标区域，且 $\mathcal D_\ell$ 非空。因此一个区域只要有正强度发送，每个相连目标区域就都有有效候选。第一层收到单位输入，非空选择沿递归区域连接传播，故每个输入位置的所有区域均有节点接收并激活，终端输出存在。

若全图各区域均采用区域分配教材的约束分配，还满足每区发送强度之和至少为 $1$。第一层有 $M_j=n$；若某父区域发送强度之和至少为 $1$，相连目标区域所有节点的接收强度之和至少为 $1$，并有

$$
M_j=\sum_{v\in\mathcal R_j}\min(1,\gamma_v r_v)
\ge\min\left(1,\sum_{v\in\mathcal R_j}r_v\right)=1,
$$

其中未接收节点按 $r_v=0$ 计。总和下限于是为 $1$，逐层归纳成立。全图各区域均用硬选择时，从单位输入出发，每条实际消息强度均为 $1$，每区非空选择同样保证发送强度之和至少为 $1$。采用固定总强度 Attention 的区域，只要有正接收候选便发送总强度 $1$；直接 Attention 及混合选择继续保证每区有正发送，其总强度按各自公式确定。

区域内的候选可只占一小部分，具体节点随上游选择与邻域变化；正温度运行中各节点的接收强度和写入权重可小于 $1$，缓存长度也可不同。全图采用约束软选择时，单节点弱接收与区域 $M_j\ge1$ 可以同时成立，区域内可调整的分配范围由区域分配教材 §2.1 与 §4.1 判断。每个区域至少保留一个激活节点，是本拓扑的 Full 成本下限。

若全部区域在正温度使用固定总强度 Attention、直接 Attention、pooled、dense、bern 或 ent 的 $\alpha=1$，第一层全部节点都发送，零偏移边让下一层全部节点都有正接收，归纳得到全图所有节点均激活；消息仍只沿既定 HB 边传播。quad 与 ent 的 $\alpha>1$ 可以在正温度通过精确零减少这里的激活数量。各选择函数的写入仍按实际 $w(r)$；发送强度另由所选函数决定。

<a id="25-直接-attention-的强度传播"></a>

### 2.5 稠密发送的强度传播

直接 Attention 的总发送强度是各候选上限的加权平均。取 $b=2,h=1,n=4$、$\mathcal H_\ell=\mathcal H_\ell^0$、$\mathcal D_\ell=\{0\}$，各层区域数为 $1,2,1$。全图采用直接 Attention、固定增益 $\gamma=1$，令每区域各候选评分相等。单位入口给出：

| 层 | 每节点接收强度及上限 $r_v=\mu_v$ | 每节点发送强度 $c_v$ | 每区域总发送强度 |
|---|---|---|---|
| $1$ | $1$ | $1/4$ | $1$ |
| $2$ | $1/4$ | $1/16$ | $1/4$ |
| $3$ | $1/8$ | $1/32$ | $1/8$ |

第二层每节点接收一个父节点；第三层每节点汇合两个父区域中对应节点的发送。所有节点均激活，终端有正强度输出，同时总强度逐层减小。基础连接的展开侧在相等评分、相同节点上限、$\gamma=1$ 时，有 $\mu_{\ell+1}=(|\mathcal D_\ell|/n)\mu_\ell$。传播到输出的正性与单位强度保障因而各有条件。

保持图、单位入口、增益及相等评分，改用固定总强度 Attention。uniform 与 mu 在各区域内均分权重，得到：

| 层 | 每节点接收强度 $r_v$、写入权重 $w_v$ 及 $\mu_v$ | 每节点发送强度 $c_v$ | 每区域总发送强度 |
|---|---|---|---|
| $1$ | $1$ | $1/4$ | $1$ |
| $2$ | $1/4$ | $1/4$ | $1$ |
| $3$ | $1/2$ | $1/4$ | $1$ |

此时每个区域的发送总强度均为 $1$，各节点的写入权重仍取实际接收强度。pooled 在此例各区域也发送总量 $1$。相同算例中，$k_j=1$ 的约束 Shannon 具有同一前向；评分不等时，两类函数分别按自己的约束分配。例如第二层 $M_j=1$，Shannon 的分配由约束固定，固定总强度 Attention 仍可响应评分变化。

<a id="3-固定图上的退火与分段继续"></a>

## 3. 分段继续与所用数学性质

固定总强度 Attention 使用固定正温度，普通版和接收加权版均可持续用于训练、推理。它与其他已定义选择共用本节的精确分段继续和联合求值。

给定位置区间 $[p,q)$ 的左切面 $Q_{Dp}$ 及完整端口输入，可以逐层求值。先取得该层所有区域的完整驱动纤维，再分别调用 KV 教材 §6 的 BatchRegionState 和逐节点 BatchFull；下一层所需消息由此确定。同层区域之间没有消息依赖，层内多个区域可独立求值。稀疏边只改变需要汇集的父节点集合。

在 $Dq$ 处没有跨界消息，继续保留节点状态、单点历史和原始位置。切在位置内部时还须保留 $W_b$。Read 的内容检索和 Full 均只读取各自快照及原始时间，整段、连续多 chunk 与逐位置求值满足同一精确记录契约。查询、缓存与消息的工作量由第 4 节计量。

固定 $\mathcal H_\ell,\mathcal D_\ell$、区域、时间和局部配置后，数值性质应用[共同架构 §6](local-architecture-learning-note.md#6-数值性质的组合)。KV 验证状态条件；正温度输入连续性和单位输入的软硬极限分别使用各自的发送函数及评分条件。该组合定理直接覆盖本实例的稀疏邻域。

硬选择每个区域每位置激活 $1$ 至 $k_j$ 个候选，激活者随输入和历史改变。既有空间边可在其他位置继续使用。连接较丰富的 HB 和较稀疏的 HB 各自在自己的固定图上使用同一结论。永久删边改变空间图；在同一图上，局部选择决定各次实际使用的边。

## 4. 候选传播与全图成本

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
\tag{8}
$$

其中 $\Delta_\ell$ 为该层最大出度。显式保留零 Full 及零广播会产生额外候选。满足[共同架构命题 1](local-architecture-learning-note.md#62-零消息与正温度输入)的组合保持消息投影、有效状态和 ReadOut，候选与消息计数须按实际计算规则重算。

含固定总强度 uniform Attention 的混合组合须保留消息存在掩码：缺席槽只作张量填充，不产生真实候选。把缺席改为存在的零强度消息，可能改变下游份额与前向结果；各发送函数的适用范围见[性质对照](local-architecture-learning-note.md#64-发送规则的性质对照)。

硬运行另有

$$
|\mathcal B_\ell|\le|\mathcal A_\ell(t)|\le
 \sum_{\omega\in\mathcal B_\ell}k_{(\ell,\omega)},
\qquad
|J|\le\#\mathrm{Full}(t)\le\sum_{j\in J}k_j.
\tag{9}
$$

在 §2.3 的形状中，每位置 Full 数在 $22$ 至 $44$ 之间。第一层全体 $64$ 个节点准备，其中一至两个激活；第二层的两个区域都会到达，总候选至多为 $2\times4=8$。后续各区的节点覆盖由实际选择及邻域重叠决定，所有区域始终有非空候选。

同一形状若全部区域采用固定总强度 Attention、直接 Attention、pooled、dense、bern 或 ent 的 $\alpha=1$，正温度下每位置为 $1408$ 个候选、$1408$ 次 Full、$3584$ 条内部消息。发送强度即使很小，这些工作仍然存在；各节点的写入权重可小于 $1$。混合选择时按式 (8) 逐层计数，不能直接套用全稠密或硬运行数字。

更一般地，若下一层有 $1000$ 个节点、当前有 $10$ 个激活者且没有其他注入，全连接会使下一层 $1000$ 个节点全部准备；出度至多 $4$ 时，候选至多为 $40$。减少一次上游发送可能同时省去下游的聚合、KV 投影、写入、Read、选择、Full 和进一步发送。

在其他发送者保持不变的条件下，撤去 $v$ 的发送会直接移除的候选恰为

$$
N^+(v)\setminus\left(
 I_{\ell+1}(t)\cup
 \bigcup_{u\in\mathcal A_\ell(t)\setminus\{v\}}N^+(u)
\right).
\tag{10}
$$

因此父邻域重叠和其他注入会削弱这项节约。式 (10) 是保持其他发送者不变的覆盖比较；实际选择须保留本区域的至少一个激活者，撤去唯一激活者时必须另选节点，其邻域也须计入。后续内容、评分和选择也可能改变，整图总工作量不能由单个发送强度的变化直接判定为单调下降。

当前已收到消息的节点，即使未激活，仍完成本次准备并保留写入。Read、选择与下游工作共同进入局部架构教材附录 S.2 与 KV 教材附录 S 的代价和式。

本实例的训练对照见 [可选研究问题与对照](memos/learning-systems/local-architecture-research-questions.md)，图、局部函数与继续记录的程序对应见 [实现核对](local-architecture-implementation-checks.md)。

## 5. 按区域组合不同记忆

保留第 1 节的 HB 拓扑与时间，以及 §2.1—2.2 的来源和边界。§2.3 的七层形状可令中间层 $4$ 使用 [delta](recurrent-memory-learning-note.md)、memory_read=state，其余层仍用 KV；循环矩阵宽度可取 $d_k=d_m=64$，描述宽度统一为 $d_s=32$。各区域继续独立选择评分和发送函数。循环短期衰减按 $\lambda=\bar\lambda/D$ 换算，长期率为零，其余参数由组合给定。

各次候选传播和消息计数只依赖图与发送，§2.4 和第 4 节的相应结论继续成立。缓存长度只描述 KV 区域，循环区域保存固定大小状态。区域 query 只要求描述类型相容，不要求不同区域有相同状态空间。

按层调用各区域自己的精确状态与 Full 契约，得到同一正典记录和切面继续。数值性质应用共同架构 §6，两种记忆分别提供局部引理。

## 附录 S：配置对应

第 2 节采用 memory_family=kv、read_mode=+、local_score=cat、send_gain=fixed、selection_mode=soft、budget_family=quad。第 2.3 节按层给出 memory_read=sum／qry 和 region_score=ind／att；query_weight 未另声明时取 mu。第 5 节中间层改为 memory_family=delta、memory_read=state。

固定尺度的稠密区域 Attention 使用 region_score=att、alpha_loc=0、alpha_sel=1 及固定正 tau_soft。发送可取 attention、direct、pooled 或约束 Shannon；它们在弱接收处按第 2.5 节产生不同结果。attention 的 allocation_base 为 uniform／mu，direct 为 mu／received，pooled 固定 mu。其余取值和参数生效范围统一见[区域分配附录 S.1](region-allocation-learning-note.md#s1-配置名称)。
